---
name: citadel
description: Creates social media thumbnails by generating actual images via the KIE.ai pipeline, following the CITADEL framework. Invoke this skill whenever a user asks for a YouTube thumbnail, Instagram post graphic, LinkedIn banner, or any social media visual — even if they phrase it as "make me a thumbnail", "design a cover image", "create a post image", "generate a thumbnail", or just "I need a thumbnail for my video". Also trigger when the user says CITADEL, mentions A/B testing thumbnails, or asks to iterate on an existing thumbnail concept. Always invoke before attempting any thumbnail generation.
---

# CITADEL Thumbnail Framework

You generate **actual thumbnail images** via the KIE.ai pipeline — same engine as carousel and infographic skills. The output is real image files saved locally, not text prompts.

**Before designing anything**, invoke the `branding-agent` skill to load official brand colors.

---

## Prerequisites

- Script: `C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py`
- API key: `.env` file at `C:\Users\richm\.claude\skills\infographic-generator\.env` (`KIE_API_KEY=...`)
- Reference photos: `C:\Users\richm\.claude\skills\citadel\assets\references\` (use as `image_input` for style reference)
- Prompt output dir: `C:\Users\richm\.claude\prompts\thumbnails\<thumbnail-slug>\`
- Image output dir: `C:\Users\richm\.claude\images\thumbnails\<thumbnail-slug>\`

---

## Workflow: C → I → T → A → D → E → L

### C — Context

Parse the user's request for:
- **Headline text**: the words that appear on the thumbnail (required — ask if missing)
- **Platform**: YouTube, Instagram, LinkedIn, TikTok, or other
- **Mode preference**: Dark or Light (default: infer from topic energy — dramatic/opinion = Dark, data/educational = Light)
- **Color preference**: any dominant hue override

---

### I — Input

| Input type | What to extract |
|---|---|
| URL | Scrape for article title, key phrases, core argument |
| Video transcript | Extract the core topic, most compelling claim, key themes |
| Document / PDF | Extract main title, subheadings |
| Raw text | Treat as the source brief |
| No input | Proceed from headline + platform alone |

If the source title is more than 5 words, propose **2–3 short punchy variations** and confirm before continuing.

---

### T — Target

| Platform | Aspect ratio | KIE parameter |
|---|---|---|
| YouTube | 16:9 | `"aspect_ratio": "16:9"` |
| Instagram post | 4:5 | `"aspect_ratio": "4:5"` |
| Instagram story / TikTok | 9:16 | `"aspect_ratio": "9:16"` |
| LinkedIn | 1.91:1 | `"aspect_ratio": "16:9"` (closest fit) |

Unknown platform → ask for exact dimensions before proceeding.

**YouTube safe zone**: bottom-right corner is obscured by the duration badge — keep key elements away from it.

---

### A — Analysis

#### Subject reference

Check `C:\Users\richm\.claude\skills\citadel\assets\references\` for reference images.

**Photos present** — the pose is picked automatically by `pick_pose.py` in Step 3. Do not manually select or pass to KIE. **The references are 3×3 pose grids, not single photos.** `pick_pose.py` tracks every individual pose cell in `headshot_ledger.json` and never returns a used one — Rich's rule: **never repeat a headshot.** This is stricter than the old `pick_reference.py` (which only rotated grid files and let two thumbnails in one run land on the same pose — the bug that shipped duplicate headshots on the first MAI video).

**No photos present** — if the references folder is empty, describe the space in the prompt as empty and skip compositing. Fallback physical description for prompts:
> `Athletic male subject, mid-30s. Short-to-medium brown hair, slightly tousled and natural. Short brown stubble beard. Strong jaw and defined cheekbones. Fair skin with warm undertones. Smart-casual attire — dark fitted sweater or open-collar dark shirt. Three-quarter angle, relaxed confident posture, hands loosely clasped or one hand gesturing naturally.`

#### Title text check

If the headline is more than 4 words, flag it — shorter text is more readable at thumbnail scale. Propose alternatives if needed.

---

### D — Design

Two established visual modes based on actual reference thumbnails. Choose based on topic energy, or ask the user.

---

#### MODE 1 — Dark / High Drama

Best for: opinion pieces, bold claims, controversial takes, "stop doing X" topics.

**Layout:**
- Background: near-black `#000814` with warm amber-brown bokeh blur (out-of-focus interior/room environment behind subject)
- Subject: positioned on the **right side**, ~40% of frame width, three-quarter angle toward camera
- Warm rim lighting on subject's near shoulder to separate from the dark background
- Text: left side of frame, left-aligned, stacked vertically

