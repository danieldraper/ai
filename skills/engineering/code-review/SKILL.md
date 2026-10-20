---
name: code-review
description: "Review a code change (branch vs base, PR number, commit range, or uncommitted work) in Ruby, Ruby on Rails, or Go through six separate lenses run as parallel sub-agents: correctness, security, performance, standards and patterns (documented standards, conventions in the surrounding code, language idioms, Fowler smells), architecture, and spec conformance. Use whenever the user asks to review code, review a branch or PR, check a change before merge, \"review since X\", or asks whether a change is safe, idiomatic, fast enough, well-placed, or matches the ticket, even if they only name one of those concerns."
---

# Code review

Act as a senior reviewer who knows Ruby, Rails, and Go and has read this repository before. Find what matters, prove it from the code at the reviewed revision, and say what to do about it. A finding is an evidenced defect or risk with a location, not a pattern match on the diff.

Review along separate **lenses** so one cannot mask another: a change that follows every convention can still implement the wrong thing, and a change that matches the ticket can still leak data or add an N+1. Each lens runs as its own sub-agent with a narrow brief, then this skill verifies and aggregates.

Reviewing does not authorise editing application code, committing, or posting to a PR. Do those only when asked.

## 1. Establish the change

Resolve exactly what is under review and record the commands you will hand to sub-agents.

| User gave | Diff | Commits |
| --- | --- | --- |
| A ref ("since main", a SHA, a tag) | `git diff <ref>...HEAD` (three-dot, merge-base) | `git log <ref>..HEAD --oneline` |
| A PR number or URL | `gh pr diff <n>`, or check out the head and diff against the PR base | `gh pr view <n> --json commits,title,body,baseRefName` |
| A branch name | `git diff <default-branch>...<branch>` | `git log <default-branch>..<branch> --oneline` |
| Nothing | merge-base with the default branch, plus uncommitted work (`git diff` and `git diff --cached`) | as above |

Before spawning anything, confirm the ref resolves (`git rev-parse`) and the diff is non-empty. If uncommitted changes exist alongside a ref-based review, say whether they are included; do not silently mix them in. List the changed files with `--stat` and note which are generated, vendored, lockfiles, or fixtures so lenses can skip them.

## 2. Profile the repository

Spend a few minutes here so the six sub-agents do not each rediscover the same facts. Build a **context pack** containing:

- **Languages and frameworks** touched by the diff: `Gemfile`/`Gemfile.lock` (Rails version, Trailblazer, Sidekiq, RSpec, Sorbet), `go.mod` (Go version, which matters for loop-variable semantics and generics, web framework, ORM/driver). Note the database from `config/database.yml` or driver imports.
- **Documented standards**: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `STYLE.md`, `CLAUDE.md`, `AGENTS.md`, `docs/` guides, ADRs, `.rubocop.yml`, `.golangci.yml`, `.editorconfig`, PR templates. A documented repo standard always wins over the generic guidance in this skill.
- **Tooling already enforced**: linters, formatters, type checkers, and security scanners in CI. Lenses skip anything these catch. If a linter is configured and runs quickly, run it on the changed files only (`rubocop <files>`, `golangci-lint run ./changed/pkg/...`, `go vet`, `brakeman -q` where present) and include the output. Do not install tools.
- **Neighbouring code**: for each changed or new file, the two or three sibling files that do the same job (other controllers, operations, jobs, handlers, repositories, tests of the same kind). These are the ground truth for "existing patterns"; the standards lens compares against them.
- **Spec source**, in this order: issue or ticket references in commit messages, the PR body, and branch name (fetch with `gh issue view`, `gh pr view`, or the `jira` CLI when present); a path the user supplied; a spec under `docs/`, `specs/`, or `.scratch/` matching the branch. If nothing is found, say so and run without the spec lens rather than blocking.

## 3. Choose the lenses

Run every applicable lens by default. The user can narrow with words like "just security" or "skip spec"; honour that. Drop a lens only when it cannot apply (no spec found; a docs-only diff has no performance surface).

| Lens | Question it answers | Reference to read |
| --- | --- | --- |
| Correctness | Does it do what it appears to do, on every path? | language file, *Correctness* section |
| Security | Can an attacker or an unlucky input turn this into a breach? | language file, *Security* section |
| Performance | Will this be slow, unbounded, or expensive at production scale? | language file, *Performance* section |
| Standards and patterns | Does it match documented standards, the neighbouring code, and language idioms? | language file, *Idioms and patterns*; [smells](references/smells.md) |
| Architecture | Is it in the right place, with the right boundaries, and will it still be right after deploy? | language file, *Architecture* section |
| Spec | Does it implement what was asked, nothing less, nothing more? | the spec itself |

Language files: [Ruby and Rails](references/ruby-rails.md), [Go](references/go.md). A mixed diff gets both. Give each sub-agent the absolute path of the file(s) and the section to read; sub-agents cannot see this skill otherwise. The absolute path comes from the base directory the harness reports when it loads this skill.

For a trivial diff (a few lines in one or two files), spawning six sub-agents costs more than it returns: run the applicable lenses yourself, one at a time, with the same briefs and reporting rules, and say that you did.

## 4. Spawn the lens sub-agents

Issue all sub-agent calls together in one message so they run in parallel. Each prompt carries the same context pack plus a lens-specific brief. Include in every prompt:

- The diff and commit commands from step 1, the changed-file list, and which files to skip.
- The repository profile: frameworks and versions, database, standards files, tooling output, neighbouring files.
- The absolute reference path(s) and section to read first.
- The reporting rules below, and the [report format](references/report-format.md) for a single lens.

Reporting rules every lens follows:

