#!/usr/bin/env python3
"""Evidence ledger for incident investigations. Standard library only.

Run with `python3 -I`. Every evidence item gets a stable ID (E-01, E-02, ...),
a JSON record in <work>/queries/, a row in <work>/query-log.tsv and a line in
<work>/SHA256SUMS. Records are never overwritten: a re-run gets a new ID.

Subcommands (all take --work DIR, default $INCIDENT_WORK or ./incident-work):

  init                          create the working directory (mode 700), ledger files and .gitignore
  next                          print the next free evidence ID
  run   --source S [--range R] -- CMD...      run a read-only command, record stdout/stderr/exit code
  nrql  [--range R] NRQL        New Relic NerdGraph (env NR_ACCOUNT_ID, NEW_RELIC_API_KEY)
  athena [--range R] SQL        AWS Athena, SELECT/WITH only (env ATHENA_PROFILE, ATHENA_WORKGROUP, ATHENA_DATABASE, AWS_REGION)
  note  --source S [--range R] (--file F | --text T)   evidence read through a tool with no CLI (Slack, PostHog, Jira, a console)
  import --source S PATH        copy an exported file into the ledger unchanged and hash it
  derived --from E-xx[,E-yy] -- CMD...        local analysis over earlier evidence
  register PATH...              record an original source file (path, size, mtime, SHA-256) in sources.tsv without copying it
  verify [--incident INCIDENT.md]            check hashes, IDs, timestamps, ordering and citations
  seal   [--incident INCIDENT.md]            dated checkpoint manifest over the ledger, answers, bin/ and INCIDENT.md

Common options: --id E-nn (explicit ID, refused if it exists), --sensitive (record contains
card data, tokens, or personal data beyond account identifiers), --supersedes E-xx,
--note TEXT (one line of context, e.g. why the query was run), --show N (rows to print).
"""

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

LOG_COLUMNS = ["id", "run_at", "source", "range", "status", "rows", "truncated", "sha256", "file", "query"]
ID_RE = re.compile(r"^E-\d{2,}(\.\d+)?$")


# --------------------------------------------------------------------------- helpers

def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def die(msg, code=2):
    print(f"evidence: {msg}", file=sys.stderr)
    sys.exit(code)


