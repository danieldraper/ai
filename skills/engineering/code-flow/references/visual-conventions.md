# Visual conventions

Use across component flows and railway diagrams. Adapt layout to the question while keeping meanings consistent.

| Treatment | Meaning |
| --- | --- |
| Named group/container | A component or boundary: request handling, operation, worker, storage, external service |
| Green path or outcome | Successful progression |
| Red path or outcome | Failure or rejection |
| Amber path or outcome | Retry, recovery, wait, or pending work; label which |
| Strong border/line plus `changed` label | Modified in the compared change |
| Muted node | Unchanged supporting context |
| Solid labelled arrow | Synchronous/control progression |
| Dashed arrow labelled `enqueue`, `publish`, or equivalent | Asynchronous handoff |
| Explicit `unverified` label | Relationship or behavior not established; do not reuse async styling as its sole indicator |

Include only relevant meanings in a small legend. Do not depend on color alone: label branches and outcomes, distinguish shapes/lines where useful, and use readable text/background contrast in the intended renderer. Avoid assigning green both to success and added code.

Prefer left-to-right progression. Keep related nodes together, route failure/recovery paths separately, and minimize crossings. Use consistent identifiers across overview and detailed diagrams. Break a crowded diagram into an overview and focused detail instead of shrinking text.

A component name is not a claim that its operation succeeded. Show return/HTTP outcomes separately from background completion, and publication separately from consumption. Label transaction boundaries only when established; mark external effects separately from database writes. Do not imply that an error rolls back previously completed effects.

For comparisons, preserve layout and identities where possible. Highlight changed edges as well as nodes. Keep enough unchanged context to explain ownership and order; omit unrelated infrastructure.

Diagrams derived from source describe possible behavior. Runtime traces describe observed executions. Identify which is being shown and pin it to the relevant revision. Put code references beside the visual or in an accessible node/evidence list; do not overload every node with long paths.
