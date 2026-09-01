# Adapter: decks, reports, course pages, email

Owner skills: `slideforge`, `prestige`, `pitch-deck-architect`, `course-builder`,
`ai-audit`, `ops-audit`, `lead-audit-walkthrough`, `handout-builder`,
`homework-builder`, `email-html-gen`, `certification-one-pager`,
`service-agreement`, `invoice-generator`.

These render through HTML even when the artifact ships as PDF or as a
screenshotted slide, so the **gate applies and is blocking**. Run it on the HTML
before the PDF or PNG step, because a defect baked into a PDF is far more
expensive to find.

## Mode

Almost everything here is **Read** (the viewer is trying to understand) or
**Persuade** (an audit or deck that has to land a conclusion). Structure for
comprehension first, then make it worth staying in. Operate rules do not apply;
these are not tools.

## What transfers directly

- Contrast, spacing rhythm, type scale, line length 65–75ch, tight leading and
  `tiny-text` limits. Report body copy is read at length, so measure and leading
  matter more here than anywhere else.
- **More space above a heading than below it.** The single most common defect in
  generated report HTML.
- Real content at real length. Audit reports overflow with long client names and
  long findings; run the actual copy, not lorem.
- Elevation declared once. Report cards under both a border and a wide shadow is
  the ghost-card tell.

## What to ignore from the digest

- Hover/loading/empty states: a printed report has none. Keep error and empty
  states only where the page is genuinely interactive (the lead audit
  walkthrough, the course hub).
- Motion guidance: irrelevant to a PDF. Applies to `course-builder` and
  `lead-audit-walkthrough`, which ship as live HTML.

## Bishop AI collateral

The editorial one-pager style at `bishop-ai-profile/brand/COLLATERAL-STYLE.md` is
**locked** and outranks every Impeccable layout opinion. Do not restructure a
one-pager because a generic rule prefers a different hierarchy.

Rich's rule that presentations ship as **PDF, never HTML** stands. Render each
HTML page at its own scrollHeight and merge with pypdf.

Expect and ignore `cream-palette` / `overused-font` on Bishop work, waived by
the brand overrides, reported as overridden rather than failed.

## Charts

Impeccable has little to say about charts. Use `design-intel` for chart type
selection and accessible fallbacks, and keep the rule that a chart never relies
on colour alone.

## Gate

```bash
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <the .html> 
```

Run on the HTML **before** PDF export or slide screenshotting. Blocking.

**Set the type scale with media queries, not `clamp()`.** The static scan cannot
resolve `clamp()`, so clamped headings drop out of the sample and the page fails
`flat-type-hierarchy` even when its hierarchy is fine. Static sizes plus a
`@media` step-down reads identically and stays visible to the gate. Full
explanation in the digest.