class Ledger:
    def __init__(self, work):
        self.work = os.path.abspath(work)
        self.queries = os.path.join(self.work, "queries")
        self.log = os.path.join(self.work, "query-log.tsv")
        self.sums = os.path.join(self.work, "SHA256SUMS")
        self.sources = os.path.join(self.work, "sources.tsv")

    def init(self):
        os.umask(0o077)
        os.makedirs(self.queries, mode=0o700, exist_ok=True)
        for sub in ("answers", "bin"):
            os.makedirs(os.path.join(self.work, sub), mode=0o700, exist_ok=True)
            os.chmod(os.path.join(self.work, sub), 0o700)
        os.chmod(self.work, 0o700)
        os.chmod(self.queries, 0o700)
        # keep a copy of this runner with the evidence it produced
        me = os.path.abspath(__file__)
        dest = os.path.join(self.work, "bin", "evidence.py")
        if not os.path.exists(dest) and os.path.isfile(me):
            shutil.copyfile(me, dest)
            os.chmod(dest, 0o700)
        if not os.path.exists(self.log):
            with open(self.log, "w") as f:
                f.write("\t".join(LOG_COLUMNS) + "\n")
        for p in (self.sums,):
            if not os.path.exists(p):
                open(p, "a").close()
        if not os.path.exists(self.sources):
            with open(self.sources, "w") as f:
                f.write("id\tregistered_at\tpath\tsize\tmtime_utc\tsha256\tnote\n")
        gi = os.path.join(self.work, ".gitignore")
        if not os.path.exists(gi):
            with open(gi, "w") as f:
                f.write("*\n")
        for p in (self.log, self.sums, self.sources, gi):
            os.chmod(p, 0o600)

    def require(self):
        if not os.path.isdir(self.queries) or not os.path.exists(self.log):
            die(f"{self.work} is not initialised; run: evidence.py init --work {self.work}")
        os.umask(0o077)

    def rows(self):
        out = []
        if not os.path.exists(self.log):
            return out
        with open(self.log, newline="") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("id\t"):
                    continue
                parts = line.split("\t")
                if len(parts) >= len(LOG_COLUMNS):
                    out.append(dict(zip(LOG_COLUMNS, parts[: len(LOG_COLUMNS)])))
                else:
                    # legacy 4-column layout: id, run_at, sha256, query
                    out.append({"id": parts[0], "run_at": parts[1] if len(parts) > 1 else "",
                                "source": "", "range": "", "status": "", "rows": "", "truncated": "",
                                "sha256": parts[2] if len(parts) > 2 else "", "file": f"queries/{parts[0]}.json",
                                "query": parts[3] if len(parts) > 3 else "", "_legacy": True})
        return out

    def ids(self):
        return [r["id"] for r in self.rows()]

    def next_id(self):
        n = 0
        for i in self.ids():
            m = re.match(r"^E-(\d+)", i)
            if m:
                n = max(n, int(m.group(1)))
        return f"E-{n + 1:02d}"

    def claim(self, explicit):
        eid = explicit or self.next_id()
        if not ID_RE.match(eid):
            die(f"bad id {eid!r}; use E-nn or E-nn.m")
        if eid in self.ids() or any(fn.startswith(eid + ".") for fn in os.listdir(self.queries)):
            die(f"{eid} already exists; evidence is never overwritten. Use the next id ({self.next_id()}) and --supersedes {eid}")
        return eid

    def write(self, eid, doc, ext="json", raw_bytes=None):
        fn = f"{eid}.{ext}"
        path = os.path.join(self.queries, fn)
        if os.path.exists(path):
            die(f"{path} exists; refusing to overwrite")
        if raw_bytes is None:
            with open(path, "x") as f:
                json.dump(doc, f, indent=1, default=str)
                f.write("\n")
        else:
            with open(path, "xb") as f:
                f.write(raw_bytes)
        os.chmod(path, 0o600)
        digest = sha256_file(path)
        with open(self.sums, "a") as f:
            f.write(f"{digest}  queries/{fn}\n")
        row = {
            "id": eid,
            "run_at": doc.get("run_at", ""),
            "source": doc.get("source", ""),
            "range": doc.get("range", "") or "",
            "status": doc.get("status", ""),
            "rows": "" if doc.get("row_count") is None else str(doc["row_count"]),
            "truncated": "" if doc.get("truncated") is None else ("yes" if doc["truncated"] else "no"),
            "sha256": digest,
            "file": f"queries/{fn}",
            "query": " ".join(str(doc.get("query", "")).split()),
        }
        with open(self.log, "a") as f:
            f.write("\t".join(row[c].replace("\t", " ") for c in LOG_COLUMNS) + "\n")
        return path, digest


def base_doc(args, eid, source, query, kind):
    return {
        "id": eid,
        "kind": kind,
        "source": source,
        "query": query,
        "range": getattr(args, "range", None),
        "run_at": now_utc(),
        "run_by": os.environ.get("INCIDENT_ANALYST") or getpass.getuser(),
        "host": socket.gethostname(),
        "sensitive": bool(getattr(args, "sensitive", False)),
        "supersedes": getattr(args, "supersedes", None),
        "note": getattr(args, "note", None),
    }


def parse_limit(query):
    m = re.search(r"\bLIMIT\s+(\d+)\b", query, re.IGNORECASE)
    return int(m.group(1)) if m else None


def fmt_epoch(v):
    if isinstance(v, (int, float)) and 1e12 < v < 1e13:
        return dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return v


def show_rows(rows, n):
    for r in (rows or [])[:n]:
        if isinstance(r, dict):
            print({k: fmt_epoch(v) for k, v in r.items()})
        else:
            print(r)
    if rows and len(rows) > n:
        print(f"... {len(rows) - n} more rows in the saved file")


