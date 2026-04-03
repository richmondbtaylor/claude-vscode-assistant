---
name: branding-agent
description: Provides Bishop AI's official brand guidelines for any visual content creation or post-processing. Use this skill whenever the user asks about brand colors, brand fonts, brand styling, or whenever they want to create or apply a consistent visual style to any deliverable — infographics, presentations, slides, social media posts, graphics, PDFs, reports, or anything visual. Also trigger when the user says things like "make it on-brand", "apply our brand", "promptAnything styling", "use our colors", "match our brand", or "brand this". Always use this skill as the authoritative brand reference before creating or modifying any visual content — don't guess at colors or fonts without consulting it.
---

# Bishop AI Brand Guidelines

These are the authoritative brand standards for all Bishop AI visual content. Consult this whenever you're creating, styling, or post-processing anything visual — infographics, presentations, social posts, PDFs, graphics, reports.

Source: Extracted from the 2026 Bishop AI Pitch Deck.

---

## Color Palette

### Main Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| White | `#FAFBFA` | rgb(250, 251, 250) | Primary background, light slide backgrounds |
| Off-White | `#E6E2DE` | rgb(230, 226, 222) | Secondary backgrounds, card surfaces |
| Dark Navy | `#1D2333` | rgb(29, 35, 51) | Body text, muted elements, captions |
| Deep Navy | `#000813` | rgb(0, 8, 19) | Primary text on light backgrounds, headlines |

### Accent Colors

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Gold | `#E0B848` | rgb(224, 184, 72) | Primary accent — headlines, CTAs, highlights |
| Blue | `#1894C9` | rgb(24, 148, 201) | Secondary accent — results, positive outcomes, icons |
| Red/Coral | `#E05252` | rgb(224, 82, 82) | Contrast/problem accent — "The Problem", negative comparisons, before states |

### Smart Color Selection Rules

- **Light background** (White, Off-White) → use Deep Navy (`#000813`) for headings, Dark Navy (`#1D2333`) for body
- **Accent on light** → Gold (`#E0B848`) for primary highlights; Blue for outcomes/results; Red/Coral for problems/contrast
- **"Before vs. After" framing** → Red/Coral marks the "before" (problem), Gold marks the "after" (solution)
- **Non-text shapes, icons** → Gold first, then Blue or Red/Coral based on context
- **Never use Red/Coral for CTAs or positive elements** — it signals friction or problem, not action

---

## Typography

### Font Stack

| Role | Font | Weight | Use |
|------|------|--------|-----|
| H1 / Primary Titles (24pt+) | Poppins | ExtraBold | Large headline statements, cover slide headlines |
| H2 / Subtitles / Subheadings | Montserrat | Bold or SemiBold | Section titles, slide headings, subtitles |
| Labels / Eyebrows / Callouts | Montserrat | SemiBold or Regular | "THE PROBLEM", stat labels, step numbers |
| Body / Captions / Smaller Text | Open Sans | Regular or Light | Paragraph text, bullet lists, supporting copy |

### Application Rules

- Poppins is the primary title typeface — use for H1 / hero headings only (ExtraBold)
- Montserrat is the subtitle typeface — use for H2 / subheadings, labels, and callouts
- Open Sans for all smaller body text, captions, and running copy
- Never use more than these three typeface families in a single piece
- Step numbers and large stat callouts → Poppins ExtraBold at large sizes with Gold color

---

## How to Apply This to Visual Deliverables

### In Prompts for AI Image Generation

```
BRAND STYLE — Bishop AI:
Background: White (#FAFBFA) or Off-White (#E6E2DE)
Primary text: Deep Navy (#000813) or Dark Navy (#1D2333)
Accent colors: Gold (#E0B848) as primary, Blue (#1894C9) for positive/result elements, Red/Coral (#E05252) for problem/contrast elements only
Typography: Poppins ExtraBold for primary titles, Montserrat Bold for subtitles/subheadings, Open Sans for body
Overall feel: Light, premium, direct, no-nonsense — confident problem-solver energy
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
# Primary titles (>=24pt)  → "Poppins" weight ExtraBold (fallback: "Arial Black")
# Subtitles / Subheadings  → "Montserrat" weight Bold or SemiBold (fallback: "Arial Bold")
# Body / Captions          → "Open Sans" (fallback: "Georgia")
```

### For Any Visual Deliverable (General Guidance)