- **Read beyond the diff.** Open the callers, the callee, the model, the migration, the test. A hunk rarely contains enough to judge it. Confirm the behaviour at this revision before claiming it.
- **Classify confidence.** *Confirmed* means the path was traced in the code and the failure is demonstrable. *Plausible* means it depends on something not verified; say what would settle it. Never present plausible as confirmed.
- **Assign severity.** *Blocker* (incorrect behaviour, data loss, vulnerability, outage, or an unmet spec requirement), *Should fix* (real defect or risk, or a clear breach of a documented standard), *Consider* (judgement call, smell, improvement), *Nit* (trivial; say it once, never block on it).
- **Skip what tooling enforces** and what a documented repo standard permits. Match repo conventions over personal taste; when the neighbouring code does it one way and the diff another, that inconsistency is the finding, not the diff's choice in isolation.
- **Cite evidence**: file and line, a short quote of the hunk, and for standards the file and rule breached. Give a concrete fix, not "consider improving".
- **Write each finding as the PR comment the author will read.** A lead sentence, then bullets: one fact per bullet for evidence, one imperative instruction with its reason per bullet under the suggestion. Inline code for every identifier. No `Evidence:` or `Fix:` labels; severity and confidence stay on the metadata line. The [report format](references/report-format.md) has the shape and a worked example.
- **Stay in lens.** Note an out-of-lens observation in one line under *Noticed, out of scope* rather than expanding the brief.
- **"Nothing found" is a valid result.** Do not invent findings to fill a section. Scale depth to the diff: a 20-line change gets a short report.
- **Do not modify code**, run destructive commands, or post anywhere.

Lens briefs, to paste after the common context:

- **Correctness**: "Find behaviour that is wrong or fragile: logic errors, unhandled nil/zero/empty/error paths, off-by-one, ordering and concurrency, data integrity across transactions and jobs, time and money handling, API and serialisation mismatches, and tests that do not actually exercise the change. Verify each by tracing the path."
- **Security**: "Find what the change exposes: authorization and tenant scoping on new or altered entry points, injection into SQL, shell, templates, or dynamic dispatch, unsafe deserialisation, mass assignment, SSRF and redirects, secrets or sensitive data in code, logs, or errors, weak crypto or comparison, and risky new dependencies. Trace source → validation → authorization → sink. Where money or card data is involved, idempotency, replay, and PCI boundaries are security properties. This is diff-scoped; recommend the `security-assessment` skill if the change warrants a whole-system audit."
- **Performance**: "Find what gets slow or unbounded under production load: N+1 and missing eager loading, missing indexes for new predicates, unbounded result sets, transactions held across I/O, lock contention, goroutine or memory growth, allocations in hot paths, missing timeouts and retries on external calls, cache misuse. Estimate scale from the data model and callers; say what the cost is proportional to."
- **Standards and patterns**: "Report breaches of documented standards (cite file and rule), divergences from how the neighbouring files do the same thing (cite the neighbour), non-idiomatic language use, missing or weak tests relative to the repo's testing conventions, and smells from the baseline, named and quoted. Documented standards and neighbouring conventions are hard findings; smells are always judgement calls."
- **Architecture**: "Judge placement and boundaries: business logic in the wrong layer, dependency direction, new coupling or abstraction (needed or speculative), consistency with the existing data model and error handling, backward compatibility across deploy (migrations, job arguments in flight, API and event payloads), observability of new paths, and whether this change makes the next change harder. Explain the design pressure, not just the rule."
- **Spec**: "Compare the change to the spec. Report requirements that are missing or partial, behaviour that was not asked for, and requirements that look implemented but whose implementation does not match the intent. Quote the spec for each finding. Note acceptance criteria that have no test."

## 5. Verify and aggregate

When reports return:

1. **Spot-check every Blocker and any Confirmed finding that looks surprising** by opening the code yourself. Downgrade or drop what does not hold; a wrong blocker costs the author more than a missed nit.
2. **Merge by root cause.** When two or more lenses flag the same cause, the lens whose question it answers owns the finding. Fold what the other lenses add into that one comment as labelled angle paragraphs (🔑 Security, ⚡ Performance, 🏗️ Architecture, 📐 Standards, 📋 Spec) and list them in the metadata line's `also`. A lens that only says "same as Correctness #1" contributes no angle; it is recorded in `also` and in its own section's "Folded into" line, nothing more. Do not rerank across lenses; the separation exists so no lens is silenced by another, and the "Folded into" line is how a lens stays visible when it owns nothing.
3. **Rewrite, do not staple.** The merged comment reads as one author wrote it: a lead sentence on the mechanism, then evidence bullets, then suggestion bullets with reasons, then the angle groups. Sub-agent text is raw material. Bullets beat paragraphs throughout the report: section intros, "Checked and fine" and Coverage are lists, never a paragraph of checks joined by semicolons. Check the result against the worked example in [report format](references/report-format.md) before moving on.
4. **Assemble the report** using the aggregate layout in [report format](references/report-format.md): a verdict line, blockers across all lenses, then one section per lens in a fixed order, then a short coverage note. Counts per lens cover owned findings only.
5. **Be honest about coverage.** Name lenses that were skipped and why, files excluded, tooling not run, and anything the sub-agents reported as unverified.

Keep the report local and in the conversation unless the user asked for a file or PR comments. If asked to post to a PR, each finding's comment body is posted verbatim on the file and line from its metadata line, Blockers and Should-fix items first; the remainder go in one summary comment. Never approve or request changes on the author's behalf without an explicit instruction.

## Why separate lenses

Each lens is a question a different reviewer would ask. A single "review this" prompt tends to collapse into style comments plus whichever bug is most visible, and a security reviewer reading for authorization is not also counting queries. Running them apart, with narrow briefs and the same evidence, gets closer to the review a strong team would give, and keeps the findings honest about which question each one answers.