def finish(ledger, eid, doc, args):
    path, digest = ledger.write(eid, doc)
    trunc = " TRUNCATED (result count equals the LIMIT; widen or paginate before treating as complete)" if doc.get("truncated") else ""
    print(f"{eid} status={doc.get('status')} rows={doc.get('row_count')} run_at={doc['run_at']} sha256={digest[:16]}... -> {os.path.relpath(path)}{trunc}")
    if doc.get("errors"):
        print("ERRORS:", json.dumps(doc["errors"], default=str)[:1000])


# --------------------------------------------------------------------------- subcommands

def cmd_init(args, ledger):
    ledger.init()
    print(f"initialised {ledger.work} (mode 700; files 600; .gitignore ignores everything; runner copied to bin/evidence.py; write draft answers to answers/Q-xx.md)")


def cmd_next(args, ledger):
    ledger.require()
    print(ledger.next_id())


def cmd_run(args, ledger):
    ledger.require()
    if not args.command:
        die("run needs a command after --")
    eid = ledger.claim(args.id)
    doc = base_doc(args, eid, args.source, " ".join(args.command), "command")
    doc["argv"] = args.command
    t0 = time.time()
    p = subprocess.run(args.command, capture_output=True, text=True, errors="replace")
    doc["duration_s"] = round(time.time() - t0, 2)
    doc["exit_code"] = p.returncode
    doc["stdout"] = p.stdout
    doc["stderr"] = p.stderr
    doc["status"] = "ok" if p.returncode == 0 else "error"
    lines = p.stdout.splitlines()
    doc["row_count"] = len(lines)
    doc["truncated"] = None
    finish(ledger, eid, doc, args)
    print("\n".join(lines[: args.show]))
    if p.stderr:
        print("stderr:", p.stderr[:2000], file=sys.stderr)


def cmd_nrql(args, ledger):
    ledger.require()
    acct = os.environ.get("NR_ACCOUNT_ID")
    key = os.environ.get("NEW_RELIC_API_KEY")
    if not acct or not key:
        die("set NR_ACCOUNT_ID and NEW_RELIC_API_KEY (read-only user key)")
    nrql = args.query
    if not re.match(r"^\s*(SELECT|SHOW|FROM|WITH)\b", nrql, re.IGNORECASE):
        die("read-only: NRQL must start with SELECT, SHOW, FROM or WITH")
    eid = ledger.claim(args.id)
    doc = base_doc(args, eid, f"newrelic account {acct}", nrql, "nrql")
    gql = {
        "query": "query($a:Int!,$q:Nrql!){actor{account(id:$a){nrql(query:$q,timeout:120){results metadata{timeWindow{begin end} messages}}}}}",
        "variables": {"a": int(acct), "q": nrql},
    }
    req = urllib.request.Request(
        os.environ.get("NR_GRAPHQL_ENDPOINT", "https://api.newrelic.com/graphql"),
        data=json.dumps(gql).encode(),
        headers={"Content-Type": "application/json", "API-Key": key},
    )
    doc["run_at"] = now_utc()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = json.load(r)
    except Exception as e:  # network or HTTP error: still record the attempt
        body = {"errors": [{"message": f"{type(e).__name__}: {e}"}]}
    node = (((body.get("data") or {}).get("actor") or {}).get("account") or {}).get("nrql") or {}
    results = node.get("results")
    meta = node.get("metadata") or {}
    tw = meta.get("timeWindow") or {}
    doc["errors"] = body.get("errors")
    doc["messages"] = meta.get("messages")
    if tw.get("begin") and tw.get("end"):
        doc["window_utc"] = {"begin": fmt_epoch(tw["begin"]), "end": fmt_epoch(tw["end"])}
        doc["range"] = doc["range"] or f"{doc['window_utc']['begin']} to {doc['window_utc']['end']}"
    doc["results"] = results
    doc["row_count"] = None if results is None else len(results)
    lim = parse_limit(nrql)
    doc["limit"] = lim
    doc["truncated"] = (results is not None and lim is not None and len(results) >= lim) or None
    doc["status"] = "error" if doc["errors"] or results is None else "ok"
    finish(ledger, eid, doc, args)
    if re.search(r"uniqueCount\s*\(", nrql, re.IGNORECASE):
        print("note: uniqueCount is approximate above ~1,000 distinct values; report it as 'about'")
    if re.search(r"\bTIMESERIES\b|\bFACET\b[^\n]*\b(day|week|month)\b", nrql, re.IGNORECASE) and "WITH TIMEZONE" not in nrql.upper():
        print("note: bucket labels follow the account timezone; add WITH TIMEZONE 'UTC' before reading dates off them")
    show_rows(results, args.show)


