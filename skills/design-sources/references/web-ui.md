# Adapter: web / UI builds

Owner skills: `visual-code`, `image-to-code`, `imagegen-frontend-web`,
`minimalist-ui`, `industrial-brutalist-ui`, `website-to-hyperframes`, `codecraft`.

This is the cluster Impeccable was written for. Apply the digest's craft floor
and refuse list directly, with no translation. **The gate is blocking here.**

## Before building

1. Pick the **mode** from the surface, not the product (digest §4). A tool's
   landing page is Persuade; its dashboard is Operate; its docs are Read. The
   mode decides whether expression or scanability wins.
2. Read at least one source of incumbent visual truth (tokens, theme, CSS, an
   existing component) before editing. Never redesign from the filename.
3. **Refinement preserves; redesign replaces.** Refinement keeps identity,
   behaviour, copy, and everything outside scope. Do not split the difference by
   polishing a look you have decided to discard.

## While building

Apply the digest's craft floor in full. The four that Impeccable says models
skip most reliably, and that our own output has historically missed:

- **Browser surfaces.** Text selection, caret, scrollbars, focus rings,
  underline offset, tabular numerals. These ship with browser defaults belonging
  to no design system. Theming them is the cheapest tell that a page was built
  rather than assembled.
- **Elevation declared once**: border *or* shadow, never a 1px border under a
  wide soft shadow (the ghost card). Card radii 12–16px.
- **Real states**: hover, disabled, loading, error, empty. Not just the happy path.
- **Real copy at every breakpoint**, then fix what overflows.

Absolute bans with no brief exception: the eyebrow/kicker above a heading, and
nested cards.

## Brand interaction

Light backgrounds are Rich's default; do not let a generic "pick light or dark
from the use scene" note talk you into a dark hero on brand work.

Bishop AI palettes will trip `cream-palette` and `overused-font`. That is
expected and waived, see the brand lock in SKILL.md. Do **not** "fix" a Bishop
warm-white background or swap Open Sans to satisfy the detector; the override
handles it and the finding is reported as overridden, not failed.

## Gate

```bash
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file|dir|url> --mobile
```

Blocking. Exit 0 before delivery, always. `--mobile` adds a 390x844 pass and is
worth it on anything with a responsive claim.

**Set the type scale with media queries, not `clamp()`.** The static scan reads
computed styles through jsdom, which cannot resolve `clamp()`, so clamped
headings vanish from the sample and the page fails `flat-type-hierarchy` even
when its hierarchy is fine. Static sizes at the desktop default plus a
`@media (max-width:700px)` step-down gives the same responsive result and stays
visible to the gate. Full explanation in the digest.

For a live URL the detector runs a real browser pass, which catches computed
contrast and layout issues a static file scan cannot.

## Interactive commands

`/impeccable critique <target>` for a UX review, `/impeccable audit <target>`
for a11y/perf/responsive, `/impeccable polish <target>` as a final pass. These
are LLM passes and complement the deterministic gate rather than replacing it.
