---
name: infographic-generator
description: Generates professional infographic images using the PRISM Framework and KIE AI pipeline. Use this skill whenever the user wants to create an infographic, data visualization, stats graphic, visual explainer, marketing graphic, educational diagram, or any image that presents information visually. Trigger even if the user just says "make a graphic about X", "show this data visually", "I need a visual for my presentation", or "design something that shows my stats." This skill handles everything from prompt construction to image download — always use it for infographic-type requests, don't try to handle them without it.
---

# Infographic Generator (PRISM + KIE AI)

Full workflow: gather requirements → construct PRISM-optimized prompt → execute KIE AI pipeline → save outputs.

## Tier Selection (decide first)

**Tier 1 — Dense Narrative** (default): Single infographic, fast results, best visual quality.

**Tier 2 — Structured JSON**: Multiple variants/A/B testing, multi-panel layouts, batch runs. Use when user says "try different versions" or needs precise iteration control.

---

## Step 1: Gather Requirements

Confirm these before building the prompt. If not provided, make reasonable assumptions and state them.

| Requirement | Default |
|-------------|---------|
| Topic & data | (required — ask if missing) |
| Style | Bishop AI brand — modern minimalist: warm-white `#F9F6F0` background, deep-black `#000814` headlines, dark-charcoal `#1E2333` cards/body, gold `#E0B848` accents and brush-stroke highlights, max 2 elements per section, generous negative space |
| Aspect ratio | `9:16` (social/mobile) |
| Platform | Instagram/LinkedIn |
| Resolution | `2K` |

---

## Step 2: Build the Prompt (Tier 1 — Dense Narrative)

Save a JSON file with this structure:

```json
{
  "task": "infographic_generation",
  "schema_version": "prism-2.0",
  "model_target": "nano-banana-2",
  "prompt": "<dense narrative — see template below>",
  "api_parameters": {
    "aspect_ratio": "9:16",
    "resolution": "2K",
    "output_format": "jpg"
  }
}
```

### Layout Archetypes

Pick the archetype that matches the content type before writing the prompt. This determines the layout structure.

**Archetype A — Hero Stat**: Single metric or bold claim. Full canvas = one big number/statement + subline + CTA. Nothing else. Use for hook cards, key stats, quotes.

**Archetype B — Module List**: Courses, frameworks, roadmaps with 4–8 items. Structure:
- Hero headline (top 15% of canvas)
- Compact stat strip (optional, narrow row)
- Module rows: each is a full-width dark-charcoal `#1E2333` card, gold number badge left, white module title in Poppins Bold, ONE subline in Open Sans — no bullet lists inside cards
- CTA strip (bottom 10%)

**Archetype C — Data Grid**: Stats, comparisons, before/after. 2–3 column grid of large-number cards on warm-white background. Each card: one big number + short label only.

---

### Prompt Narrative Template

Write the `prompt` value as a single dense string following this structure:

```
Professional infographic titled "[TITLE]". Bishop AI brand: modern minimalist, warm-white #F9F6F0 background, premium editorial feel, maximum negative space.
Layout [Archetype X]: [describe top to bottom — each section has ONE clear message, maximum 2 elements per section, generous padding between sections — approximately 5% canvas height between each block].
Color palette: Warm-white #F9F6F0 background, Deep Black #000814 for primary headlines, Dark Charcoal #1E2333 for cards and body text, Gold #E0B848 for accents and brush-stroke highlights on key words, Blue #1894C9 for supporting callouts, Light Gray #E6E2DE for 1px dividers. Dark Charcoal #1E2333 cards with white #FFFFFF text inside — this is the signature contrast element.
Typography: Poppins weight 900 (Black) for H1 at 72pt minimum, Poppins weight 700 (Bold) for H2/module titles, Montserrat SemiBold for subheadings and labels (11px uppercase letter-spaced), Open Sans Regular for body copy at 16pt — never more than 1 line of body copy per card.
Visual motifs: Gold brush-stroke highlight mark behind [key word or stat] — hand-painted marker swipe effect in #E0B848 behind the most important word in the headline. Thin 1px #E6E2DE horizontal rule lines as section dividers. Simple Gold → arrow marks for emphasis only. Dark charcoal #1E2333 full-width cards with white text for all module/list rows.
Data content: [EXACT DATA — verbatim numbers only. Each stat: big number in Poppins Black + 2–4 word Montserrat label. Nothing else on that element].
Visual constraints: no icons, no gradients, no shadows, no decorative borders, no textures, no background patterns. Whitespace IS the design.
Quality directive: ultra-sharp print-quality render, pixel-perfect text alignment, every character perfectly legible, zero garbled or blurry text.
Negative: busy background, alternating light row stripes, bullet lists inside cards, more than 6 words per card subline, more than 2 elements per section, photorealistic photography, blurry text, garbled typography, gradients, drop shadows, decorative icons, more than 3 colors in any single section, stock photo aesthetic, bokeh, lens flare, beauty filters, clutter.
```