def cmd_athena(args, ledger):
    ledger.require()
    sql = args.query
    if not re.match(r"^\s*(SELECT|WITH|SHOW|DESCRIBE)\b", sql, re.IGNORECASE):
        die("read-only: SQL must start with SELECT, WITH, SHOW or DESCRIBE")
    profile = os.environ.get("ATHENA_PROFILE")
    wg = os.environ.get("ATHENA_WORKGROUP")
    db = os.environ.get("ATHENA_DATABASE")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if not (wg and db):
        die("set ATHENA_WORKGROUP and ATHENA_DATABASE (and ATHENA_PROFILE / AWS_REGION as needed)")
    base = ["aws", "athena", "--output", "json"]
    if profile:
        base += ["--profile", profile]
    if region:
        base += ["--region", region]

    def aws(*a):
        p = subprocess.run(base + list(a), capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(p.stderr.strip())
        return json.loads(p.stdout)

    eid = ledger.claim(args.id)
    doc = base_doc(args, eid, f"athena {db} (workgroup {wg}, profile {profile or 'default'})", sql, "athena")
    doc["run_at"] = now_utc()
    state, error, cols, rows, qid, scanned = "FAILED", None, [], [], None, None
    try:
        qid = aws("start-query-execution", "--work-group", wg, "--query-execution-context", f"Database={db}",
                  "--query-string", sql)["QueryExecutionId"]
        while True:
            ex = aws("get-query-execution", "--query-execution-id", qid)["QueryExecution"]
            state = ex["Status"]["State"]
            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                break
            time.sleep(2)
        error = ex["Status"].get("StateChangeReason")
        scanned = (ex.get("Statistics") or {}).get("DataScannedInBytes")
        if state == "SUCCEEDED":
            token, first = None, True
            while True:
                a = ["get-query-results", "--query-execution-id", qid, "--max-items", "1000"]
                if token:
                    a += ["--starting-token", token]
                page = aws(*a)
                rs = page["ResultSet"]
                if not cols:
                    cols = [c["Name"] for c in rs["ResultSetMetadata"]["ColumnInfo"]]
                data = rs["Rows"][1:] if first else rs["Rows"]
                first = False
                rows += [[d.get("VarCharValue") for d in r["Data"]] for r in data]
                token = page.get("NextToken")
                if not token:
                    break
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    doc.update({"query_execution_id": qid, "state": state, "errors": [error] if error else None,
                "bytes_scanned": scanned, "columns": cols, "rows": rows,
                "row_count": len(rows) if state == "SUCCEEDED" else None,
                "limit": parse_limit(sql)})
    doc["truncated"] = (doc["limit"] is not None and len(rows) >= doc["limit"]) or None
    doc["status"] = "ok" if state == "SUCCEEDED" else "error"
    finish(ledger, eid, doc, args)
    if cols:
        print("\t".join(cols))
    show_rows(["\t".join("" if c is None else c for c in r) for r in rows], args.show)


def cmd_note(args, ledger):
    """Evidence obtained through a tool with no CLI (an MCP tool, a web console, a screenshot)."""
    ledger.require()
    if not args.file and args.text is None:
        die("note needs --file PATH (the result text you saved) or --text")
    content = open(args.file, errors="replace").read() if args.file else args.text
    if not content.strip():
        die("refusing to record an empty note; paste the actual result")
    eid = ledger.claim(args.id)
    doc = base_doc(args, eid, args.source, args.query or "", "note")
    doc["content"] = content
    doc["content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
    doc["row_count"] = len(content.splitlines())
    doc["truncated"] = None
    doc["status"] = "ok"
    doc["tool_timezone"] = args.tool_timezone
    finish(ledger, eid, doc, args)


def cmd_import(args, ledger):
    ledger.require()
    src = args.path
    if not os.path.isfile(src):
        die(f"{src} is not a file")
    eid = ledger.claim(args.id)
    ext = os.path.splitext(src)[1].lstrip(".") or "bin"
    st = os.stat(src)
    with open(src, "rb") as f:
        raw = f.read()
    # the file itself is kept byte-for-byte; a .meta.json sidecar holds the record
    doc = base_doc(args, eid, args.source, f"import {os.path.abspath(src)}", "import")
    doc.update({"original_path": os.path.abspath(src), "original_size": st.st_size,
                "original_mtime_utc": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "ok", "row_count": None, "truncated": None})
    path, digest = ledger.write(eid, doc, ext=ext, raw_bytes=raw)
    doc.update({"stored_as": os.path.relpath(path, ledger.work), "sha256": digest})
    meta = os.path.join(ledger.queries, f"{eid}.meta.json")
    with open(meta, "x") as f:
        json.dump(doc, f, indent=1)
    os.chmod(meta, 0o600)
    with open(ledger.sums, "a") as f:
        f.write(f"{sha256_file(meta)}  queries/{eid}.meta.json\n")
    print(f"{eid} imported {src} ({st.st_size} bytes) sha256={digest} -> {os.path.relpath(path)}")


def cmd_derived(args, ledger):
    ledger.require()
    if not args.command:
        die("derived needs a command after --")
    inputs = [i.strip() for i in args.frm.split(",") if i.strip()]
    known = set(ledger.ids())
    missing = [i for i in inputs if i not in known]
    if missing:
        die(f"unknown input evidence ids: {missing}")
    eid = ledger.claim(args.id)
    doc = base_doc(args, eid, f"derived from {', '.join(inputs)}", " ".join(args.command), "derived")
    doc["inputs"] = inputs
    doc["argv"] = args.command
    p = subprocess.run(args.command, capture_output=True, text=True, errors="replace")
    doc.update({"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                "status": "ok" if p.returncode == 0 else "error",
                "row_count": len(p.stdout.splitlines()), "truncated": None})
    finish(ledger, eid, doc, args)
    print("\n".join(p.stdout.splitlines()[: args.show]))


def cmd_register(args, ledger):
    ledger.require()
    existing = sum(1 for _ in open(ledger.sources)) - 1
    for i, path in enumerate(args.paths, start=existing + 1):
        if not os.path.isfile(path):
            die(f"{path} is not a file")
        st = os.stat(path)
        digest = sha256_file(path)
        sid = f"S-{i:02d}"
        with open(ledger.sources, "a") as f:
            f.write("\t".join([sid, now_utc(), os.path.abspath(path), str(st.st_size),
                               dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                               digest, (args.note or "").replace("\t", " ")]) + "\n")
        print(f"{sid}\t{path}\t{st.st_size} bytes\tsha256={digest}")


def cmd_seal(args, ledger):
    """Write a dated checkpoint manifest covering the ledger files, answers, scripts and INCIDENT.md.

    SHA256SUMS covers only query results and is append-only, so the log itself and the context
    file are hashed here. Compare two seals to see what changed between sessions.
    """
    ledger.require()
    stamp = now_utc().replace(":", "").replace("-", "")
    out = os.path.join(ledger.work, f"SEAL-{stamp}.sha256")
    targets = [ledger.log, ledger.sums, ledger.sources]
    for sub in ("answers", "bin"):
        d = os.path.join(ledger.work, sub)
        if os.path.isdir(d):
            targets += [os.path.join(d, f) for f in sorted(os.listdir(d)) if not f.startswith(".")]
    inc = args.incident or os.path.join(os.path.dirname(ledger.work), "INCIDENT.md")
    if os.path.exists(inc):
        targets.append(inc)
    lines = []
    for t in targets:
        if os.path.isfile(t):
            rel = os.path.relpath(t, ledger.work)
            lines.append(f"{sha256_file(t)}  {rel}")
    with open(out, "x") as f:
        f.write(f"# sealed {now_utc()} by {os.environ.get('INCIDENT_ANALYST') or getpass.getuser()}@{socket.gethostname()}\n")
        f.write("\n".join(lines) + "\n")
    os.chmod(out, 0o600)
    print(f"sealed {len(lines)} files -> {os.path.relpath(out)}")


# --------------------------------------------------------------------------- verify

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CITE_RE = re.compile(r"\bE-(\d{2,})(?:\.(\d+))?(?:\s*[–-]\s*E-(\d{2,}))?")
SECRET_PATTERNS = [
    (re.compile(r"\b(?:Bearer|token|secret|password|api[_-]?key)\b[^\n|]{0,20}[A-Za-z0-9_\-]{32,}", re.IGNORECASE), "possible unredacted credential"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "possible full card number (13-19 digits)"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"), "possible JWT"),
]


def luhn_ok(digits):
    s, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return s % 10 == 0


def cmd_verify(args, ledger):
    problems, warnings = [], []
    rows = ledger.rows()
    ids = [r["id"] for r in rows]

    # 1. duplicate ids and id format
    seen = set()
    for i in ids:
        if i in seen:
            problems.append(f"duplicate evidence id in query-log: {i}")
        seen.add(i)
        if not ID_RE.match(i):
            problems.append(f"malformed evidence id: {i!r}")

    # 2. run_at format: full ISO 8601 UTC, no approximations
    for r in rows:
        if not ISO_RE.match(r["run_at"]):
            problems.append(f"{r['id']}: run_at {r['run_at']!r} is not an exact ISO 8601 UTC timestamp")

    # 3. hashes
    manifest = {}
    if os.path.exists(ledger.sums):
        for line in open(ledger.sums):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            h, _, p = line.partition("  ")
            p = p.strip()
            if p in manifest and manifest[p] != h:
                problems.append(f"SHA256SUMS lists {p} twice with different hashes")
            manifest[p] = h
    unprefixed = 0
    for p, h in list(manifest.items()):
        full = os.path.join(ledger.work, p)
        if not os.path.exists(full) and os.path.exists(os.path.join(ledger.queries, p)):
            unprefixed += 1
            full = os.path.join(ledger.queries, p)
            manifest[f"queries/{p}"] = h
        if not os.path.exists(full):
            problems.append(f"SHA256SUMS entry missing on disk: {p}")
        elif sha256_file(full) != h:
            problems.append(f"hash mismatch: {p}")
    if unprefixed:
        warnings.append(f"SHA256SUMS: {unprefixed} entries lack the queries/ prefix (shasum -c fails from incident-work/); regenerate with: (cd incident-work && shasum -a 256 queries/* > SHA256SUMS)")
    if os.path.isdir(ledger.queries):
        listed = {os.path.basename(p) for p in manifest}
        for fn in sorted(os.listdir(ledger.queries)):
            if fn.startswith("."):
                continue
            if fn not in listed:
                problems.append(f"queries/{fn} is not in SHA256SUMS")
            mode = os.stat(os.path.join(ledger.queries, fn)).st_mode & 0o777
            if mode & 0o077:
                warnings.append(f"queries/{fn} is mode {mode:o}; expected 600")
    for r in rows:
        if r["sha256"] and r["sha256"] != "-" and r["file"] and r["file"] not in manifest:
            warnings.append(f"{r['id']}: logged file {r['file']} has no SHA256SUMS entry")
        if r["sha256"] in ("", "-"):
            problems.append(f"{r['id']}: no hash recorded (result not exported). Save the result and record it with `note` or `import`.")

    # 4. the incident file
    inc = args.incident
    if not inc:
        cand = os.path.join(os.path.dirname(ledger.work), "INCIDENT.md")
        inc = cand if os.path.exists(cand) else None
    if inc and os.path.exists(inc):
        text = open(inc, errors="replace").read()
        lines = text.splitlines()
        logged = set(ids)
        groups = {re.match(r"^E-\d+", i).group(0) for i in ids}

        # citations
        cited = set()
        for m in CITE_RE.finditer(text):
            a = int(m.group(1))
            if m.group(3):
                for n in range(a, int(m.group(3)) + 1):
                    cited.add(f"E-{n:02d}")
            else:
                cited.add(f"E-{a:02d}" + (f".{m.group(2)}" if m.group(2) else ""))
        for c in sorted(cited, key=lambda s: [int(x) for x in re.findall(r"\d+", s)]):
            if c not in logged and c not in groups:
                problems.append(f"{inc}: cites {c}, which is not in query-log.tsv")
        failed = {r["id"] for r in rows if r.get("status") == "error"}
        for c in sorted(cited & failed):
            warnings.append(f"{inc}: cites {c}, whose status is error; make sure it is cited as a failed query, not a finding")

        # placeholder times anywhere in table cells
        for n, line in enumerate(lines, 1):
            if re.search(r"\b\d{2}:[0-9x]x\b|~\d{2}:\d{2}|\bapprox(?:\.|imately)?\s+\d{2}:\d{2}", line):
                warnings.append(f"{inc}:{n}: approximate or placeholder time; record the exact time or 'unknown'")

        # evidence table: a time without a date is ambiguous once a ledger spans midnight UTC
        in_ev, dateless = False, 0
        for line in lines:
            if line.startswith("## "):
                in_ev = line.lower().startswith("## evidence references")
                continue
            if in_ev and line.startswith("|"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if any(re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", c) for c in cells):
                    dateless += 1
        if dateless:
            warnings.append(f"{inc}: {dateless} evidence rows give a run time without a date; use the full UTC timestamp from query-log.tsv")
        if len(lines) > 300:
            warnings.append(f"{inc}: {len(lines)} lines. Keep the Summary short and consider moving the Evidence references table to incident-work/EVIDENCE.md (generated from query-log.tsv) so the file stays readable in one pass")

        # timeline order
        in_tl = False
        prev, prev_n = None, None
        for n, line in enumerate(lines, 1):
            if line.startswith("## "):
                in_tl = line.lower().startswith("## known timeline")
                prev = None
                continue
            if in_tl and line.startswith("|"):
                cell = line.split("|")[1].strip()
                m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2})?))?", cell)
                if m:
                    key = m.group(1) + " " + (m.group(2) or "00:00")
                    if prev and key < prev:
                        problems.append(f"{inc}:{n}: timeline out of order ({cell!r} after line {prev_n})")
                    prev, prev_n = key, n

        # header freshness
        m = re.search(r"^Last updated:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        latest = max((r["run_at"][:10] for r in rows if ISO_RE.match(r["run_at"])), default=None)
        if m and latest and m.group(1) < latest:
            warnings.append(f"{inc}: 'Last updated: {m.group(1)}' is older than the latest evidence run ({latest})")

        # cross-incident references
        for m in re.finditer(r"`?(\.\./[^`\s)]+?/INCIDENT\.md)`?", text):
            target = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(inc)), m.group(1)))
            if not os.path.exists(target):
                problems.append(f"{inc}: cross-incident reference {m.group(1)} does not exist (directory renamed?)")

        # secrets
        for n, line in enumerate(lines, 1):
            for pat, label in SECRET_PATTERNS:
                for m in pat.finditer(line):
                    s = m.group(0)
                    if "card number" in label:
                        digits = re.sub(r"\D", "", s)
                        if not (13 <= len(digits) <= 19 and luhn_ok(digits)):
                            continue
                    if re.search(r"[0-9a-f]{64}", s):  # a SHA-256 hash is fine
                        continue
                    warnings.append(f"{inc}:{n}: {label}: {s[:40]}...")
    elif args.incident:
        problems.append(f"incident file not found: {args.incident}")

    # 5. runner scripts preserved
    bindir = os.path.join(ledger.work, "bin")
    if not os.path.isdir(bindir):
        warnings.append("incident-work/bin/ is missing: copy the evidence runner and any helper scripts there so the tooling that produced the evidence survives the session")

    for w in warnings:
        print(f"WARN  {w}")
    for p in problems:
        print(f"FAIL  {p}")
    print(f"verify: {len(rows)} evidence records, {len(problems)} failures, {len(warnings)} warnings")
    sys.exit(1 if problems else 0)


