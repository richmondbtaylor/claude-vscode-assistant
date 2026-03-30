---
name: visigen
description: Generates high-CTR YouTube thumbnail images for Rich Taylor's AI channel using the VISIGEN Framework + KIE AI pipeline. Use this skill whenever the user wants to create a YouTube thumbnail, needs thumbnail concepts, or says "make a thumbnail for X". Handles the full pipeline: content analysis → expression selection → prompt construction → image generation via KIE API with Rich's face reference → local file output.
---

# VISIGEN — YouTube Thumbnail Generator

Full pipeline: analyze content → select expression → build prompt → generate 3 variations via KIE API with face reference → save images.

---

## Prerequisites

- **Face reference:** `C:\Users\richm\.claude\skills\visigen\references\rich_reference.jpg` — must exist. If missing, ask user to save one of their reference photos there before generating.
- **API key:** Shared with infographic-generator at `C:\Users\richm\.claude\skills\infographic-generator\.env`
- **Script:** `C:\Users\richm\.claude\skills\visigen\scripts\generate_thumbnail.py`
- **Output dir:** `C:\Users\richm\.claude\skills\visigen\images\`
- **Prompt dir:** `C:\Users\richm\.claude\skills\visigen\prompts\`

---

## Inputs

Required:
1. **Video Title**
2. **Hook** — one sentence describing the core idea

Optional:
3. **Brand** — `default` (dark gray + electric blue) or `prompt-anything` (charcoal + gold). Defaults to `default`.
4. **Expression** — override auto-selection (thinking / shock / confident-smile)

---

## Step 1 — Content Analysis

Identify: core emotion, primary curiosity element, value proposition, appropriate expression.

**Expression auto-selection:**
- "secret", "hidden", "nobody knows" → **Confident Knowing Smile** (slight smirk, direct eye contact, relaxed posture)
- "shocking", "can't believe", "insane", "dead", "wrong" → **Shock / Surprise** (wide eyes, mouth open, leaning back)
- Tutorials, methods, analysis, problem-solving → **Intense Focus / Thinking** (furrowed brow, hand near chin, looking slightly down/side)

---

## Step 2 — Brand Palette

| Element | Default | Prompt Anything |
|---|---|---|
| Background | `#1A1A1A` dark gray | `#101319` deep charcoal |
| Secondary BG | — | `#000814` near black |
| Primary accent | `#00FFFF` electric blue | `#E0B848` gold |
| Secondary accent | — | `#1894C9` sky blue |
| Contrast element | — | `#E32E52` crimson red |
| Text | `#FFFFFF` white | `#FFFFFF` white |
| Typography (PA only) | — | Poppins Bold titles, Montserrat subheadings, Open Sans body |

---

## Step 3 — Avatar Description (Rich Taylor)

Every prompt must include this character description for face consistency:

> Semi-realistic portrait of a man in his mid-30s: medium-length wavy brown hair with natural volume swept back, short brown beard/stubble, light blue-green eyes, athletic broad-shouldered build, strong jaw and defined cheekbones, fair skin with warm undertones. Dramatic side or three-quarter lighting emphasizing jaw structure. Sharp focus on face. [EXPRESSION from Step 1].

---

## Step 4 — Build Prompt (per variation)

Each variation gets a distinct JSON prompt file. Structure:

```json
{
  "prompt": "<see template below>",
  "api_parameters": {
    "aspect_ratio": "16:9",
    "resolution": "2K",
    "output_format": "png"
  }
}
```

**Note:** Do NOT include `image_input` in the JSON — the script auto-injects Rich's face reference from `references/rich_reference.jpg`.

### Prompt Template

```
YouTube thumbnail, 16:9, ultra high CTR design. [AVATAR_DESCRIPTION]. Subject positioned [POSITION: right two-thirds / centered]. [EXPRESSION_DETAILS]. Background: solid [BG_COLOR], minimal and clean. Bold sans-serif text overlaid: primary text "[PRIMARY_TEXT]" in large white bold font [TEXT_POSITION: left third / bottom bar / top]. Accent color [ACCENT_COLOR] on keyword "[KEYWORD]". [SECONDARY_TEXT if any: smaller below in accent color]. Dramatic side lighting, high contrast, deep shadows on face. Professional thumbnail composition. Text has shadow or outline for legibility at small sizes. Ultra sharp, no blur, clean edges, print quality. Negative: blurry text, random background, stock photo aesthetic, generic face, cluttered layout, multiple fonts, illegible small text.
```

### Three Variations — Required Differences

| Variation | Expression | Layout | Text Treatment |
|---|---|---|---|
| A | Thinking / Focus | Avatar right, text left third | Primary text white, accent on 1 keyword |
| B | Shock / Surprise | Avatar right leaning back, large text top+left | Bold headline dominant, secondary accent line below |
| C | Confident Knowing Smile | Avatar centered, bottom text bar with semi-transparent box | Direct eye contact, text in bottom third |

Each must be meaningfully different — not minor tweaks.

---

## Step 5 — Save Prompt Files

Save each to:
```
C:\Users\richm\.claude\skills\visigen\prompts\[video-slug]_varA.json
C:\Users\richm\.claude\skills\visigen\prompts\[video-slug]_varB.json
C:\Users\richm\.claude\skills\visigen\prompts\[video-slug]_varC.json
```

Use lowercase hyphenated slug from title, max 30 chars.

---

## Step 6 — Generate All Three in Parallel

Run all three simultaneously using the Agent tool with three parallel subagents, each running:

```bash
python "C:\Users\richm\.claude\skills\visigen\scripts\generate_thumbnail.py" \
  "C:\Users\richm\.claude\skills\visigen\prompts\[slug]_var[A/B/C].json" \
  "C:\Users\richm\.claude\skills\visigen\images\[slug]_var[A/B/C].png"
```

The script automatically injects Rich's face reference from `references/rich_reference.jpg` as `image_input` to the KIE API.

---

## Step 7 — Report Back

For each variation output:

**Variation [A/B/C]: [Descriptive Title]**
- **Expression:** [which]
- **Primary Text:** [exact words on image]
- **Colors:** [palette used]
- **File:** `C:\Users\richm\.claude\skills\visigen\images\[filename].png`
- **CTR Rationale:** 2–3 sentences

Then ask: "Which variation do you want to use, or should I iterate on any of them?"

---

## CTR Rules (apply to every prompt)

1. Primary text: max 4–6 words, creates curiosity gap — never complete sentences
2. One keyword in accent color for visual punch
3. Face must be clearly lit and occupying at least 40% of the frame
4. Text must be legible at 320×180px
5. Background never competes with subject

---

## Channel Context

Rich's channel: AI tools and productivity for creative professionals and entrepreneurs. Thumbnails must convey expertise, insider knowledge, and immediate value. Audience is tech-savvy and time-conscious.