### Why these details matter

- **Text legibility is the #1 failure mode** in AI-generated infographics. Specifying font sizes and demanding "perfectly legible" forces the model to treat typography as a hard constraint, not an afterthought.
- **Exact data values must be verbatim** — paraphrasing numbers causes the model to hallucinate different values.
- **Hex color codes** prevent vague "professional blue" interpretations that produce inconsistent results.
- **Top-to-bottom layout description** works because the model reads spatial instructions sequentially — it builds the infographic the way you describe it.
- The **negative blocklist** at the end of the positive prompt (not in a separate field) works better for the KIE API than a separate negative_prompt field.

---

## Step 3: Save the Prompt

```
<project_root>/prompts/infographics/<descriptive-filename>.json
```

Use a specific filename (e.g., `ai-adoption-2020-2024.json`, `q4-sales-funnel.json`).

---

## Step 4: Execute the Pipeline

```powershell
python .\scripts\generate_kie.py .\prompts\infographics\<filename>.json .\images\infographics\<output-name>.jpg "<aspect_ratio>"
```

The script handles API submission, polling (every 4s, up to 4 minutes), and image download automatically.

**Prerequisites:**
- `.env` in project root: `KIE_API_KEY=27e396fd4b9124bf9e802d0178bee73a`
- `scripts/generate_kie.py` present in project

---

## Step 4b: Upload to Google Drive (always run after Step 4)

After the image downloads successfully, immediately run:

```powershell
python .\scripts\upload_gdrive.py .\images\infographics\<output-name>.jpg
```

- Always uploads to folder ID `1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ` (hardcoded — no folder arg needed)
- Token is saved at `scripts/gdrive_token.pickle` — fully automatic after first auth
- Print the Drive share link in the output

---

## Step 5: Report Back

Tell the user:
- Output file path (local)
- Google Drive link (for mobile access)
- Prompt file path (so they can iterate)
- Any assumptions made about style/layout
- Suggested next steps if they want variations

---

## Tier 2: Batch / A/B Testing

For multiple variants, create one JSON file per variant and run generate_kie.py for each in parallel using the Agent tool. Name variants clearly:

```
prompts/infographics/ai-adoption-v1-minimal.json
prompts/infographics/ai-adoption-v2-bold.json
```

Each file uses the same base schema but with different prompt narratives. Output to:
```
images/infographics/ai-adoption-v1-minimal.jpg
images/infographics/ai-adoption-v2-bold.jpg
```

---

## Style Reference

| Style | Colors | Typography | Best For |
|-------|--------|------------|----------|
| Corporate/Minimal | Neutrals + 1-2 accents | Clean sans-serif, generous whitespace | Business reports, decks |
| Bold/Editorial | High contrast, vibrant | Heavy headers, varied sizes | Social media, marketing |
| Dark Mode | Dark BG, neon/bright accents | Light text, glowing elements | Tech, modern brands |
| Illustrated | Soft pastels, earthy | Rounded fonts, organic | Education, health, lifestyle |
| Data-Heavy | Systematic color coding | Monospace data, clear hierarchy | Analytics, research |

## Aspect Ratio Quick Reference

| Use Case | Ratio | Notes |
|----------|-------|-------|
| Instagram/TikTok Story | `9:16` | Default |
| Instagram/LinkedIn Post | `4:5` | Feed posts |
| Twitter/X Card | `16:9` | Landscape |
| Pinterest | `2:3` | Tall format |
| Presentation Slide | `16:9` | Widescreen |
| Square Post | `1:1` | Universal |

---

## Brand Kits

### Bishop AI
**ALWAYS apply this brand kit by default for every infographic unless the user explicitly requests a different style. This is the default brand for all infographic generation.**

> Authoritative source: `C:\Users\richm\.claude\bishop-ai-profile\bishop-ai-profile\brand\tokens.json` and `bishop-ai-profile\brand\BRAND.md`
> **Layout composition (MANDATORY):** follow `bishop-ai-profile\brand\COLLATERAL-STYLE.md` — the approved editorial one-pager style (dark masthead band, gold-numbered sections with right-aligned micro-captions, one dark hero card per region, `TYPE · QUALIFIER` kickers, ghost-numeral grids, dark footer with link columns). Reference PDF: `bishop-ai-profile\brand\references\approved-infographic-style-2026-08.pdf`.