# --------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="evidence.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=os.environ.get("INCIDENT_WORK", "incident-work"), help="working directory (default $INCIDENT_WORK or ./incident-work)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, query=False):
        p.add_argument("--id", help="explicit evidence id (refused if it exists)")
        p.add_argument("--range", help="time range covered, in UTC, e.g. '2026-10-10T00:00Z to 2026-10-13T00:00Z'")
        p.add_argument("--sensitive", action="store_true", help="record holds card data, secrets, or personal data beyond account identifiers")
        p.add_argument("--supersedes", help="earlier evidence id this replaces (wrong window, failed query)")
        p.add_argument("--note", help="one line of context: why this was run")
        p.add_argument("--show", type=int, default=40, help="rows to print (default 40)")

    sub.add_parser("init", help="create the working directory and ledger files").set_defaults(fn=cmd_init)
    sub.add_parser("next", help="print the next free evidence id").set_defaults(fn=cmd_next)

    p = sub.add_parser("run", help="run a read-only command and record it")
    common(p)
    p.add_argument("--source", required=True, help="what was queried, e.g. 'psql replica payments', 'jq over E-05'")
    p.add_argument("command", nargs=argparse.REMAINDER, help="-- command and arguments")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("nrql", help="run a read-only NRQL query via NerdGraph")
    common(p)
    p.add_argument("query")
    p.set_defaults(fn=cmd_nrql)

    p = sub.add_parser("athena", help="run a read-only Athena query")
    common(p)
    p.add_argument("query")
    p.set_defaults(fn=cmd_athena)

    p = sub.add_parser("note", help="record evidence read through a tool without a CLI (MCP, console, screenshot)")
    common(p)
    p.add_argument("--source", required=True, help="e.g. 'Slack #major-incident (C0C96RN4UAH) via MCP slack_read_channel'")
    p.add_argument("--query", help="the filter, channel, thread ts, HogQL, JQL or URL used")
    p.add_argument("--tool-timezone", help="timezone the tool displayed times in, if not UTC (e.g. 'UTC+10 (Slack MCP)')")
    p.add_argument("--file", help="file holding the result text exactly as returned")
    p.add_argument("--text", help="result text inline (short results only)")
    p.set_defaults(fn=cmd_note)

    p = sub.add_parser("import", help="copy an exported file into the ledger unchanged")
    common(p)
    p.add_argument("--source", required=True)
    p.add_argument("path")
    p.set_defaults(fn=cmd_import)

    p = sub.add_parser("derived", help="record a local analysis over earlier evidence")
    common(p)
    p.add_argument("--from", dest="frm", required=True, help="comma-separated input evidence ids")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_derived)

    p = sub.add_parser("register", help="record original source files without copying them")
    p.add_argument("--note")
    p.add_argument("paths", nargs="+")
    p.set_defaults(fn=cmd_register)

    p = sub.add_parser("seal", help="write a dated checkpoint manifest over the ledger, answers, scripts and INCIDENT.md")
    p.add_argument("--incident")
    p.set_defaults(fn=cmd_seal)

    p = sub.add_parser("verify", help="check the ledger and INCIDENT.md for auditability problems")
    p.add_argument("--incident", help="path to INCIDENT.md (default: next to the working directory)")
    p.set_defaults(fn=cmd_verify)

    args = ap.parse_args(argv)
    v = getattr(args, "command", None)
    if isinstance(v, list) and v and v[0] == "--":
        args.command = v[1:]
    args.fn(args, Ledger(args.work))


if __name__ == "__main__":
    main()
