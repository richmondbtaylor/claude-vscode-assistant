---
name: branding-agent
description: Provides Bishop AI's and Prompt Anything's official brand guidelines for any visual content creation or post-processing. Use this skill whenever the user asks about brand colors, brand fonts, brand styling, or whenever they want to create or apply a consistent visual style to any deliverable: infographics, presentations, slides, social media posts, graphics, PDFs, reports, or anything visual. Also trigger when the user says things like "make it on-brand", "apply our brand", "promptAnything styling", "use our colors", "match our brand", or "brand this". Always use this skill as the authoritative brand reference before creating or modifying any visual content. Don't guess at colors or fonts without consulting it.
---

# Bishop AI Brand Guidelines

Source of truth: `bishop-ai-profile/brand/BRAND.md` (human-readable) | `bishop-ai-profile/brand/tokens.json` (machine-readable) | `bishop-ai-profile/brand/brand.css` (CSS properties for HTML content)

---

## Colors

| Token | Hex | Role |
|---|---|---|
| `deep-black` | `#000814` | Primary dark: text on light bg, dark hero sections |
| `dark-charcoal` | `#1E2333` | Secondary dark: cards, nav bars, overlays on dark |
| `gold` | `#E0B848` | Primary accent: highlighted words, CTAs, brush-stroke marks |
| `blue` | `#1894C9` | Secondary accent: links, tags, supporting callouts |
| `light-gray` | `#E6E2DE` | Subtle dividers, secondary light surface |
| `warm-white` | `#F9F6F0` | **Primary background**: default for all light content |
| `near-white` | `#FAFBFA` | Alternate light surface |
| `near-black` | `#101319` | Prompt Anything dark surface / logo-tile background |
| `red` | `#E32E52` | Prompt Anything accent: alerts, emphasis, error states (use sparingly) |

**Background rule:** Light-first. `#F9F6F0` is the default. Dark (`#000814` / `#1E2333`) is intentional: hero sections, inverted callouts: not a default.

**Prompt Anything** shares this palette and typography. Its kit adds `#101319` (near-black tile) and `#E32E52` (red accent); everything else is identical. The one real difference is the logo. See the Prompt Anything logo section below.

**Legacy values to correct on sight:** `#0D1B2A`, `#D4AF37`, `#D4A853`, `#F5F0E8`. These are wrong and must be replaced.

---

## Typography

| Role | Font | Weight |
|---|---|---|
| Title / H1 | Poppins | 900 (Black) |
| Heading / H2 | Poppins | 700 (Bold) |
| Subheading / H3 | Montserrat | 600 (SemiBold) |
| Label / caption | Montserrat | 400, uppercase, letter-spacing 1.5px |
| Body | Open Sans | 400 (Regular) |
| Body strong | Open Sans | 600 (SemiBold) |
| Quote | Open Sans | 400 (Regular) |

**Google Fonts:**
```
https://fonts.googleapis.com/css2?family=Poppins:wght@700;900&family=Montserrat:wght@400;600&family=Open+Sans:wght@400;600&display=swap
```

**Never use Inter as body font**. Legacy error. Body is Open Sans.

---

## Logo

**Variants** (files live in `bishop-ai-profile/assets/logos/`):
- `bishop-ai-logo-horizontal-dark.png`: for light backgrounds
- `bishop-ai-logo-horizontal-white.png`: for dark backgrounds
- `bishop-ai-logo-icon.png`: circular icon only

**Rules:**
- On light bg: dark version, no filter manipulation
- On dark bg: white version as-is
- Minimum width: 120px
- Clear space: equal to chess piece icon height on all four sides
- Never stretch, distort, recolor, or add glow/shadow effects

### Prompt Anything logo (updated 2026)

The Prompt Anything mark is a **feather quill inside a rounded speech bubble**, with the "PROMPT / ANYTHING" wordmark below it. This is a distinct mark from Bishop AI: do not swap one for the other.