**Colors (exact — no substitutions):**
- **Background (primary):** `#F9F6F0` (warm-white) — default for all light-mode content
- **Background (secondary/dividers):** `#E6E2DE` (light-gray)
- **Dark cards:** `#1E2333` (dark-charcoal) — signature contrast element; use for module rows, callout panels, examples
- **Primary headlines:** `#000814` (deep-black)
- **Body text inside light sections:** `#1E2333` (dark-charcoal)
- **Text inside dark cards:** `#FFFFFF` (white)
- **Gold accent:** `#E0B848` — highlights, CTAs, brush-stroke marks, number badges
- **Blue accent:** `#1894C9` — supporting callouts only
- **Never use:** `#FAFBFA`, `#000813`, `#1D2333`, `#0D1B2A`, `#D4AF37`, `#D4A853`, `#F5F0E8` — these are legacy incorrect values

**Typography:**
- **H1 titles:** Poppins weight 900 (Black), 72pt minimum
- **H2 headings:** Poppins weight 700 (Bold)
- **Subheadings/labels:** Montserrat SemiBold 600, 11px uppercase, letter-spacing 1.5px
- **Body copy:** Open Sans Regular 400, 16pt max, never more than 1 line per card
- **Never use:** Inter (legacy error), ExtraBold (use Black/900 for H1)

**Visual Motifs (these define the Bishop AI look):**
- **Brush-stroke highlight:** Gold `#E0B848` painted marker swipe behind the most important word in the headline. Include in every infographic with a text hero.
- **Dark card panels:** Full-width `#1E2333` cards with white text — the primary way to create visual hierarchy. Every module, step, or list item gets one of these.
- **Thin grid-line dividers:** 1px `#E6E2DE` horizontal rules between sections only.
- **Gold arrow marks:** Simple `→` in Gold for directional emphasis — used sparingly, never decorative.
- **No icons, no gradients, no shadows, no borders, no textures.** Whitespace IS the design.

**Logo:**
- NEVER describe or generate the Bishop AI logo in the AI prompt — AI cannot reproduce it accurately.
- Reserve a clean empty zone in the bottom-left corner (approximately 120x45px, no text or elements). User overlays the real logo file in Canva or Photoshop after generation.

**Scripts and paths:**
- **Script:** `C:/Users/richm/Downloads/generate_kie.py`
- **Upload script:** `C:/Users/richm/.claude/scripts/upload_gdrive.py`
- **Env file:** `C:/Users/richm/.env`
- **Output dir:** `C:/Users/richm/Downloads/images/infographics/`
- **Prompt dir:** `C:/Users/richm/Downloads/prompts/infographics/`


## Copy Language Standards

Any text content in infographics -- headlines, stat labels, callouts, section titles -- must avoid overused AI and corporate language.

**Full banned list:** `~/.claude/bishop-ai-profile/brand-evals/banned-phrases.md`

Never write headlines or labels using: game-changer, transformative, cutting-edge, revolutionary, innovative, seamless, robust, scalable (vague), synergy, actionable insights, thought leader, skyrocket, dominate, paradigm shift, disruptive, frictionless, unlock (vague), empower, unprecedented, groundbreaking, holistic, multifaceted.

Write headlines as direct, specific claims -- e.g., "AI cuts response time by 40%" not "Transformative AI revolutionizes workflows".


<!-- design-bridge:start -->

## Design bridges: consult before building

Three bridge skills sit under this one. None of them produces deliverables; this
skill still owns the output.

1. **`design-extract`** — MEASURED tokens from one named site, repo, or project.
   When a design system is active it wins on layout, spacing, type scale,
   components, motion and interaction states.
2. **`design-intel`** — RECOMMENDED generic values (layout, spacing, UX,
   accessibility, chart selection, font pairing) where brand and the active
   system are silent.
3. **`design-sources`** — external craft rules plus the deterministic gate. Read
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
system"). Near-miss phrasings — "use Linear's colors", "make it look like Linear", "match
Linear's branding" — do NOT count. Only the literal phrase.

- **Phrase present** -> that extracted system supersedes `branding-agent` for this one
  deliverable. Read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`, and use its
  colors and font families directly.
- **Phrase absent** -> resolve the active system the normal way:
  1. A system named in the request ("in the linear system", "build this like Stripe"), or a
     `.design-system` marker file in the working folder.
  2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
  3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
     motion, easing, interaction states.
     **KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families, logo
     treatment.
  4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Measured beats recommended: where an active system covers a decision, it outranks
`design-intel`. Where it is silent — accessibility, chart choice, breakpoints —
`design-intel` is still the answer.

**This skill emits images or decks.** Read `screens/` and `references/VISUAL_GUIDE.md` to describe the visual language in prompts, and `tokens/` for palette bounds.

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
<!-- /design-extract:connector v1 -->
