---
name: pr
description: Write or update a pull request description with a clear problem statement, visual explanation of changed behavior, actual verification evidence, and concrete merge risks. Use for PR bodies and reviewer briefings; not a substitute for code review.
---

# PR

Write for a reviewer who has not seen the conversation. Explain the concrete problem and resulting behavior before implementation details. Use the project's domain language and `GLOSSARY.md` when present; do not require a glossary to proceed.

## Important

- Never force push without explicit user permission for the relevant operation. This includes `--force`, `--force-with-lease`, and equivalent ref updates. A request to create or update a PR does not grant that permission.
- Never commit `.env` files, credentials, or secrets. Before committing, inspect the staged file list and diff for sensitive files and values without printing secrets. If any are present, exclude them from the commit while preserving the user's local files and report the issue with values redacted. Do not assume `.gitignore` protects files already tracked by Git.

## Establish the change

Read the repository's PR template and contribution instructions, the originating request/spec when available, and the actual diff. Determine the intended base and head, capture their revisions, and account for relevant working changes. Do not silently describe local uncommitted edits as part of a published PR. If the base cannot be established, ask rather than comparing against an arbitrary branch.

Describe the final implementation, not the conversation history or abandoned approaches. Respect the repository template and map the guidance below into it instead of replacing required sections.

Drafting a description does not authorize publishing, opening/updating a PR, committing, merging, or uploading artifacts. Perform those actions when requested or already authorized. Follow the host's PR linking requirements when working on an actual PR.

## Create or update the PR

When asked to create or update a PR, prefer updating the existing open PR for the intended repository and head branch. Use `gh pr view` or `gh pr list` to establish its URL, state, head, and base; do not select an unrelated PR merely because it targets the same base branch.

- If an appropriate open PR exists, update it with `gh pr edit <number-or-url> --title <title> --body-file <file>`.
- If none exists, create it with `gh pr create --base <base> --head <head> --title <title> --body-file <file>`. Do not treat authentication, network, or lookup errors as proof that no PR exists, and do not create a duplicate after an uncertain creation result; check again first.

Write the exact multiline Markdown body to a temporary file and pass it through `--body-file` to preserve formatting and avoid shell interpolation. Use explicit repository selection when needed. Preserve the existing PR's intended base, draft status, and unrelated metadata unless a change is requested.

After creation or editing, verify the resulting PR with `gh pr view`, follow any host-required PR linking workflow, and return its full URL. If the operation fails, report the failure rather than claiming the PR was updated or created.

## Summary and visual explanation

Lead with one or two sentences: what triggered the problem, and what now happens differently. For behavioral changes, prefer an entry-to-outcome flow with a closer view of significant branching logic when useful. Keep unchanged context only where it explains the change.

Use independent skills when available:

- `code-flow` for entry points, component interactions, calls, data movement, asynchronous work, side effects, and outcomes.
- `railway-diagram` for operation-level success/failure routing, decisions, recovery, and termini.
- `archify` optionally for larger interactive maps or before/delta/after exploration, when installed and suitable. Request source-backed evidence explicitly. Treat its diagram/layout validation as distinct from correctness or merge-safety evidence.

These skills can also be invoked for standalone code inspection. Do not install a missing skill or make the PR depend on it. Fall back to a source-backed Mermaid diagram or small static view using the guidance below.

A useful hybrid has a component overview and a separate detailed operation view with matching names. Do not force every call and decision into one crowded diagram. For small non-behavioral changes, a brief explanation, file tree, diff sketch, or pseudocode may be sufficient. Pseudocode explains behavior; it does not prove execution.

### Visual contract

- Show relevant entry points and actual exits, including failure/rejection and asynchronous outcomes where affected. Distinguish a response or enqueue from completed background work.
- Group request handling, operations, background processing, storage, and external systems where relevant.
- Use green for successful progression, red for failure/rejection, amber for retry/recovery/pending work, and muted styling for unchanged context. Mark changed nodes/edges with a strong border or line and an explicit `changed` label, not a conflicting second color meaning.
- Use labelled dashed arrows for asynchronous handoffs, solid arrows for synchronous progression, and labels such as `unverified` for unresolved relationships. Include a small legend; color alone must not carry meaning.
- Trace nodes and edges to the actual implementation at the assessed revisions. Link important code locations. Do not invent ordering, consumers, rollback, or recovery to complete a picture. Distinguish source-derived behavior from runtime-observed behavior.
- Show before/after views only when the difference is difficult to understand in one annotated flow. Use consistent node identities, layout, and visual meanings across both.

Keep the essential visual readable in the PR itself using supported Mermaid or an accessible static image. Interactive HTML is an optional companion, not the only explanation. Local filesystem links will not work for other PR readers: use repository permalinks or authorized attachments. Keep private artifacts local until sharing is authorized and avoid sensitive data. Inspect rendered diagrams where tools permit; disclose unverified rendering.

## Evidence

Report actual evidence relevant to the claim: screenshots for visual changes, executed commands and results for behavior, and logs or persisted state for side effects. Show before/after when observed. If a before-state reproduction was not performed, say so rather than inventing one. For a new feature, describe the previous limitation and the checks actually run.

Include the exact useful command/test name, outcome, environment or revision where material, and evidence links. A proposed test or pseudocode is not a passing test. A green suite alone does not prove every displayed path. List relevant untested cases and blocked checks without burying them in prose.

## Merge risk

Describe concrete affected users, systems, contracts, records, and likely failure modes. Keep this proportional to the change; avoid hypothetical risk inventories.

Explain rollback, distinguishing reverting code from reversing persisted data or external side effects. Note migrations, compatibility windows, feature flags, emitted events, uploads, and irreversible actions when applicable. A one-way/two-way label is optional shorthand, not a replacement for the actual rollback constraints.

## Default body

Use this structure only when the repository has no required template. Omit inapplicable detail and scale length to complexity.

```markdown
## Summary

<Concrete problem and resulting behavior.>

<Inline overview diagram; operation detail only when useful.>
<Short explanation of changed paths and important code links.>

## Evidence

- Before: <observed previous behavior, or explicitly not reproduced>
- After: <actual command/result or visual evidence>
- Limits: <relevant blocked or untested behavior, if any>

## Merge risk

- Affected scope: <users, systems, data, or contracts>
- Failure modes: <concrete material risks>
- Rollback: <steps and limits, including persistent/external effects>
```

## Source

Adapted from [Matt Pocock's PR skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/pr/SKILL.md), with the repository owner's visual review preferences.