1. Background first — default to White (`#FAFBFA`) or Off-White (`#E6E2DE`) for light/premium
2. Primary titles in Deep Navy (`#000813`), Poppins ExtraBold; subtitles in Montserrat Bold
3. Primary accent is Gold — use on the most important stat, CTA, or highlight
4. Use Red/Coral only for contrast/problem framing — never on CTAs or positive claims
5. Use Blue for outcome/result/positive secondary elements
6. Keep layout clean and high-contrast — this brand leads with directness, not decoration

---

## Brand Voice in Visuals

- **Direct and declarative** — headlines are statements, not questions
- **Problem-first framing** — establish the problem clearly before the solution
- **Data-backed** — lead with numbers when possible (11×, 73M+, $390B)
- **Confident, not boastful** — the copy earns authority through specificity, not adjectives
- Light-first aesthetic — premium, clean, built for high-contrast digital contexts

---

## Language & Copy Standards

Copy in or accompanying any promptAnything.io visual must be direct, specific, and plain-spoken.

Never use: game-changer, transformative, cutting-edge, seamless, revolutionize, innovative, robust, scalable (as vague praise), synergy, thought leader, pain points, humbled and honored, in today's digital landscape, delve into, holistic, empower, utilize, unprecedented, groundbreaking.

**The standard:** Numbers beat adjectives. "11 rewrites before abandonment" beats "frustrating prompt engineering experience."

---

## Color System Design Protocol

When asked to analyze, optimize, or apply the color palette, act as a senior brand designer and UI/UX color strategist. The goal is clarity, consistency, and usability across web, product UI, marketing assets, and dashboards.

### Design Principles

* The brand should feel modern, technical, trustworthy, and minimal.
* Lighter colors must be used as the PRIMARY visual foundation.
* Darker colors should support contrast, hierarchy, and readability.
* Accent colors should be intentional and used sparingly.

### Extended Color Palette (HEX Reference)

#### Light Neutral / Background Candidates

| Name | Hex | Use |
|------|-----|-----|
| Light Gray | `#E5E5E5` | Neutral background surface |
| Warm Light Beige | `#D9D6CF` | Warm neutral surface |
| Soft Neutral Gray | `#CFCFD1` | Soft neutral surface |

#### Brand / Supporting Colors

| Name | Hex | Use |
|------|-----|-----|
| Light Blue | `#4FB0D8` | Supporting brand blue |
| Teal Blue | `#2A8FB3` | Primary brand blue |
| Gold | `#D4AF37` | Brand gold accent |

#### Dark / Contrast Colors

| Name | Hex | Use |
|------|-----|-----|
| Navy | `#1F2A3A` | Dark UI surfaces, contrast |
| Dark Navy | `#202636` | Secondary dark surfaces |
| Deep Navy | `#0B0F19` | Deep background, almost black |
| Midnight Blue | `#020A14` | Darkest background option |

#### Accent Color

| Name | Hex | Use |
|------|-----|-----|
| Red / Attention | `#E52B4A` | Alerts, errors, urgent CTAs |

### Color System Structure

When reorganizing or applying the palette, define these layers:

#### 1. PRIMARY COLORS
Use lighter tones as the visual foundation. These should dominate backgrounds, sections, and UI surfaces.

#### 2. SECONDARY COLORS
Used for components, cards, panels, and supporting UI elements.

#### 3. ACCENT COLORS
Used for calls to action, highlights, notifications, and key interactions.

#### 4. TEXT COLORS
Define:
* Primary text color
* Secondary text color
* Muted text color
* Inverse text color

#### 5. BACKGROUND SYSTEM
Define:
* Main background
* Section background
* Card background
* Hover / subtle surface color

#### 6. INTERFACE STATES
Assign colors for:
* Hover
* Active
* Disabled
* Success
* Warning
* Error
* Info

#### 7. ACCESSIBILITY
Ensure all major text/background combinations meet WCAG contrast standards.

#### 8. USAGE RULES
Provide short, practical rules:
* When to use light vs dark
* When to use accent colors
* Maximum number of colors per screen
* What colors should never be paired

### Output Format for Color System Deliverables

Return the final result as a structured design system with:
* Clear color roles
* HEX codes
* Short usage descriptions
* Logical hierarchy
* Consistent naming

**Do not redesign the colors. Do not invent new colors unless absolutely necessary. Focus on clarity, balance, and real-world usability.**
