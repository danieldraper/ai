---
name: railway-diagram
description: Explain operation or workflow logic with a source-backed railway diagram showing success, failure, recovery, and terminal outcomes. Use for Trailblazer operations or comparable branching logic in standalone inspections and PR explanations.
---

# Railway diagram

Make the important logic visible: what runs, what branches, what gets skipped, what recovers, and how execution ends. Railway layout is a presentation technique; do not assume the application uses Trailblazer or a two-track execution model.

## Trace the actual wiring

Establish the requested operation/workflow, source revision, entry arguments/context, and callers. For change reviews, resolve base/head and inspect both versions where behavior differs. Read step implementations and the surrounding orchestration, not just method names.

Build a compact transition inventory before rendering: step, outcome/condition, next step or terminus, relevant state change/side effect, and source location. Capture early returns, rejection, exceptions/rescue, retries, recovery, nested operations, and additional termini when present. Mark unknown behavior rather than completing the picture by assumption.

For Trailblazer, inspect the pinned framework version and actual DSL wiring, including inherited steps, macros, subprocesses, custom outputs/signals, and track changes. Consult [the operation documentation](https://trailblazer.to/2.1/docs/operation/) when semantics are uncertain; match documentation to the installed version. Do not assume every false result, exception, or failed subprocess follows the same path.

A failure normally continues according to its wired downstream path; it does not automatically visit every error handler. In particular, failure after a handler's position need not run that earlier handler. Show an exception leaving the operation separately unless code explicitly catches and maps it. Do not invent retry bounds or imply rollback/compensation without implementation evidence.

For other frameworks, derive branching from their actual control flow. Use additional lanes, decision nodes, or separate views when a binary railway would misrepresent it.

## Draw the operation

Prefer a left-to-right happy path, with failure/rejection below and recovery/retry paths distinctly labelled. Enclose related steps in a named operation boundary. Label the entry and every relevant terminal outcome. Show nested operations as collapsed steps with a separate detail when their internal behavior matters.

Use green for success, red for rejection/failure, amber for recovery/retry/pending, and labels as well as color. For a diff, use a strong outline plus `changed` label; mute unchanged context. Use labelled dashed arrows only for async handoffs and separate response completion from deferred outcomes. Include a legend. When available, follow the shared [visual conventions](../code-flow/references/visual-conventions.md); the rules here are sufficient if that companion skill is not installed.

Keep the diagram faithful to execution order. Attach failure edges to the exact step that emits them; distinguish recovery that rejoins success from handling that still terminates in failure. Mark relevant persisted state, external effects, and proven transaction boundaries. A failure terminus does not mean earlier uploads, events, or writes were undone.

Mermaid flowcharts are a suitable baseline; use SVG/static rendering when it provides clearer railway layout. An installed Archify skill may be used for an optional interactive view if it can preserve these semantics. Do not force the graph into a renderer that loses important routing. Keep an inline/static view for PR readers.

For a larger component flow, invoke `code-flow` when available, or supply a small overview with the operation as one node. Reuse names so the reader can connect the two levels.

## Verify and hand over

Walk at least the successful path and each materially distinct branch through the transition inventory and source. This is a source consistency check, not a claim of runtime execution. Include actual traces/tests separately when available and authorized. Do not invoke an operation against live data simply to obtain a diagram.

Inspect the rendered artifact where possible for incorrect edges, clipped labels, hidden termini, and confusing crossings. State rendering limitations. Deliver the diagram, a short explanation of the important branches, source references/revision, and unresolved conditions. Keep artifacts local by default; do not edit application code, commit, or publish unless requested.
