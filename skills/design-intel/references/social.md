# Social graphic lookups

Owner skills: `citadel` (thumbnails), `carousel`, `infographic-generator`,
`reel-cover`. They generate the images. This file tells you what to look up first.

Set `S` per the SKILL.md resolution block before running anything.

## What the database is good for here

These skills output PNG/JPG through image generation, so most web-oriented
results do not apply. Query for **composition, hierarchy and legibility**, not
implementation.

```bash
python "$S" "social media thumbnail composition" -n 3
python "$S" "visual hierarchy" --domain ux -n 3
python "$S" "type scale modular hierarchy" --domain typography -n 3
```

## Charts inside infographics

This is the one place the database is clearly authoritative, and `infographic-generator`
should always consult it before picking a form.

```bash
python "$S" "compare parts of a whole" --domain chart -n 3
python "$S" "show change over time" --domain chart -n 3
python "$S" "ranking comparison categories" --domain chart -n 3
```

25 chart types indexed. Take the **type selection and the accessible fallback**.
Take the palette only on unbranded work. A chart must never rely on colour alone
to carry meaning.

## Legibility at delivery size

A thumbnail is read at phone size, a carousel slide at roughly a third of a
screen. Contrast rules are *less* forgiving here than on a webpage, not more.

```bash
python "$S" "text over image legibility contrast" --domain ux -n 3
```

Minimum ≥4.5:1 for anything at body size and ≥3:1 for large display type still
applies, measured against the actual background region the type sits on, not the
average of the image.

## Rich's locked rules: these outrank every result

The database does not know these. They win.

- Carousels: square 1:1, seamless panorama mode by default, no word-labels or
  domains, hard-edge headshot never cut off, LinkedIn PDF with every deck
- Thumbnails: subject fully in frame, bottom waist crop only
- Never reuse a headshot pose; use the pose ledger
- Carousel faces come from generated avatar headshots, never raw webcam frames
- Brand colours and faces from `tokens.json`, never from the database
- No emoji as icons; drawn SVG only

## Cross-check against design-sources

Read `design-sources/references/brand-graphics.md` before generating. Its refuse
list transfers directly to image work: no kicker above the headline, no gradient
text, no purple-to-blue gradients, no icon-tile stack, no same-size card grid as
the structure of a carousel.

Note that the design **gate does not run** on image output. If the graphic is
produced by screenshotting HTML, gate that HTML before capture.

## Before handing off

- Composition justified per slide, not repeated
- Contrast checked against the actual region behind the type
- Chart type selected from the database, not by habit
- Brand lock held
- No em dashes anywhere
- Run the SKILL.md pre-delivery check
