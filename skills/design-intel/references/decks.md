# Deck, report and email lookups

Owner skills: `slideforge`, `prestige`, `pitch-deck-architect`, `course-builder`,
`email-html-gen`, `ai-audit`, `ops-audit`, `lead-audit-walkthrough`,
`handout-builder`, `homework-builder`. They build. This file tells you what to
look up first.

Set `S` per the SKILL.md resolution block before running anything.

## Slides and presentation structure

```bash
python "$S" "presentation slide layout hierarchy" -n 3
python "$S" "type scale modular hierarchy" --domain typography -n 3
```

A slide is read at distance and a report at reading distance. Query the scale
question explicitly rather than reusing a web ramp for both.

Rich's rule: presentations ship as **PDF, never HTML** as the final artifact.
Render each HTML page at its own scrollHeight and merge with pypdf.

## Long-form reports and audits

The audit deliverables are the longest-form thing Rich ships, so measure and
leading matter more here than anywhere else.

```bash
python "$S" "long form reading measure line length" --domain typography -n 3
python "$S" "data table dense readable" -n 3
python "$S" "section hierarchy scannable document" --domain style -n 3
```

Body measure 65–75ch. More space above a heading than below it. Run the real
client copy, not lorem: real client names and real findings are what overflow.

## Charts in reports

```bash
python "$S" "show change over time" --domain chart -n 3
python "$S" "ranking comparison categories" --domain chart -n 3
python "$S" "compare parts of a whole" --domain chart -n 3
```

Take the type selection and the accessible fallback. On Bishop AI work the chart
palette comes from brand, not the database. Never rely on colour alone.

## Email

```bash
python "$S" "email newsletter responsive layout" -n 3
```

Email is the most constrained medium here: table layout, inline styles, no
modern CSS. Treat generic web results with suspicion and verify anything before
applying it. Client support, not elegance, decides.

## Course pages and interactive walkthroughs

`course-builder` and `lead-audit-walkthrough` ship as live HTML, so the full web
ruleset applies. Use `references/web.md` for those instead of this file, and run
the design gate.

```bash
python "$S" "focus not obscured" --domain ux -n 3
python "$S" "error summary validation" --domain ux -n 3
```

## Locked style

The Bishop AI editorial one-pager style at
`bishop-ai-profile/brand/COLLATERAL-STYLE.md` governs all Bishop collateral and
outranks any database layout result. Roadmap milestone names are locked:
Foundation / Quick Wins / Reactive to Proactive / Scale Unlock.

## Cross-check against design-sources

Read `design-sources/references/deck-doc.md` before building, and **run the gate
on the HTML before the PDF or screenshot step**. A defect baked into a PDF is far
more expensive to find than one caught in the HTML.

## Before handing off

- Measure and leading checked against real copy at real length
- Chart types selected from the database, palette from brand
- Milestone names correct where they appear
- No em dashes anywhere
- Gate run on the HTML before export
- Run the SKILL.md pre-delivery check
