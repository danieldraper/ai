---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered, using the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations in a standalone HTML file or on a development-only route, switchable via a URL search param and a floating bottom bar.

When the same design question involves both appearance and behavior, use the primary branch and borrow the relevant guidance from the other. For example, a UI prototype can include a small in-memory model for partial completion, inherited records, or denied actions. Keep the combined prototype focused on the same question and label simulated behavior.

The two branches produce different artifacts, so getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** For in-app prototypes, locate code near the module or page it explores. For standalone artifacts, use the project's prototype/artifact location or an identified temporary directory. Name either clearly as a prototype. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** An in-app UI prototype starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A standalone UI or logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
4. **Skip the polish.** No permanent test suite, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Check it before handover.** Open the prototype using available browser tools, exercise variants and meaningful controls, check reset/replay behavior where present, inspect relevant viewport sizes, and check for console errors. Verify that in-app prototypes leave the normal page unchanged without the development opt-in. Report any checks that could not run; do not claim an unchecked artifact works.
7. **Keep it local and synthetic by default.** Use realistic synthetic data, in-memory actions, and no live mutations. Keep files, screenshots, and previews local unless sharing or publishing is requested. Do not embed customer data or credentials in portable artifacts.
8. **Capture the decision, then stop at the requested boundary.** Record the question, selected approach and rationale, unresolved questions, and prototype location. Keep the prototype available for review. Approval of a design alone is not a request to implement it. Modify production code, commit or archive branches, and update external issues only when those actions are within the user's requested scope. When implementation is requested, preserve the useful decisions and scenarios, implement them to production standards, and remove prototype-only wiring as part of that work.

## Source

Adapted from [Matt Pocock's prototype skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/prototype), including its UI and logic guides.
