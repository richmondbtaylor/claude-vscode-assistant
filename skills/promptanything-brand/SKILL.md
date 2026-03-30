---
name: promptanything-brand
description: Provides promptAnything.io's official brand guidelines for any visual content creation or post-processing. Use this skill whenever the user asks about promptAnything brand colors, fonts, styling, or whenever they want to create or apply a consistent visual style to any deliverable for the promptAnything.io brand — infographics, presentations, slides, social posts, graphics, PDFs, reports, or anything visual. Also trigger when the user says "make it on-brand for promptAnything", "apply the PA brand", "promptAnything styling", or "brand this for PromptAnything". Always use this skill as the authoritative reference before creating or modifying any visual content for promptAnything.io — don't guess at colors or fonts without consulting it.
---

# promptAnything.io Brand Guidelines

These are the authoritative brand standards for all promptAnything.io visual content. Consult this whenever you're creating, styling, or post-processing anything visual — infographics, presentations, social posts, PDFs, graphics, reports.

Source: Extracted from the 2026 promptAnything.io Pitch Deck.

---

## Color Palette

### Main Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Deep Navy | `#000813` | rgb(0, 8, 19) | Primary background, dark slide backgrounds |
| Dark Navy | `#1D2333` | rgb(29, 35, 51) | Secondary backgrounds, card surfaces |
| Off-White | `#E6E2DE` | rgb(230, 226, 222) | Body text, muted elements, captions |
| White | `#FAFBFA` | rgb(250, 251, 250) | Primary text on dark backgrounds, headlines |

### Accent Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Gold | `#E0B848` | rgb(224, 184, 72) | Primary accent — logo, headlines, CTAs, highlights |
| Blue | `#1894C9` | rgb(24, 148, 201) | Secondary accent — results, positive outcomes, icons |
| Red/Coral | `#E05252` | rgb(224, 82, 82) | Contrast/problem accent — "The Problem", negative comparisons, before states |

### Smart Color Selection Rules

- **Dark background** (Deep Navy, Dark Navy) → use White (`#FAFBFA`) for headings, Off-White (`#E6E2DE`) for body
- **Accent on dark** → Gold (`#E0B848`) for primary highlights; Blue for outcomes/results; Red/Coral for problems/contrast
- **"Before vs. After" framing** → Red/Coral marks the "before" (problem), Gold marks the "after" (solution)
- **Non-text shapes, icons** → Gold first, then Blue or Red/Coral based on context
- **Never use Red/Coral for CTAs or positive elements** — it signals friction or problem, not action

---

## Typography

### Font Stack

| Role | Font | Weight | Use |
|------|------|--------|-----|
| H1 / Hero Headings (24pt+) | Poppins | ExtraBold | Large headline statements, cover slide headlines |
| H2 / Subheadings | Poppins | Bold | Section titles, slide headings |
| Labels / Eyebrows / Callouts | Poppins or Montserrat | SemiBold or Regular | "THE PROBLEM", stat labels, step numbers |
| Body / Captions | Open Sans | Regular or Light | Paragraph text, bullet lists, supporting copy |

### Application Rules

- Poppins is the primary typeface — use across all heading levels (ExtraBold for hero, Bold for subheads)
- Open Sans for any running body text
- Never use more than these two typeface families in a single piece
- Step numbers and large stat callouts → Poppins ExtraBold at large sizes with Gold color

---

## Logo

### promptAnything.io Wordmark

- Rendered in **Poppins ExtraBold**, Gold (`#E0B848`)
- Lowercase `p`, camelCase `A` in `Anything` — match the exact casing: `promptAnything.io`
- Logo files (once uploaded): `~/.claude/assets/logos/promptanything/`
- On dark backgrounds: use Gold wordmark
- On light backgrounds: use Deep Navy wordmark

### Usage Rules

- Never stretch, skew, or recolor the wordmark
- Minimum clear space: equal to the height of the `p` on all sides
- Preferred pairing: wordmark + separator bar + tagline "PROMPT ENGINEERING · SIMPLIFIED" in small caps Off-White

---

## How to Apply This to Visual Deliverables

### In Prompts for AI Image Generation

```
BRAND STYLE — promptAnything.io:
Background: Deep Navy (#000813) or Dark Navy (#1D2333)
Primary text: White (#FAFBFA) or Off-White (#E6E2DE)
Accent colors: Gold (#E0B848) as primary, Blue (#1894C9) for positive/result elements, Red/Coral (#E05252) for problem/contrast elements only
Typography: Poppins ExtraBold for hero titles, Poppins Bold for subheadings, Open Sans for body
Logo: "promptAnything.io" wordmark in Gold, Poppins ExtraBold
Overall feel: Dark, premium, direct, no-nonsense — confident problem-solver energy
```

### In python-pptx / Code-Based Rendering

```python
from pptx.util import Pt
from pptx.dml.color import RGBColor

DEEP_NAVY   = RGBColor(0, 8, 19)
DARK_NAVY   = RGBColor(29, 35, 51)
OFF_WHITE   = RGBColor(230, 226, 222)
WHITE       = RGBColor(250, 251, 250)
GOLD        = RGBColor(224, 184, 72)
BLUE        = RGBColor(24, 148, 201)
RED_CORAL   = RGBColor(224, 82, 82)

# Font assignment:
# Hero headings (>=24pt)   → "Poppins" weight ExtraBold (fallback: "Arial Black")
# Subheadings              → "Poppins" weight Bold (fallback: "Arial Bold")
# Body / Captions          → "Open Sans" (fallback: "Georgia")
```

### For Any Visual Deliverable (General Guidance)

1. Background first — default to Deep Navy for dark/premium
2. Headlines in White (`#FAFBFA`), Poppins ExtraBold
3. Primary accent is Gold — use on the most important stat, CTA, or logo element
4. Use Red/Coral only for contrast/problem framing — never on CTAs or positive claims
5. Use Blue for outcome/result/positive secondary elements
6. Keep layout clean and high-contrast — this brand leads with directness, not decoration

---

## Brand Voice in Visuals

- **Direct and declarative** — headlines are statements, not questions
- **Problem-first framing** — establish the problem clearly before the solution
- **Data-backed** — lead with numbers when possible (11×, 73M+, $390B)
- **Confident, not boastful** — the copy earns authority through specificity, not adjectives
- Dark-first aesthetic — same visual identity family as Bishop AI, built for premium digital contexts

---

## Relationship to Bishop AI Brand

promptAnything.io is a sister brand under Rich Taylor's portfolio. The two brands share:
- Same core color palette (Deep Navy, Dark Navy, Off-White, Gold, Blue)
- Same font system (Poppins headings, Open Sans body)
- Same "dark-first, gold-accent" visual identity

**Key difference:** promptAnything adds Red/Coral (`#E05252`) as a problem/contrast accent. Bishop AI does not use this color.

See also: `~/.claude/skills/bishop-brand/SKILL.md`

---

## Language & Copy Standards

Copy in or accompanying any promptAnything.io visual must be direct, specific, and plain-spoken.

Never use: game-changer, transformative, cutting-edge, seamless, revolutionize, innovative, robust, scalable (as vague praise), synergy, thought leader, pain points, humbled and honored, in today's digital landscape, delve into, holistic, empower, utilize, unprecedented, groundbreaking.

**The standard:** Numbers beat adjectives. "11 rewrites before abandonment" beats "frustrating prompt engineering experience."
