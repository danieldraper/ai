---
name: code-flow
description: Trace source code from entry points through components to outcomes and explain it with a source-backed visual flow. Use for standalone code inspections, architecture walkthroughs, or PR change explanations, including async handoffs and side effects.
---

# Code flow

Help the reader follow the path that matters, from trigger to observable outcome. Work from code; an attractive diagram of assumed relationships is not an explanation.

## Establish the question

Identify the requested behavior, entry points, repository, and revision. For a PR or comparison, resolve base/head and inspect the diff; for an ordinary inspection, use the current checkout and note relevant working changes. Do not require a PR or change code to explain it.

Read project terminology, relevant architecture notes, routes, callers, and tests. Follow concrete paths through controllers/handlers, operations/services, persistence, events, jobs, integrations, and exits as applicable. Include multiple entry points only where they clarify shared behavior or differences.

For each important relationship, establish its source location and meaning: synchronous call, data movement, event publication, queue handoff, return, or side effect. Inspect registered event consumers and job implementations rather than assuming publication implies execution. Distinguish scheduling, response completion, eventual completion, retries, and failure outcomes.

Record evidence while tracing. Use repository paths and symbols, plus revision-pinned links when available. Local inspection can use local file links; shared PRs need links accessible to reviewers. Tests support intent but do not prove a path was executed in this session. Label uncertain dynamic dispatch or environment-dependent relationships and state what would resolve them.

## Choose the view

Read [visual conventions](references/visual-conventions.md).

- Use a grouped left-to-right flowchart for component interactions and major outcomes.
- Use a sequence diagram when temporal ordering, responses, or asynchronous interaction is the central question.
- Use a compact before/after pair when changed topology cannot be explained clearly by highlighting changes in one view.
- For significant internal branching, invoke `railway-diagram` if available, or create a separate operation detail using the same names. Keep the overview focused on boundaries.

Mermaid is the baseline. A static SVG/image is appropriate when precise layout improves readability. If an installed `archify` skill is available and the user needs focus, path exploration, or a larger map, it can render an optional interactive companion. Request source-backed mode explicitly, verify authored relationships against code, and retain a readable static/inline view for PRs. Do not install Archify, publish diagrams, or send source elsewhere merely to generate a visual.

## Deliver and check

Include a short explanation of the behavior, the visual with a legend, important source links, and unresolved assumptions or omitted scope. Mark changed elements only when comparing an established base/head. For standalone inspection there is no need to manufacture a delta.

Check every important edge against its evidence. Inspect rendered output when tools permit: labels must fit, arrows must connect correctly, groups must not hide paths, and the important flow must remain readable. For interactive output, check the relevant focus/navigation controls. State if rendering or runtime behavior was not verified. Renderer validation is not proof of application correctness.

Keep artifacts local by default and use synthetic/redacted labels where real data is unnecessary. Preserve editable diagram source with exported artifacts when producing files. Creating a diagram does not authorize application edits, commits, or external publication.
