# Web and code design lookups

Owner skills: `visual-code`, `image-to-code`, `imagegen-frontend-web`,
`website-to-hyperframes`. They build. This file tells you what to look up first.

Set `S` per the SKILL.md resolution block before running anything.

## New site or landing page: start with the design system

One call returns pattern, style, colours, typography, effects, and anti-patterns
in one aggregate. Run it before writing any markup.

```bash
python "$S" "b2b saas automation consulting professional" --design-system -p "Bishop AI"
```

Swap the query for the actual product. Two to five terms: product type, industry,
audience, and a style keyword.

**Apply the pattern, layout, effects, and anti-patterns. Discard the palette and
font pairing on Bishop AI work**. `branding-agent` owns those. On client work
with no brand yet, the palette is usable as a starting point.

`--persist` writes the system to disk for reuse across sessions. If you use it,
always pass `--output-dir` pointed at the project root, or files land wherever
the tool happened to run.

## Section and page structure

```bash
python "$S" "landing page hero conversion above fold" --domain landing -n 3
python "$S" "pricing table comparison tiers" --domain landing -n 3
python "$S" "social proof testimonial placement" --domain landing -n 3
```

`imagegen-frontend-web` requires one image per section and enforces composition
variety. Query `landing` per section so each one gets a distinct, justified
structure rather than repeating left-text / right-image.

## Stack-specific implementation

Detect the stack before querying. Check `package.json` deps, `pubspec.yaml`
(Flutter), `*.xcodeproj` or `Package.swift` (SwiftUI), `composer.json` (Laravel).
**Never assume a stack**. A wrong guess misroutes every recommendation.

Rich's single-file HTML output is `html-tailwind`:

```bash
python "$S" "responsive grid card layout" --stack html-tailwind -n 3
python "$S" "navigation header" --stack html-tailwind -n 3
```

For `website-to-hyperframes` and any GSAP work:

```bash
python "$S" "staggered reveal on scroll" --domain gsap -n 3
python "$S" "page transition continuity" --domain gsap -n 3
```

17 GSAP presets are indexed. Prefer a preset over hand-rolled timing. Cross-check
against the `gsap` skill for the API surface.

## UX and accessibility

Query one observable outcome at a time, using outcome words rather than component
names:

```bash
python "$S" "focus not obscured" --domain ux -n 3
python "$S" "error summary validation" --domain ux -n 3
python "$S" "orphan heading line balance" --domain ux -n 3
python "$S" "accessible authentication" --domain ux -n 3
```

Then, only if needed, a component or stack query for implementation:

```bash
python "$S" "icon button accessible label" --domain icons -n 3
python "$S" "chip badge overflow nowrap" --stack html-tailwind -n 3
```

Do not accept a generic accessibility result for a specific WCAG criterion or
interaction. Narrow the query instead.

## Icons

105 curated icons indexed, Phosphor upstream.

```bash
python "$S" "decorative icon aria hidden" --domain icons -n 3
```

SVG only. Emoji as icons is a listed anti-pattern and breaks Rich's rules too.

## Before handing off

- Stack confirmed by inspection, not assumed
- Every section has a distinct, justified structure
- Brand lock held: no database hex, no database font on Bishop AI work
- Light background unless there is a stated reason otherwise
- No em dashes anywhere in the copy
- Run the SKILL.md pre-delivery check
