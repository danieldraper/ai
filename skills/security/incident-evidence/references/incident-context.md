# Incident context template

Ask for these fields when no context file exists. Offer to save them to `INCIDENT.md` in the working directory. Leave unknown fields as `unknown`, not blank, so gaps stay visible.

Rules that keep the file auditable as it grows:

- **Summary** is at most ten lines: what happened, current status, the one or two numbers that matter. Narrative, correlation analysis and device-level detail go in their own sections, not the Summary.
- **Every time** is UTC as `YYYY-MM-DD HH:MM:SS` (seconds when the source has them). No `~`, no `HH:2x`, no time without a date. If the exact time is not known, write `unknown` or a bounded range with what each bound rests on.
- **Timeline rows stay in chronological order.** Insert new rows in place; `evidence.py verify` fails on out-of-order rows.
- **Evidence IDs are allocated by the ledger** (`incident-work/query-log.tsv`), never typed by hand, and never reused. A re-run or corrected query gets a new ID and `supersedes E-xx`. A failed query keeps its ID with status `error` and is cited only as a failed attempt.
- **Cross-incident references** use the other incident's directory name as a prefix: `major-incident-12-oct-2026-214225:E-08`. Do not rename incident directories after they are referenced; if one is renamed, update every reference the same day.
- **Evidence from tools without a CLI** (Slack, PostHog, Jira, Confluence, a console, a screenshot) is still saved to the ledger: paste the returned text into a file and record it with `evidence.py note`. "Not exported" is not an acceptable value.
- When the file passes about 300 lines, move the Evidence references table to `incident-work/EVIDENCE.md` and leave a one-line pointer, so the context file can be read in one pass.

```markdown
# Incident context

Last updated: <YYYY-MM-DD, UTC>
Status: <suspected | active | partially contained | contained | closed>. <if partially contained: what remains open, in one line>

## Summary
<one line, e.g. unauthorised access via an Auth0-backed login route>

## Trigger
<what raised the suspicion, who reported it, and when (UTC)>

## Window under investigation
<start> to <end> (UTC). Why these bounds: <what sets each end>

## Affected systems
- Applications and routes:
- Identity provider tenants, applications, and connections:
- APIs and services:
- Data stores:

## Containment
| Time (UTC) | Action | By | Status | Evidence |
| --- | --- | --- | --- | --- |
| | e.g. route disabled, secret rotated, sessions revoked | | reported / verified | E-xx for the message; E-yy for the effect (401 transition, failed login) |

## Token and session lifetimes
<access token, refresh token, ID token, and application session lifetimes in force during the window; whether any were revoked at containment>

## Evidence sources
| ID | Source | Coverage (UTC) | Gaps | Retention rule | Expires | Preserved? | Tool timezone | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-01 | e.g. Auth0 tenant logs | 2026-09-13 to now | none found | <plan retention> | <date earliest data rolls off> | no | UTC | log stream to <destination>? |
| S-02 | e.g. Slack #incident channel via MCP | | | workspace retention | | no | displays UTC+10; convert from raw `ts` | |

## Sweep coverage
| Area (triage-sweep.md) | Checked | Evidence | Baseline compared | Not covered because |
| --- | --- | --- | --- | --- |
| Authentication | yes / partial / no | E-xx | yes / no | |
| Authorization and privileged actions | | | | |
| Routes and requests | | | | |
| Data access and exfiltration | | | | |
| Timing and shape | | | | |
| Logging integrity | | | | |

## Known timeline
| Time (UTC) | Event | Source | Status |
| --- | --- | --- | --- |
| | | E-xx or source | confirmed / inferred / reported |

## Indicators
| Type | Value | First seen (UTC) | Last seen (UTC) | Evidence |
| --- | --- | --- | --- | --- |
| | IP / account / user agent / session prefix / other | | | E-xx |

## Leads
| ID | Anomaly | Evidence | Benign explanations still open | Would confirm or dismiss |
| --- | --- | --- | --- | --- |
| L-01 | | E-xx | | |

## Open questions
| ID | Question | Status | Answer summary |
| --- | --- | --- | --- |
| Q-01 | | open | |

## Evidence references
Ledger: `incident-work/query-log.tsv` (one row per ID, exact query text, run time, result count, truncation, SHA-256) and `incident-work/SHA256SUMS`. Raw results: `incident-work/queries/E-xx.*`. Runner: `incident-work/bin/evidence.py`.

| ID | Source | Query or filter (summary) | Range (UTC) | Results | Status | Truncated | Run at (UTC) | File |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E-01 | | | | <count> | ok / error / superseded by E-xx | no / yes (LIMIT n) | YYYY-MM-DDTHH:MM:SSZ | queries/E-01.json |
```

Timeline status values:

- **confirmed:** directly shown by cited evidence.
- **inferred:** follows from cited evidence by stated reasoning.
- **reported:** stated by a person or third party and not yet verified. A Slack message or Confluence page saying an action was taken is `reported` until a log shows its effect (a 401 transition after rotation, a disabled user's login failing).

A row may carry a split status when the event is confirmed but the attribution is not: `confirmed (actor inferred)`.
