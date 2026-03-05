---
name: bishop-brand
description: Provides Bishop AI's official brand guidelines for any visual content creation or post-processing. Use this skill whenever the user asks about brand colors, brand fonts, brand styling, or whenever they want to create or apply a consistent visual style to any deliverable — infographics, presentations, slides, social media posts, graphics, PDFs, reports, or anything visual. Also trigger when the user says things like "make it on-brand", "apply our brand", "Bishop AI styling", "use our colors", "match our brand", or "brand this". Always use this skill as the authoritative brand reference before creating or modifying any visual content for Bishop AI — don't guess at colors or fonts without consulting it.
---

# Bishop AI Brand Guidelines

These are the authoritative brand standards for all Bishop AI visual content. Consult this whenever you're creating, styling, or post-processing anything visual — infographics, presentations, social posts, PDFs, graphics, reports.

---

## Color Palette

### Main Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Deep Navy | `#000814` | rgb(0, 8, 20) | Primary text, dark backgrounds |
| Dark Navy | `#1E2333` | rgb(30, 35, 51) | Dark UI surfaces, secondary backgrounds |
| Off-White | `#E6E2DE` | rgb(230, 226, 222) | Subtle backgrounds, muted elements |
| Near White | `#F9F6F0` | rgb(249, 246, 240) | Light backgrounds |
| White | `#FAFBFA` | rgb(250, 251, 250) | Light text on dark, clean backgrounds |

### Accent Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Gold | `#E0B848` | rgb(224, 184, 72) | Primary accent — headlines, highlights, CTAs |
| Blue | `#1894C9` | rgb(24, 148, 201) | Secondary accent — icons, charts, supporting elements |

### Smart Color Selection Rules

- **Dark background** (Deep Navy, Dark Navy) → use White (`#FAFBFA`) or Off-White (`#E6E2DE`) for text
- **Light background** (Off-White, Near White, White) → use Deep Navy (`#000814`) for text
- **Accent on dark** → Gold (`#E0B848`) stands out best
- **Accent on light** → Blue (`#1894C9`) or Gold both work; prefer Blue for UI/data elements
- **Non-text shapes, icons, chart elements** → cycle through Gold then Blue (never use main colors for decorative shapes)

---

## Typography

### Font Stack

| Role | Primary Font | Fallback |
|------|-------------|---------|
| H1 / H2 Headings (24pt+) | Poppins Bold | Arial Bold |
| Subheadings / Subtitles | Montserrat | Helvetica |
| Body Text / Quotes / Captions | Open Sans | Georgia |

### Application Rules

- **Titles and major headings** (the biggest, most prominent text) → Poppins Bold
- **Section labels, subtitles, callout headers** → Montserrat (regular or SemiBold)
- **Paragraph text, bullet lists, pull quotes, captions** → Open Sans (regular or Light)
- Never mix more than these three font families in a single piece
- Fonts should be pre-installed in the environment; if unavailable, use the fallback — readability takes priority over perfection

---

## How to Apply This to Visual Deliverables

### In Prompts for AI Image Generation (e.g., infographic-generator)

When passing brand context into an image generation prompt, include a section like:

```
BRAND STYLE — Bishop AI:
Background: Deep Navy (#000814) or Dark Navy (#1E2333)
Primary text: White (#FAFBFA) or Off-White (#E6E2DE)
Accent colors: Gold (#E0B848) as primary, Blue (#1894C9) as secondary
Typography: Poppins Bold for titles, Montserrat for subheadings, Open Sans for body
Shapes and icons: Gold and Blue accents only — no other colors
Overall feel: Premium, dark, corporate-tech, clean
```

### In python-pptx / Code-Based Rendering

Use `RGBColor` with the exact values:

```python
from pptx.util import Pt
from pptx.dml.color import RGBColor

DEEP_NAVY   = RGBColor(0, 8, 20)
DARK_NAVY   = RGBColor(30, 35, 51)
OFF_WHITE   = RGBColor(230, 226, 222)
NEAR_WHITE  = RGBColor(249, 246, 240)
WHITE       = RGBColor(250, 251, 250)
GOLD        = RGBColor(224, 184, 72)
BLUE        = RGBColor(24, 148, 201)

# Font assignment by element type:
# Heading (>=24pt)  → "Poppins" (fallback: "Arial")
# Subheading        → "Montserrat" (fallback: "Helvetica")
# Body / Quotes     → "Open Sans" (fallback: "Georgia")
```

### For Any Visual Deliverable (General Guidance)

1. Set the background first — default to Deep Navy for premium/dramatic, Near White for clean/minimal
2. Apply text color based on background (smart selection rules above)
3. Use Gold as the first accent (borders, highlights, key stats, CTAs)
4. Use Blue as the second accent (secondary charts, icons, supporting callouts)
5. Apply typography hierarchy: Poppins → Montserrat → Open Sans, top to bottom
6. Avoid adding other colors — the palette is intentionally minimal and high-contrast

---

## Brand Voice in Visuals

- **Premium and precise** — no clutter, no gradients that fight the palette
- **Dark-first default** — Bishop AI's visual identity leans dark; use light backgrounds sparingly
- **Gold as the hero accent** — it signals authority and trust; use it on the most important element
- **Clean hierarchy** — let the typography do the work; don't rely on color chaos to create interest
