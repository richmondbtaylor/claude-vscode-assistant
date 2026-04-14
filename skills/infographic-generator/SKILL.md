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
| Style | Bishop AI brand — minimal & impactful: light background #FAFBFA (white) or #E6E2DE (off-white), Deep Navy #000813 headings, Dark Navy #1D2333 body text, Gold #E0B848 primary accent, Blue #1894C9 for positive/result elements, Red/Coral #E05252 for problem/contrast only, max 3 elements per section, no decorative clutter |
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

### Prompt Narrative Template

Write the `prompt` value as a single dense string following this structure:

```
Professional infographic titled "[TITLE]". Bishop AI brand style: light premium background #FAFBFA (white) or #E6E2DE (off-white), generous whitespace, bold single-idea sections.
Layout: [describe top to bottom — each section has ONE clear message, maximum 3 elements per section, no visual noise].
Color palette: White #FAFBFA or Off-White #E6E2DE background, Deep Navy #000813 for primary headlines, Dark Navy #1D2333 for body text, Gold #E0B848 for primary accent/highlights, Blue #1894C9 for positive outcomes/results, Red/Coral #E05252 for problem/contrast sections only — never on CTAs or positive elements. Off-White #E6E2DE for card/panel backgrounds.
Typography: Poppins ExtraBold for H1 headlines at 64pt minimum, Montserrat Bold for subheadings/labels, Open Sans for body copy at 20pt max — never more than 2 lines of body copy per element.
Data content: [EXACT DATA — repeat user's numbers verbatim. Present each stat as a BIG number in Poppins ExtraBold + short Montserrat label, nothing else].
Visual elements: thin single-line dividers only, no icons unless essential, no gradients, no shadows, no decorative borders. Let whitespace do the work.
Quality directive: ultra-sharp, print-quality, pixel-perfect alignment, zero text rendering errors. Less is more — if an element doesn't add meaning, remove it.
Negative: dark background, blurry text, garbled typography, illegible fonts, busy layouts, too many colors, decorative clutter, drop shadows, gradients, icons for decoration, more than 4 bullet points per section, stock photo aesthetic, photorealistic faces, lens flare, bokeh, photography lighting, beauty filters, skin textures.
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

- **Background (primary):** `#FAFBFA` (white)
- **Background (secondary/cards):** `#E6E2DE` (off-white)
- **Primary text (headlines):** `#000813` (Deep Navy)
- **Body text:** `#1D2333` (Dark Navy)
- **Gold accent (primary highlights, CTAs):** `#E0B848`
- **Blue accent (positive outcomes/results):** `#1894C9`
- **Red/Coral accent (problem/contrast only — never on CTAs):** `#E05252`
- **Typography:** Poppins ExtraBold (H1 titles), Montserrat Bold (subheadings/labels), Open Sans (body)
- **Logo:** NEVER describe or generate the Bishop AI logo in the AI prompt. AI models cannot reproduce the exact logo. Instead: generate the infographic with a blank reserved zone (e.g., "leave a clean empty area in the bottom-left corner, approximately 100x40px, no text or elements in that zone") and instruct the user to overlay the real logo file in Canva, Photoshop, or similar tool after generation.
- **Logo placement:** Bottom-left corner, reserved blank zone only — user overlays the actual file manually.
- **Script:** `C:/Users/richm/Downloads/generate_kie.py`
- **Env file:** `C:/Users/richm/.env`
- **Output dir:** `C:/Users/richm/Downloads/images/infographics/`
- **Prompt dir:** `C:/Users/richm/Downloads/prompts/infographics/`


## Copy Language Standards

Any text content in infographics -- headlines, stat labels, callouts, section titles -- must avoid overused AI and corporate language.

**Full banned list:** `~/.claude/skills/references/banned-phrases.md`

Never write headlines or labels using: game-changer, transformative, cutting-edge, revolutionary, innovative, seamless, robust, scalable (vague), synergy, actionable insights, thought leader, skyrocket, dominate, paradigm shift, disruptive, frictionless, unlock (vague), empower, unprecedented, groundbreaking, holistic, multifaceted.

Write headlines as direct, specific claims -- e.g., "AI cuts response time by 40%" not "Transformative AI revolutionizes workflows".