**Variants** (files live in `assets/logos/promptanything/`):
- `promptanything-logo-horizontal-dark.png`: full lockup (icon + wordmark), dark ink: for **light** backgrounds
- `promptanything-logo-horizontal-white.png`: full lockup, white: for **dark** backgrounds
- `promptanything-logo-icon-dark.png`: icon only (feather-in-bubble), dark: for **light** backgrounds
- `promptanything-logo-icon-white.png`: icon only, white: for **dark** backgrounds

**Rules:**
- On light bg use the dark variant; on dark bg use the white variant. Never recolor.
- Circular-badge placement: clip the icon to a circle only: no border ring of any color.
- Never stretch, distort, recolor, or add glow/shadow effects.
- Prefer the icon-only variant where the "PROMPT ANYTHING" name already appears nearby; use the full lockup as the standalone brand mark.

### Prompt Anything mascot

A friendly robot character: glossy white round body, black screen face with **yellow eyes** and a **blue accent ring**. Use it as a spot illustration / character for Prompt Anything content (onboarding, empty states, explainers, social). It is a mascot, not a logo: never use it in place of the logo.

**Files** live in `assets/mascots/promptanything/`:
- `mascot-sheet.png`: all 10 poses on one sheet
- Individual poses: `mascot-01-wave`, `-02-fly`, `-03-present`, `-04-happy`, `-05-sleep`, `-06-chart`, `-07-laptop`, `-08-think`, `-09-business`, `-10-celebrate` (`.png`)

**Rules:**
- Match the pose to context: `think` for problem-solving, `celebrate` for success, `sleep` for idle/empty states, `chart`/`laptop` for work, `business` for professional.
- Reads well on light and dark backgrounds (it carries its own rim light). No glow needed behind it.
- Never recolor the body, eyes, or ring; never stretch or distort. Keep the whole character: don't crop off limbs or accessories (lightbulb, Zzz).

---

## Background Rule

Light-first always. `#F9F6F0` is the default surface for every page, slide, and carousel. Dark backgrounds are intentional decisions, not defaults.

---

## Layout and Spacing

- Base unit: 8px
- Page side padding: 48–64px desktop, 24px mobile
- Max content width: 1200px centered
- Section padding: 80–96px vertical
- Card padding: 32–48px
- White space is intentional: it signals confidence

---

## Visual Motifs

- **Brush-stroke highlights:** Key words in headlines get a `#E0B848` soft brush-stroke behind them: described in KIE prompts as "like a hand-painted marker swipe"
- **Grid lines:** Thin structural rule lines dividing sections
- **Arrow marks:** Simple directional → and ↗ as navigation and emphasis cues
- **Dark example cards:** `#1E2333` background with light text for code blocks, comparisons, or callouts

---

## Voice and Messaging

- Lead with the audience's problem or result before introducing Richmond or Bishop AI
- Plain-spoken and practical: make AI feel accessible to non-technical people
- Richmond's background (athlete-to-founder) is credibility context, not the headline
- Confident, results-focused, not hype-focused

**Hard formatting rules:**
- No em dashes anywhere
- Minimal emojis: only when they add meaning, never decorative
- Never frame AI as replacing humans or suggest firing people
- No AI-sounding openers, stacked fragments, hollow filler phrases

---

## Per-Format Specs

| Format | Canvas | Output | Notes |
|---|---|---|---|
| Carousel | 1080 × 1350px (4:5) | JPG | Instagram + LinkedIn. `#F9F6F0` bg. Gold brush-stroke accents. |
| Deck | 1920 × 1080px (16:9) | PDF | Never deliver as HTML. Render per-page at scrollHeight, merge with pypdf. |
| Overlay | 1080 × 1080px (1:1) | PNG | Transparent bg where needed. |
| Thumbnail | 1280 × 720px (16:9) | JPG | High contrast, face + text, strong focal point. |
| HTML proposal/report | Responsive | PDF | Import `bishop-ai-profile/brand/brand.css`. Render to PDF via headless browser. |

---

## KIE AI Prompt Guidance (for carousel and image generation)

KIE does not understand font names: describe visually instead:

