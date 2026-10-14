# UI Prototype

Generate **several radically different UI variations** in a standalone HTML file or on a development-only route, switchable from a floating bottom bar. The user flips between variants in the browser, picks one (or steals bits from each), then throws the rest away.

For a primarily logic/state question, use [LOGIC.md](LOGIC.md). If the UI decision depends on behavior, borrow its in-memory modeling and scenario guidance without expanding the prototype beyond the design question.

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- Any time the user would otherwise spend a day picking between three vague mockups in their head.

## Choose the delivery shape

Follow the user's requested format. Standalone previews and in-app variants are both first-class options; an existing page does not override a request for a local HTML mockup.

### Standalone HTML

Use for planning, stakeholder review, or explicitly requested HTML mockups before application changes. Produce one self-contained HTML file with inline styles, scripts, and synthetic data that opens locally without a build or server. Reproduce the relevant app header, sidebar, styling, and realistic data density so variants can be judged in context. Use the same variant switcher described below with browser URL APIs rather than a framework router. Do not modify application routes to deliver this shape.

### Sub-shape A: adjustment to an existing page

Use when the decision benefits from real layout and integration constraints and in-app prototyping fits the request. Keep the existing route, data fetching, parameters, and authentication. Swap only the rendered subtree behind an explicit `?variant=` opt-in and a development-only environment gate. Without a valid opt-in, render the original page unchanged. Use synthetic fixtures by default; existing read-only test data can be used when appropriate to the task. Stub mutations.

A new section or step that naturally belongs inside an existing page can use this shape too.

### Sub-shape B: a new page

Use when in-app integration matters but no existing page is a suitable host. Follow the project's routing convention and clearly name the route as a prototype. The entire route must be unavailable outside development; hiding its switcher is insufficient. Include the surrounding app shell and realistic synthetic content so it is not judged in a vacuum.

All shapes use the same floating switcher behavior.

## Process

### 1. State the question and pick N

Default to **3 variants**. More than 5 stops being radically different and starts being noise, so cap there.

Write down the plan in one line, in the prototype's location or a top-of-file comment:

> "Three variants of the settings page, switchable via `?variant=`, on the existing `/settings` route."

This works whether the user is here to push back or not.

### 2. Generate radically different variants

Draft each variant. Hold each one to:

- The page's purpose and the data it has access to.
- The project's component library / styling system (TailwindCSS, shadcn, MUI, plain CSS, whatever).
- A clear variant identifier, e.g. `VariantA`, `VariantB`, `VariantC`, using components or standalone DOM sections as appropriate.

Variants must be **structurally different**: different layout, different information hierarchy, different primary affordance, not just different colours. Three slightly-tweaked card grids isn't a UI prototype, it's wallpaper. If two drafts come out too similar, redo one with explicit "do not use a card grid" guidance.

### 3. Wire them together

For an existing page, gate the entire prototype before selecting its variant:

```tsx
// pseudo-code, adapt to the project's framework
const variant = searchParams.get('variant');
if (!isDevelopment || !['A', 'B', 'C'].includes(variant)) {
  return <OriginalPage {...data} />;
}
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

For sub-shape A (existing page): keep all the existing data fetching above the switcher; only the rendered subtree changes per variant.

For sub-shape B (new page): enforce the development gate at the route boundary before mounting the variants and switcher.

For standalone HTML: render the selected variant in the file, defaulting to A for absent or invalid keys. A standalone file has no original application page to preserve.

### 4. Build the floating switcher

A small fixed-position bar at the bottom-centre of the screen with three pieces:

- **Left arrow**: cycles to the previous variant (wraps around).
- **Variant label**: shows the current variant key and, if the variant exports a name, that name too. e.g. `B (Sidebar layout)`.
- **Right arrow**: cycles forward (wraps around).

Behaviour:

- Clicking an arrow updates the URL search param (use the framework's router, e.g. `router.replace` on Next, `navigate` on React Router, etc) so the variant is shareable and reload-stable. Preserve unrelated query parameters and the URL fragment. In standalone HTML, use browser URL/history APIs that work when opened locally.
- Keyboard: `←` and `→` arrow keys also cycle. Don't intercept arrow keys when an `<input>`, `<textarea>`, or `[contenteditable]` is focused.
- Visually distinct from the page (e.g. high-contrast pill, subtle shadow) so it's obviously not part of the design being evaluated.
- Provide a hide/show control that can be restored after hiding, so mobile layouts and screenshots can be reviewed without the bar covering content.
- For in-app prototypes, gate the variants, switcher, and any prototype routes on the project's explicit development environment check. A URL parameter alone must not enable them in production or staging.

Share switcher behavior between variants. For in-app prototypes, use one prototype-only component; for standalone HTML, keep it inline. Avoid introducing application-wide infrastructure for a disposable artifact.

### 5. Hand it over

Perform the browser checks in [SKILL.md](SKILL.md), including each variant, switcher hide/show, URL parameter preservation, and relevant viewport sizes. For in-app prototypes, also verify the original page without opt-in and the environment gate using the project's available checks. Report any unverified gate behavior. Surface the local file or URL (and the `?variant=` keys). The user will flip through whenever they get to it. The interesting feedback is usually **"I want the header from B with the sidebar from C"**, which is the actual design they want.

### 6. Capture the answer and clean up

Once a variant has won, record which parts were selected, why, and any unresolved decisions, following [SKILL.md](SKILL.md). Preserve the alternatives locally for review. Do not automatically implement the winner, commit a branch, publish the artifact, or update an external issue.

When implementation is requested, build the selected design to production standards in the appropriate page or route and remove the prototype wiring. Archive the full prototype only through the storage or version-control workflow authorized for the task.

## Anti-patterns

- **Variants that differ only in colour or copy.** That's a tweak, not a prototype. Real variants disagree about structure.
- **Sharing too much code between variants.** A shared `<Header>` is fine; a shared `<Layout>` defeats the point. Each variant should be free to throw out the layout.
- **Wiring variants to real mutations.** Read-only prototypes are fine. If a variant needs to mutate, point it at a stub: the question is "what should this look like", not "does the backend work".
- **Promoting the prototype directly to production.** The variant code was written under prototype constraints (no tests, minimal error handling). Rewrite it properly when you fold it in.