**Typography:**
- Primary headline: large bold white sans-serif, title case, left-aligned — takes up ~60% of left half
- Key phrase or punchline: same size, with a **gold `#E0B848` hand-painted brush-stroke highlight behind it**
- Secondary callout: smaller text inside a **white rounded-rectangle pill/card** below the headline, dark text
- Subtle dot-grid pattern top-left corner (low opacity, ~10%)

**Prompt template (Dark mode):**

```
Social media thumbnail, [ASPECT RATIO]. Dark dramatic editorial design.

Background: near-black #000814 with warm amber-brown bokeh blur of a softly lit interior room. Shallow depth of field — background is fully defocused warm tones.

Subject: [SUBJECT DESCRIPTION OR "use the provided reference photo as subject"]. Positioned on the RIGHT side of the frame, approximately 40% of total width. Three-quarter angle toward camera. Warm amber rim lighting on near shoulder separating subject from background. Subject is relaxed and confident.

Left side of frame contains the text layout: Large bold white sans-serif headline text reading "[LINE 1]" at approximately 72pt. Below it, same size bold white text reading "[LINE 2]" but with a visible gold #E0B848 hand-painted brush-stroke highlight beneath the key phrase "[KEY PHRASE]". Below that, a white rounded-rectangle pill card with dark text reading "[SECONDARY TEXT]".

Top-left corner: subtle small dot-grid pattern at 10% opacity.

Style: photorealistic, cinematic, high contrast, warm vs dark tension. Sharp subject, blurred background.

Negative: blurry subject, garbled text, illegible fonts, busy layouts, multiple competing focal points, cold color grading, flat lighting, lens flare, watermarks, stock photo aesthetic.
```

---

#### MODE 2 — Light / Editorial

Best for: data, statistics, how-to, educational, informational topics.

**Layout:**
- Background: warm cream `#F9F6F0` or `#F5EDD8`
- Massive bold black UPPERCASE headline: dominates upper-left, oversized — almost full width
- Thin horizontal gold line `#E0B848` accent below or beside the headline
- Subject: positioned **bottom-right**, slightly cropped at waist or shoulder, as if entering the frame from below-right
- Optional: subtle photographic collage texture at bottom (landscape, mountain, or architectural silhouette)
- Optional: low-opacity geometric circle in upper-right background
- Small scattered dot accents

**Typography:**
- Headline: massive Poppins ExtraBold or equivalent, all-caps or title-case, black `#000814`
- Supporting stat or subtitle: medium-weight, smaller, below headline — Montserrat Bold style
- All text is crisp black on the cream background — no white text

**Prompt template (Light mode):**

```
Social media thumbnail, [ASPECT RATIO]. Clean editorial magazine design.

Background: solid warm cream off-white #F9F6F0. Generous whitespace. Premium editorial feel.

Upper left: massive bold uppercase sans-serif headline text reading "[HEADLINE LINE 1]" at approximately 96pt, color #000814 (near-black). Second line "[HEADLINE LINE 2]" same size. Thin horizontal gold #E0B848 line accent (2px) directly below the headline block.

Below headline: medium-weight supporting text reading "[SUPPORTING TEXT]" in Montserrat Bold style, color #1E2333, approximately 28pt.

Subject: [SUBJECT DESCRIPTION OR "use the provided reference photo as subject"]. Positioned bottom-right of frame, slightly cropped at waist — figure appears to emerge from below-right into the composition. Smart-casual dark attire.

Optional bottom texture: subtle photographic landscape or mountain silhouette collage blended at 30% opacity across the bottom 25% of the image. Low-opacity geometric circle outline in upper right at 15% opacity.

Style: clean, editorial, print-quality, high contrast text, magazine cover aesthetic.

Negative: dark backgrounds, blurry text, garbled typography, illegible fonts, drop shadows, gradients, decorative clutter, photorealistic lens effects, bokeh, warm lighting filters.
```