| Brand element | KIE prompt language |
|---|---|
| `#F9F6F0` background | "Warm cream off-white background, solid, clean" |
| `#E0B848` gold | "Soft golden-amber brush-stroke highlight behind key words, like a hand-painted marker swipe" |
| `#000814` text | "Ultra-bold deep black sans-serif headline" |
| `#1E2333` card | "Dark navy-charcoal card with cream-white body text" |
| `#1894C9` accent | "Clean sky-blue accent tag or label" |

Never reference font names (Poppins, Montserrat, Open Sans) in KIE prompts: use descriptive terms only.

---

## Pre-flight QA Checklist

Before delivering any content, verify:

- [ ] All colors are from the official palette: no `#0D1B2A`, `#D4AF37`, `#D4A853`, `#F5F0E8`
- [ ] Fonts: Poppins titles, Montserrat subheadings, Open Sans body
- [ ] Background defaults to `#F9F6F0` unless dark is intentional
- [ ] Logo: correct variant for the background, clear space respected
- [ ] Canvas dimensions match the format spec
- [ ] No em dashes in any text
- [ ] No AI-sounding openers, stacked fragments, or hype language
- [ ] AI framed as amplifying people, not replacing them
- [ ] Content leads with audience value before Richmond's personal story


<!-- design-bridge:start -->

## Design bridges: consult before building

Three bridge skills sit under this one. None of them produces deliverables; this
skill still owns the output.

1. **`design-extract`**: MEASURED tokens from one named site, repo, or project.
   When a design system is active it wins on layout, spacing, type scale,
   components, motion and interaction states.
2. **`design-intel`**: RECOMMENDED generic values (layout, spacing, UX,
   accessibility, chart selection, font pairing) where brand and the active
   system are silent.
3. **`design-sources`**: external craft rules plus the deterministic gate. Read
   `C:/Users/richm/.claude/skills/design-sources/references/brand-graphics.md` for this medium.

**Precedence:** explicit instruction in the request > `branding-agent` (colours,
fonts, logo) > active extracted system > style preset (`brutalist-skill`,
`minimalist-skill`) > `design-intel` > skill defaults. Measured beats
recommended where both cover a decision. Borrow ratios and structure from an
extracted system; keep brand colours and typefaces from `branding-agent`.

`design-sources` is a **gate, not a precedence layer**: it runs before shipping
no matter which layer supplied the values.

3. **No gate on image output.** `impeccable detect` parses HTML/CSS/URLs, so there is nothing to scan in a PNG. Do not claim a gate pass on an image. If the graphic is produced by screenshotting HTML, gate that HTML before capture.

**Brand outranks both.** Bishop AI / Prompt Anything / BOB colours and typefaces
come from `branding-agent` and `tokens.json`, never from an external source.
Verified: Bishop AI's own palette trips two Impeccable rules (`cream-palette` on
warm-white `#F9F6F0`, `overused-font` on Open Sans); both are waived in
`C:/Users/richm/.claude/design-sources/brand-overrides/config.json` and reported as overridden
rather than failed. Do not "fix" brand to satisfy a detector.

<!-- design-bridge:end -->
<!-- design-extract:connector v1 -->

---

## Extracted Design System

**First, scan the request for the literal phrase "full <name> system"** (e.g. "full linear
system").

- **Phrase present** -> that extracted system supersedes this skill for this one
  deliverable. Use its colors and font families from `~/.claude/design-systems/<slug>/`.
  State in one line that you did so and why.
- **Phrase absent** -> this skill is the brand authority, and extracted systems sit beneath
  it. Bishop AI / Prompt Anything colors, font families, and logo treatment win over any
  extracted system. An active system may still contribute layout, spacing grid, type scale
  ratios, component patterns, motion, and interaction states: borrowing a 1.25 type scale
  while keeping the Bishop typeface is the intended outcome, not a compromise.

Near-miss phrasings do NOT trigger the override: "use Linear's colors", "make it look like
Linear", "match Linear's branding". Only the literal phrase.

**This skill defines brand values.** When a system is active, read `tokens/` and `DESIGN.md` only to understand what the extracted system offers: never to redefine a Bishop value.

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
<!-- /design-extract:connector v1 -->
