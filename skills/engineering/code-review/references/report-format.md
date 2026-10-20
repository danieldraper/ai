# Report format

A finding is written once, as the comment the author will read on the PR. Severity, confidence, location and lens are metadata on a line above the comment; they do not appear inside it. The comment body must stand on its own when pasted onto the diff line.

Bullets over paragraphs, everywhere in the report. A paragraph is for one idea that needs two or three connected sentences. A set of facts, steps or instructions is a bulleted list, one item per line. If a paragraph is doing the work of a list, it is a list.

## A finding

```markdown
1. **<Severity>** · <Confirmed|Plausible> · `path/to/file.rb:42` · also <Lens, Lens>

   <One or two sentences: what the change does and what it lost or broke. Name the before and the after.>

   - <Why it matters at this revision: which paths reach it.>
   - <How the sibling code differs.>
   - <What the tests pin and no longer pin.>

   🧠 **Suggestion:**
   - <One instruction to the author, with its reason.>
   - <Next instruction.>

   🔑 **Security:**
   - <One fact per bullet. Only when the security lens adds something on this root cause.>
```

Severity: **Blocker**, **Should fix**, **Consider**, **Nit**. Confidence: **Confirmed** (traced at this revision) or **Plausible** (depends on something not read). `also` lists the other lenses that contributed an angle; omit it when none did.

Angle labels, in this order after the suggestion, each only when that lens has something of its own to say on the same root cause:

| Label | Lens |
| --- | --- |
| 🔑 **Security:** | Security |
| ⚡ **Performance:** | Performance |
| 🏗️ **Architecture:** | Architecture |
| 📐 **Standards:** | Standards and patterns |
| 📋 **Spec:** | Spec |

A pointer with no new content ("same as Correctness #1") is not an angle; drop it and let the `also` list record the contribution.

## Writing the comment

- **Lead sentence, then bullets.** The opening sentence states the mechanism. Everything after it is a bullet unless it is a single idea that needs connected sentences.
- **One fact or one instruction per bullet.** A bullet is one or two sentences. If a bullet needs "and also", split it.
- **No template labels.** No `Evidence:`, `Fix:`, `Spec says:` or `Would be settled by:`. The spec is quoted inline: the ticket says "…". What would settle a Plausible point is its own bullet, last in the group it belongs to.
- **Inline code for every identifier**: methods, constants, kwargs, file names, event names, config keys, error classes. `Alert.fire`, `exception: nil`, `error_backtrace`, `attributes.exclude`.
- **Short sentences.** Prefer "X, because Y" to a parenthetical. A parenthetical is fine for a gloss on a name, such as `rendered_record` (the 120-char ABA line with BSB, account number and name).
- **Address the author.** Suggestion bullets are imperative: "Give `Alert.fire` an `exception: nil` kwarg", "Re-pin `error_class` in the spec". Say why each step is there.
- **Severity and confidence stay on the metadata line.** Inside the comment, confidence shows as plain statements: "Traced sources: …", "At this revision those keys are ids and dates."
- **No cross-reference chains.** The comment never says "see Correctness #1". If another lens has an angle, it is a labelled bullet group here.
- **Location is implicit.** The comment is posted on the line in the metadata, so it does not repeat the path. It may name other files and lines that matter, such as the sibling hook or the spec example.

## Worked example

A finding owned by Correctness with a Security angle. This is the shape to match.

```markdown
1. **Should fix** · Confirmed · `components/direct_entry/app/jobs/assignment_job.rb:12` · also Security, Standards, Architecture, Spec

   The `retries_exhausted` alert passes `error: exception&.message` raw. The old `Log.error(..., exception:)` ran the message through `Platform::Logging::ErrorMessage.for` and added `error_class` and `error_backtrace`.

   - Exceptions that reach exhaustion include ones raised outside the operation boundary, such as `find_by`, the jsonb EventRecord query and `Mapper.to_event`, so a `StatementInvalid` now arrives unsanitised.
   - The sibling `upload.retries_exhausted` hook still emits the structured fields, so the two exhaustion alerts now differ in shape.
   - The old spec pinned `error_class` and `error_message`. The new one pins only `error: "boom"`.

   🧠 **Suggestion:**
   - Give `Alert.fire` an `exception: nil` kwarg and expand it with the same helper `Log` uses, by moving `Log.error_fields` somewhere both can call.
   - Do the expansion before notify so no adapter receives an Exception object.
   - In the New Relic adapter, join or drop `error_backtrace`, because the agent flattens an Array into one attribute per element.
   - Re-pin `error_class` and the sanitised message in the spec.

   🔑 **Security:**
   - The raw message now reaches New Relic custom events, which are queryable by anyone with account access and not covered by `attributes.exclude`.
   - Traced sources: the `:unknown` Failure wrapper embeds any `StandardError` message, and `:conflict` embeds the full `PG DETAIL: Key (...)=(...)` text.
   - At this revision those keys are ids and dates, but `rendered_record` (the 120-char ABA line with BSB, account number and name) flows through the same projection and `Dry::Struct` path the sanitiser was written for.
   - Would be settled by a concrete raise on this path that quotes a row.
```