---

### E — Execution

Generate **3 variations** — one Dark, one Light, one alternate (either mode with a different text placement or color treatment). Run them in parallel.

#### Step 1 — Write JSON prompt files

Create `C:\Users\richm\.claude\prompts\thumbnails\<slug>\` and write one JSON file per variation.
**Do NOT include `image_input`** — the person is composited in Step 3, not passed to KIE.

```json
{
  "task": "thumbnail_generation",
  "schema_version": "prism-2.0",
  "model_target": "nano-banana-2",
  "prompt": "<full dense prompt from template above>",
  "api_parameters": {
    "aspect_ratio": "16:9",
    "resolution": "2K",
    "output_format": "jpg"
  }
}
```

Use `variation-a-dark.json`, `variation-b-light.json`, `variation-c-alt.json` as filenames.

**Important prompt note:** When writing the prompt, do NOT describe a subject/person in the scene — the background should have empty space on the right side where the subject will be composited in Step 3.

#### Step 2 — Generate backgrounds in parallel

Use two simultaneous Agent calls:
- **Agent A**: generate variation A and B
- **Agent B**: generate variation C

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py `
  C:\Users\richm\.claude\prompts\thumbnails\<slug>\variation-a-dark.json `
  C:\Users\richm\.claude\images\thumbnails\<slug>\variation-a-dark-bg.jpg `
  "16:9"
```

Save with `-bg.jpg` suffix (these are backgrounds before compositing).

#### Step 3 — Pick reference and composite subject

Pick a fresh pose for **each** variation with `pick_pose.py`. Call it once **per variation** — each call advances the ledger, so three calls guarantee three distinct, never-before-used poses (this is what prevents the duplicate-headshot bug). Each call prints `<grid_path>\t<pose_index>`:

```powershell
python C:\Users\richm\.claude\skills\citadel\scripts\pick_pose.py    # -> C:\...\image_xxx.jpg<TAB>7
```

Split that output on the tab into `<grid_path>` and `<pose_index>`, then composite in **grid mode** (`--pose N`, NOT `--single` — the references are grids):

```powershell
python C:\Users\richm\.claude\skills\citadel\scripts\composite.py `
  C:\Users\richm\.claude\images\thumbnails\<slug>\variation-a-dark-bg.jpg `
  <grid_path> `
  C:\Users\richm\.claude\images\thumbnails\<slug>\variation-a-dark.jpg `
  --pose <pose_index> --side right --scale 0.85
```

Run pick+composite for all three variations (three separate `pick_pose.py` calls). Final outputs save without the `-bg` suffix. **Always view each composited result** and confirm it's Rich per the avatar baseline (brown hair, stubble, dark casual) — never a mismatched face. If you make a manual pose pick outside `pick_pose.py`, log it with `pick_pose.py --commit <grid_path> <pose_index>` so it's never reused.

#### Step 4 — Report

When all three complete, display the images. Ask which variation they prefer and invite follow-up commands.

---

### L — Loop

After delivery, support simple revision commands applied to the last-generated variation:

| Command | What to do |
|---|---|
| "make the text red" | Update prompt color spec, regenerate that variation only |
| "switch to light mode" | Swap to Mode 2 template, regenerate |
| "bigger headline" | Increase pt size in prompt, regenerate |
| "try a different headline" | Propose 3 options, confirm, regenerate |
| "more dramatic" / "darker" | Increase contrast and saturation descriptors, regenerate |

**Vague feedback** ("make it better", "more energy"): ask exactly 2 targeted questions before regenerating:
1. Warmer/cooler color? Or more/less saturated?
2. Should the text be more dominant or the subject?

Each session is a **blank slate** — do not carry over settings from previous conversations. Up to 10 thumbnail requests per session.

---

## Output format

Always end your delivery with:

```
## Thumbnails generated

- **Variation A — Dark**: `images/thumbnails/<slug>/variation-a-dark.jpg`
- **Variation B — Light**: `images/thumbnails/<slug>/variation-b-light.jpg`
- **Variation C — Alt**: `images/thumbnails/<slug>/variation-c-alt.jpg`

Which one is closest? Any changes you want to make?
```


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
