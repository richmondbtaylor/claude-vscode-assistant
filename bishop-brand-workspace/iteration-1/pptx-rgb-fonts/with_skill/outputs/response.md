# Bishop AI Brand Colors and Fonts for python-pptx

## RGBColor Values

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt

# --- Main Colors ---
DEEP_NAVY  = RGBColor(0, 8, 20)       # #000814 — Primary text, dark backgrounds
DARK_NAVY  = RGBColor(30, 35, 51)     # #1E2333 — Dark UI surfaces, secondary backgrounds
OFF_WHITE  = RGBColor(230, 226, 222)  # #E6E2DE — Subtle backgrounds, muted elements
NEAR_WHITE = RGBColor(249, 246, 240)  # #F9F6F0 — Light backgrounds
WHITE      = RGBColor(250, 251, 250)  # #FAFBFA — Light text on dark, clean backgrounds

# --- Accent Colors ---
GOLD       = RGBColor(224, 184, 72)   # #E0B848 — Primary accent: headlines, highlights, CTAs
BLUE       = RGBColor(24, 148, 201)   # #1894C9 — Secondary accent: icons, charts, supporting elements
```

---

## Font Assignments

| Element | Primary Font | Fallback Font |
|---|---|---|
| Headings (H1 / H2, 24pt+) | `"Poppins"` (Bold) | `"Arial"` (Bold) |
| Subheadings / Subtitles / Section Labels | `"Montserrat"` | `"Helvetica"` |
| Body Text / Bullet Lists / Captions / Quotes | `"Open Sans"` | `"Georgia"` |

In python-pptx, assign fonts by setting `run.font.name`:

```python
# Heading
run.font.name = "Poppins"
run.font.bold = True
run.font.size = Pt(36)
run.font.color.rgb = GOLD         # Gold on dark background

# Subheading
run.font.name = "Montserrat"
run.font.size = Pt(20)
run.font.color.rgb = WHITE

# Body text
run.font.name = "Open Sans"
run.font.size = Pt(14)
run.font.color.rgb = OFF_WHITE
```

---

## Key Color Selection Rules for Slides

- Dark backgrounds (Deep Navy / Dark Navy) → use White or Off-White for text
- Light backgrounds (Near White / White) → use Deep Navy for text
- Primary accent (borders, key stats, CTAs, slide title highlights) → Gold
- Secondary accent (chart elements, icons, supporting callouts) → Blue
- Default slide background: Deep Navy (`RGBColor(0, 8, 20)`) for Bishop AI's premium dark-first identity
