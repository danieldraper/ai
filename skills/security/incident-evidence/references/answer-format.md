# Answer format

Use this structure for every question. Keep sections short; a section with nothing to say gets one line saying so. Do not pad sections to fill the template.

```markdown
## Q-<nn>: <question restated in one line>
<!-- follow-ups: "## Q-<nn> (follow-up <n>): ..." -->

> Preservation warning: <only if a relevant source is close to expiring and unpreserved; omit otherwise>

**Short answer:** <one or two sentences, including the bounds if the answer is a range>

### What the evidence shows
- <finding> [E-xx]

### What we can reasonably infer
- <inference> — because <reasoning from E-xx>

### What cannot be known
- <unknown> — because <retention gap / not logged / not collected / sampled>

### Bounds
- Earliest possible: <YYYY-MM-DDTHH:MM:SSZ> [inclusive | exclusive] — rests on <E-xx | assumption: ...>
- Latest possible: <YYYY-MM-DDTHH:MM:SSZ> [inclusive | exclusive] — rests on <E-xx | assumption: ...>

### Worst case not ruled out
<the worst plausible reading the evidence cannot exclude, stated explicitly>

### Alternative explanations
- <explanation> — <evidence for or against>

### Evidence that could narrow this
| Priority | Source | What to look for | Retention risk |
| --- | --- | --- | --- |

### Contradictions and assumptions
- <conflict with stated facts, or premise that is an assumption rather than a finding>

### Confidence: <high | medium | low>
<one line of reasoning>

### Report wording
<short paragraph, plain and factual>

### Timeline and follow-ups
- Proposed timeline entries: <YYYY-MM-DDTHH:MM:SSZ> — <event> [E-xx] (<confirmed | inferred>)
- New open questions: <question>
- Changes to earlier answers: <Q-xx: what changes, or "none">
```

Save each answer to `incident-work/answers/Q-<nn>.md` (follow-ups as `Q-<nn>-f<n>.md`) as soon as it is written, before asking whether to update `INCIDENT.md`. An answer that exists only in the conversation is lost when the session ends.

## Section rules

**Evidence shows** contains only what a cited source directly records. Each item carries an evidence reference. Pasted extracts are cited as such. A statement about how a system behaves (what an endpoint returns, what a status code means, how a token is validated) is not evidence unless you read the code or documentation in this session; cite it as `[source: <file or doc>]` or move it to Infer with `[assumption]`. "Requested" is not "returned": a log line showing `offset=5000` proves the request, not that 5,000 records existed.

**Infer** states the reasoning, not just the conclusion, so a reviewer can reject the step if they disagree.

**Cannot be known** distinguishes permanently unknowable (logs gone, never logged) from not yet known (source exists but not collected). Not-yet-known items belong in the narrowing table too.

**Bounds** apply wherever the answer is a time, count, or scope that evidence does not pin down. Each bound names what it rests on, such as the earliest retained log, the deploy that introduced a route, a token lifetime, or a containment action. A bound that rests on an assumption says so. Write every time as `YYYY-MM-DDTHH:MM:SSZ` and mark it inclusive or exclusive; do not mix formats within an answer.

**Worst case** is the most severe reading not excluded by evidence, not the most severe imaginable. If the evidence rules out the worst case, say what rules it out.

**Alternative explanations** cover benign and malicious readings, such as a legitimate user, internal testing, monitoring or scanners, a misconfigured integration, or a second actor.

**Narrowing table** names a specific source and a specific query or artefact, not a category. Order by how much the result would narrow the answer, and put sources at risk of expiring first.

**Confidence** is one level. If sub-claims differ, the headline is the lowest of them and the reasoning line gives the split ("high that X; medium on Y").

- **High:** directly supported by primary evidence that covers the relevant period and event types, with no material contradiction.
- **Medium:** depends on inference from evidence, or on evidence with partial coverage, sampling, or one unverified assumption.
- **Low:** rests mainly on assumptions, reported statements, or significant gaps.

**Report wording** states the finding at the confidence the evidence supports. Use "the evidence shows" for confirmed items, "the evidence indicates" for inferences, and give ranges as ranges. Name retention limits plainly ("logs before 13 September 2026 were not available"). Do not write "irrefutable", "proves", "conclusive" or "definitively"; if asked for irrefutable evidence, give the strongest evidence and state what would still be needed to exclude the alternatives. Include no unsupported speculation, no blame, and no secrets or unnecessary personal data.

## Follow-ups

A follow-up to an answered question is headed `## Q-<nn> (follow-up <n>): <question>` and keeps at least: Short answer, What the evidence shows, Confidence, Report wording, and Changes to earlier answers. Any count or time that differs from the earlier answer is reconciled explicitly (which query, which filter, why the numbers differ) rather than restated. Sections with nothing to add can be collapsed into one line: `Sections omitted: Bounds, Alternative explanations (nothing to add).`