What this replaces: a Correctness entry with `Fix:` and "See Security #1", a Security entry with "Same root as Correctness #1", and one-line pointers in Standards, Architecture and Spec. Five entries became one comment, and the Standards, Architecture and Spec angles were dropped because they added nothing the comment did not already say.

## Single lens (what each sub-agent returns)

Keep it under roughly 400 words for a typical change; a large diff may need more, a tiny one much less. Omit empty subsections. Write each finding in the comment form above so the aggregator can lift it; a lens writes only its own angle, and the aggregator folds angles together.

```markdown
## <Lens name>

### Findings
1. **<Severity>** · <Confirmed|Plausible> · `path/to/file.rb:42`

   <Lead sentence.>

   - <evidence bullets. For standards, name the file and rule breached, or the sibling and what it does. For spec, quote the ticket.>

   🧠 **Suggestion:**
   - <instruction with reason>

### Noticed, out of scope
- <one line each; the owning lens decides>

### Checked and fine
- <one line per area examined that held up, so the aggregator knows what was covered>
```

## Aggregate (what the user receives)

```markdown
# Review: <branch or PR title> (<base>...<head>, <n> files, +<a>/-<d>)

**Verdict:** <Mergeable as-is | Mergeable after the should-fix items | Blocked by N items>.
- <What is sound about the change, one line.>
- <What regressed or is missing, one line each.>

## Blockers
- [<Lens>] `file:line` <summary>  ← one line each, across all lenses; "None" if none

## Correctness
<n> findings (<counts by severity>).
- Verified by: <tracing, probes, specs run and result>.

<findings in comment form>

Checked and fine:
- <one line per area>

## Security
Folded into: Correctness #1 (raw exception message reaches New Relic).

<findings this lens owns>

Checked and fine:
- <one line per area>

## Performance
No findings.
- Checked: <one line per area>

## Standards and patterns
Folded into: Correctness #1 (exception convention), Correctness #2 (caller frame).

...

## Architecture
...

## Spec
Source: <ticket id, state, where read from>.
- <requirements implemented faithfully, one line>
- <explicitly out of scope, one line>

<findings, or "No spec found; lens skipped." with where you looked>

## Coverage
- Lenses run / skipped and why
- Files excluded (generated, vendored, lockfiles)
- Tooling run and result, or not available
- Findings that remain Plausible and what would settle them, one per bullet
- Repo state: <behind main by n, merge-tree result, worktree removed>
```

Rules for the aggregate:

- **One finding per root cause.** When two or more lenses flag the same cause, the lens whose question it answers owns it. The others contribute an angle group if they have one, and are listed in `also`. Their own sections do not repeat the finding.
- **Each lens section opens with a "Folded into" line** naming the findings it contributed to, so the reader can see that the lens ran and what it found even when it owns nothing. Omit the line when the lens contributed nothing.
- **Counts cover owned findings only.** A contribution to another lens's finding is not counted twice.
- **Section intros, "Checked and fine" and Coverage are bullets**, one item per line. Never a paragraph that strings five checks together with semicolons.
- Keep the lens order fixed so readers learn where to look.
- Do not rank findings across lenses. The verdict line counts blockers; it does not pick a winning lens.
- A lens with no findings keeps its heading and says "No findings." followed by a "Checked:" bullet list, so absence is visibly deliberate.
- Quote code sparingly: enough to locate and understand, not whole functions.
