---
name: carousel
description: Generates complete, slide-by-slide social media carousel content AND images for Instagram and LinkedIn using the CAROUSEL Framework + KIE AI pipeline. Use this skill whenever the user wants to create a carousel post, needs slide content for Instagram or LinkedIn, wants to turn a topic or piece of content into a swipeable carousel, asks for carousel copy or structure, or says things like "make me a carousel about X", "write carousel slides for Y", "help me create a LinkedIn carousel", "turn this into a carousel", "I need carousel content", or wants a seamless/panoramic carousel where slides bleed into each other as one continuous picture. Generates actual slide images via KIE AI -- not just text. Always trigger for carousel creation even if the user only mentions a topic and platform -- infer the rest.
---

# CAROUSEL Framework — Social Media Carousel Generator

You are an expert social media content strategist. You write high-performing carousel posts in the style of Chris Do, Sahil Bloom, and Justin Welsh: visually minimal, information-dense, no fluff, punchy clarity.

## Step 1: Gather Inputs

**Required** (ask if not provided):
- **Topic**: What is this carousel about?
- **Goal**: saves | shares | comments | follows | DMs | link clicks

**Optional** (use smart defaults if missing):
- **Platform**: Instagram | LinkedIn | Both (default: both)
- **Audience**: Who is this for? (default: infer from topic)
- **Format**: numbered list | step-by-step | myth-busting | before/after | story arc (default: auto-select)
- **Tone**: educational | conversational | bold (default: adapt per platform)
- **Mode**: seamless (default) | standalone -- seamless generates the deck as continuous panoramas so slides bleed into each other; standalone generates each slide as an isolated image
- **Raw Input**: Existing content to repurpose, or create from scratch?

If topic and goal are clear from context, proceed without asking.

---

## Step 2: Select Format

Pick the best fit for the topic:

| Format | Best For |
|---|---|
| **Numbered List** | Tips, tools, resources, principles |
| **Step-by-Step** | Processes, workflows, how-tos |
| **Myth-Busting** | Correcting misconceptions, contrarian takes |
| **Before/After** | Transformations, comparisons |
| **Story Arc** | Personal experiences, case studies |

If a topic needs more than 10 slides, flag it — suggest splitting into a series or narrowing scope.

---

## Step 3: Apply Structure Rules

### Slide Count
- 5–6 slides: simple tips, quick wins, single concepts
- 7–10 slides: frameworks, processes, story arcs

### Text Limits (non-negotiable)
- Max **3 lines** per slide
- Max **8 words** per line
- No paragraphs, no walls of text

### Text Hierarchy
- **HEADLINE**: bold, primary message — required on every slide
- **SUBTEXT**: one supporting line — only when needed for clarity
- Never more than two text levels per slide

### Backbone (always)
1. Slide 1: Hook — scroll-stopping opener
2. Slides 2–N: Value — core content
3. Final slide: CTA — one clear action

### Platform Placement
- **Instagram**: keep text in the upper 2/3 (UI covers the bottom ~20%)
- **LinkedIn**: top-heavy preferred, slightly more detail allowed

---

## Step 4: Write 3 Hook Options

Every carousel gets three Slide 1 options with different angles:

1. **Curiosity**: Creates a knowledge gap — "The one thing nobody tells you about X"
2. **Contrarian**: Challenges conventional wisdom — "Everyone says X. They're wrong."
3. **Direct Benefit**: Promises clear value — "How to [outcome] without [obstacle]"

Hook must be specific, not generic. Ask: would this make someone stop scrolling? Avoid: "you won't believe", "this one trick", "mind-blowing", "game-changer".

---

## Step 5: Weave In Engagement Mechanics

Place these naturally inside value slides — don't force them:
- **Teaser**: "Wait for slide [N] — this changes everything"
- **Question**: "Have you experienced this? Comment below."
- **Surprise**: "Here's the part that surprised me..."
- **Relatability**: "If you've ever felt [X], you're not alone."

---

## Step 6: Design the CTA (Final Slide)

Match the action to the goal:

| Goal | CTA |
|---|---|
| Saves | "Save this for later" |
| Shares | "Share with someone who needs this" |
| Comments | "What's your experience with [X]? Drop a comment." |
| Follows | "Follow for more [content type]" |
| DMs | "DM me [KEYWORD] for the full guide" |
| Link Clicks | "Link in bio for the full breakdown" |

CTA test: if someone sees only the final slide, do they know exactly what to do and why?

---

## Step 7: Add Minimal Visual Notes

Use bracketed cues to guide image generation:
- `[ICON: lightbulb]` / `[ICON: warning]` / `[ICON: checkmark]`
- `[HIGHLIGHT: this phrase]` / `[BOLD: key term]`
- `[BACKGROUND: dark]` / `[BACKGROUND: light]` / `[BACKGROUND: gradient]`
- `[TEXT: upper third]` / `[TEXT: centered]`
- `[LAYOUT: tool-list]` / `[LAYOUT: comparison]` / `[LAYOUT: podium]` / `[LAYOUT: single-stat]`
- `[LOGOS: tool1, tool2, tool3]` -- include when referencing specific tools/platforms
- `[SCREENSHOT: <url or tool> -- <what to show>]` -- slide will carry a REAL captured screenshot inside the floating card (see Real Screenshot Cards section)

---

## Step 8: Self-Audit Before Output

Check every slide:
- [ ] Max 3 lines per slide
- [ ] Max 8 words per line
- [ ] 3 hook options written
- [ ] CTA matches stated goal
- [ ] No banned words (see below)
- [ ] Genuine value delivered

**Banned words/phrases**: the single source of truth is `~/.claude/bishop-ai-profile/brand-evals/banned-phrases.md` (AI lingo, hype, corporate speak, structural tells, no em dashes ever). Additionally for carousels: limited time, act now, don't miss out, basically, essentially, literally, very, really.

**Mandatory lint gate (Rich, 2026-07-21):** every caption block (Instagram AND LinkedIn) must pass
`python ~/.claude/skills/captioncraft/scripts/caption_lint.py <file> --platform ig|linkedin`
before delivery — exit 0 or rewrite and re-lint. Emoji policy is enforced by the linter (IG 2-4, LinkedIn 0-1). Slide copy itself follows the banned list too (lint slide text with `--no-emoji-check`).

If any check fails, revise before outputting.

---

## Output Format

```
### CAROUSEL OVERVIEW
- **Topic**:
- **Platform**:
- **Goal**:
- **Format**:
- **Slide Count**:

---

### HOOK OPTIONS (Choose 1)
1. [Curiosity hook]
2. [Contrarian hook]
3. [Direct benefit hook]

---

### SLIDE-BY-SLIDE CONTENT

**Slide 1 — Hook**
HEADLINE: [hook text]
[visual note]

**Slide 2 — [name]**
HEADLINE: [text]
SUBTEXT: [text, if needed]
[visual note]

... (continue for all slides)

**Slide [N] — CTA**
HEADLINE: [CTA text]
SUBTEXT: [supporting line, if needed]
[visual note]

---

### PLATFORM VARIATIONS
*(include only when targeting both platforms)*

**Instagram**: [key adjustments]
**LinkedIn**: [key adjustments]

---

### ENGAGEMENT STRATEGY
- **Hook angle**: [psychological trigger used]
- **Mid-carousel hooks**: [engagement mechanics and where they appear]
- **CTA type**: [action chosen and why it matches the goal]
- **Save-worthiness**: [why someone would bookmark or share this]
```

---

## Repurposing Existing Content

When given a blog post, transcript, notes, or video:
1. Extract 5–10 key insights that translate to carousel format
2. Create a hook that wasn't in the original
3. Restructure into the best-fit format
4. Condense wording to fit text limits
5. Add a goal-aligned CTA

If the source is too nuanced for carousel format, say so and suggest splitting into a series or using a long-form post instead.

---

## Step 9: Generate Carousel Images (KIE AI Pipeline)

> Brand values in this section are sourced from the branding-agent skill. If in doubt about any color or style, consult branding-agent.

After finalizing slide content, generate an actual image for each slide using the KIE AI pipeline.

### Visual Style Presets

**All carousels use the Light Editorial style by default (Rich, 2026-08-25).** This corrected a
direct conflict: this file used to mandate a near-black ground while
`feedback_light_background_default` records Rich saying *"I never want the dark EVER again"*
about exactly this. Light wins. Only build a dark deck if Rich asks for one in the moment.

#### Light Editorial Style (Default -- Always Use)

Warm off-white ground, near-black ink type, golden-amber as the single accent. Depth comes
from soft neutral drop shadows, NOT from glow -- glow is a dark-ground device and reads as
grime on white.

| Element | Value |
|---------|-------|
| **Background** | Warm off-white `#F9F6F0` -- solid and perfectly uniform across all slides |
| **Primary Text** | Near-black ink `#000814` -- use "ultra-bold near-black sans-serif" in prompts, never specific font names |
| **Body Text** | Warm grey -- use "medium-weight warm grey text" in prompts |
| **Primary Accent** | Golden-amber `#E0B848` -- thin divider lines, bullet dash markers, underline swashes, card edge lines |
| **Slide Number** | Large bold warm mid-grey number (e.g., "02") top-left. No word-label above it -- the number stands alone |
| **Handle** | `@bishop_ai_` small warm grey text at bottom center, every slide. NEVER a website/domain (promptanything.io, bishopai.io, any URL) anywhere on any slide -- the handle is the only footer text |
| **3D Floating Element** | Right-side clean white UI card tilted in perspective, lifted by a soft neutral drop shadow -- unique per slide, relevant to the slide topic |
| **Portrait Panel** | Rounded vertical panel in a slightly deeper warm sand than the ground, soft drop shadow, thin amber edge line down one side |
| **CTA Slide** | Text only -- no floating card. Keyword carries an amber underline swash. |

Every prompt's negative list must include: `dark or black backgrounds, navy backgrounds, neon glow`.

Worked example, all seven slides plus the panoramas:
`prompts/carousels/invoice-fraud-bob/` with output in `images/carousels/invoice-fraud-bob-light/`.

> **The prompt examples further down this file are LEGACY DARK.** They are still correct for
> layout, zone structure, bleed and negative-prompt discipline. Translate the palette as you
> read them: `#080B14` ground becomes `#F9F6F0`, white type becomes `#000814`, and every
> "golden-amber glow radiating from behind" becomes "soft neutral drop shadow".

**CRITICAL: Never reference specific font names** (Poppins, Montserrat, Open Sans, etc.) in image generation prompts. Image gen models don't know fonts -- font names add noise and degrade output quality. Instead use descriptive terms: "ultra-bold white sans-serif", "medium-weight muted gray-white text", "small clean white monospace text".

#### Key Visual Elements (What Makes This Style Work)

1. **3D floating UI card**: Every value slide (2 through N-1) has a dark UI card on the RIGHT side, tilted in 3D perspective, showing an interface relevant to the slide topic (Claude chat, CRM dashboard, email sequence, workflow diagram, etc.). The card appears to hover with depth and a subtle drop shadow.
2. **Golden-amber glow**: A soft warm `#E0B848` glow radiates from BEHIND the floating card onto the dark background. This is the signature visual element -- it creates depth and makes the slide feel cinematic.
3. **Left-side text column**: Slide number top-left, headline, then bullet list with golden-amber dash markers. Text is LEFT-ALIGNED, not centered.
4. **Number only, no word-label**: The top-left carries ONLY the large slide number -- no "HOOK"/"MODULE 1"/"EARLY ACCESS" category word. Never add a text title above or beside the number.
5. **Bullet markers**: List items use golden-amber `#E0B848` dash markers (not checkmarks or circles).
6. **CTA slide is text-only**: No floating card on the CTA. The keyword (e.g., "AI Sales") glows in golden-amber. Left-aligned, thin amber divider line below the keyword, secondary text below in muted gray.
7. **Varied 3D elements per slide**: Each value slide should show a DIFFERENT UI interface floating on the right. Never repeat the same card type. Match the card to the slide content.

#### Reference Images

Before generating any carousel, check `C:\Users\richm\.claude\references\carousel-inspo\` for the latest style references. These images are the authoritative visual target.

#### Alternate Presets (Only When User Explicitly Requests)

| Preset | Background | Text Color | Accent | Best For |
|--------|-----------|------------|--------|----------|
| **Bold Editorial** | White `#FFFFFF` | Black `#000000` | Golden-amber `#E0B848` | Authoritative, long-form content |
| **Cream Editorial** | Warm cream `#F9F6F0` | Black | Golden-amber brush strokes + coral-red numbers | Legacy style, personal stories |

### Real Screenshot Cards (Mixed Decks)

Slides that reference something real and screenshottable (a tool, site, chat, dashboard, article) should carry a REAL screenshot inside the signature floating card instead of a model-imagined UI. Abstract/conceptual slides keep generated cards. Mixed decks are the norm. Never fake a "real" screenshot with the image model, and never let the image model redraw a captured screenshot -- real pixels only.

**Pipeline per screenshot slide:**

1. Capture the target live (2x scale):
```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\capture_screenshot.py <url> .\images\carousels\<name>\captures\shot-03.png [css-selector|-]
```
2. Wrap it in the signature card (tilt right by default, RGBA + amber glow on transparency):
```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\render_card.py .\images\carousels\<name>\captures\shot-03.png .\images\carousels\<name>\captures\card-03.png
```
3. Composite onto the panorama BEFORE slicing. Put center_x ON the zone boundary so the card straddles two slides (seamless bleed), target width ~28-32% of panorama width:
```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\composite_card.py .\images\carousels\<name>\pano-01.jpg .\images\carousels\<name>\captures\card-03.png <center_x> <center_y> <target_width> .\images\carousels\<name>\pano-01-comp.jpg
```
Compute center_x/center_y against the POST-CROP dimensions, not the raw panorama: slice_panorama.py center-crops to exactly N x panel ratio (e.g. a 2-slide square group crops the 16:9 panorama to 2:1 -- the height loss comes off the top and bottom) before slicing. Work out the crop box first (same center-crop math: if the panorama is wider than N x ratio, width is cropped symmetrically; if taller, height is), place the card relative to that box, then convert back to raw-panorama pixels by adding the crop offset. Zone boundaries sit at crop_x0 + k * (cropped_width / N). For the common case (card on a boundary, vertically centered) this reduces to: center_x = crop_x0 + cropped_width * k / N, center_y = height // 2.

Then run slice_panorama.py on the composited file. In standalone mode, composite onto the individual slide image instead.

**Cookie banners / overlays:** if a consent banner or popup lands in the capture, re-capture with a CSS selector that targets the content region below/behind it (capture_screenshot.py's selector argument), or pick a deeper page URL without the overlay. Never ship a slide with a consent dialog visible.

**Prompt rule (placeholder-cover method -- session-validated):** do NOT ask for plain empty background where the real card will go; the model will not keep text out of a reserved empty area (validated failure, two attempts). Instead, prompt a placeholder the model manages itself: 'A medium-sized plain 3D floating dark card with a completely blank empty dark screen showing absolutely nothing sits at the far right of this zone, tilted in perspective, its right half crossing into the next zone, with a warm golden-amber #E0B848 glow radiating from behind it.' The model lays out all zone text around its own card. After generation, cover the placeholder with the real card: view the panorama, estimate the placeholder body's bbox and center, then composite with center on the placeholder's center and target_width sized so the opaque card (about 2/3 of the card PNG's width) covers the placeholder body with ~10% margin. Any drawn-glow remnants outside the cover blend into the real card's own glow -- only the placeholder's opaque body must be fully covered.

**Capture shape:** drawn placeholder cards come out portrait, so capture the target at a mobile portrait viewport (capture_screenshot.py viewport args: 430 660 for ~3:2 cards, 430 860 for ~2:1) -- mobile screenshots cover them naturally and read great at slide size. Landscape desktop captures cannot cover a portrait placeholder without colliding with neighboring text.

**Group shape:** square decks (the default) use TWO-zone groups generated at 16:9 -- the slicer keeps the full width and crops ~5.5% off the top and bottom to reach 2:1, so no edge text is ever side-cropped. Because of that vertical crop, every panorama prompt must say the zone furniture (numbers, headlines, handle) stays within the central ~85% of the image height, with plain background in the top and bottom ~7%.

**Verify after slicing:** screenshot text legible, card tilt/glow matches neighboring generated cards, bleed intact across the boundary, no zone furniture covered, no ghost edges of the placeholder card peeking out from behind the real one.

**Fallback:** if a target needs a login you cannot reach or will not render, use a generated card for that slide or ask Rich for a manual capture.

### Rich's Face (Hook + CTA Slides)

Every carousel puts Rich's real face on TWO slides: the **hook (slide 01)** and the **CTA (final slide)**. Value slides keep their floating UI cards and get NO face. The face is a real headshot cut out from the citadel references and composited over a reserved portrait panel -- never generated by the image model (the `photorealistic faces` negative stays in every prompt to stop the model drawing a competing face).

**How no words overlap the face:** same placeholder-cover method as screenshot cards. The prompt reserves a *tall dark rounded vertical portrait panel, plain and empty, with an amber glow behind it* on ONE side of the zone, and forces all headline/CTA text to the opposite side. The model lays its text around the panel it drew itself, so the reserved area stays clear. After generation you cover the panel with the real cutout.

**Panel side:** put the panel on the RIGHT of the hook zone (text on the left) and on the RIGHT of the CTA (text on the left). The hook zone therefore uses the portrait panel INSTEAD of a floating UI card -- see the panorama example above. Unlike floating cards, the panel must sit FULLY INSIDE its own zone, never straddling a zone boundary -- the slicer would cut Rich in half across two slides. Keep it out of the outer ~12% of the panorama so group seams stay invisible.

**Pipeline per face slide:**

1. Cut out a fresh non-repeating headshot (auto-picks a pose from the citadel grids and commits it to the ledger, honoring the never-repeat-a-pose rule):
```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\cutout_headshot.py .\images\carousels\<name>\captures\face-01.png
```
This writes a transparent RGBA PNG of Rich with a clean HARD edge (rembg cutout + binarized/eroded alpha -- no white fringe, no feathered blur; the composite downscale anti-aliases the edge). Run it twice (once for the hook, once for the CTA) so the two slides use different poses. To force a specific pose: `cutout_headshot.py <out.png> --grid "<grid_path>" --pose N`.

2. Cover the reserved panel with the real cutout. View the generated panorama/slide, estimate the panel body's center and width, then composite (seamless: onto the panorama BEFORE slicing; standalone/CTA: onto the slide):
```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\composite_card.py .\images\carousels\<name>\pano-01.jpg .\images\carousels\<name>\captures\face-01.png <center_x> <center_y> <target_width> .\images\carousels\<name>\pano-01-comp.jpg
```
Size `target_width` so the cutout covers the panel with a small margin; set `center_y` so Rich's head sits near the top of the panel and his torso fills the rest. Compute center_x/center_y against the POST-CROP dimensions exactly as for screenshot cards (the slicer center-crops before slicing).

**Never cut Rich off.** His head, face, and shoulders must be fully inside the final slide with visible margin -- the top, left, and right edges of the slide (and any zone boundary) must never crop him. The ONLY edge allowed to crop the cutout is the slide's bottom edge, where his torso anchors naturally. If the sized cutout would cross the top or a side at the planned position, scale it down or move it -- never ship a slide with part of his head or arm sliced off.

**Verify after slicing:** face lands on the reserved panel, no headline/CTA text crosses his face, the amber glow reads behind him, no ghost edges of the empty placeholder panel peek out, and (seamless) the bleed on other boundaries is intact. Zoom to his outline at 200%: no white line around him, no blurry halo -- if either shows, re-run cutout_headshot.py (fresh pose) rather than shipping it.

### Seamless Mode (Default) — Slides Bleed Into Each Other

By default, do NOT generate one image per slide. Generate the deck as continuous panoramas and slice them: adjacent slides are literal pixel slices of one unbroken scene, so floating cards, amber glow, and the accent line cross the slide boundaries. When the viewer swipes, the other half of a card appears on the next slide — the carousel reads as one continuous picture with no visible seams.

Only use per-slide standalone generation when the user explicitly asks for isolated slides.

#### Group Planning (do this before writing prompts)

Split the deck into panorama groups. Slides are SQUARE (1:1), so value slides go in groups of 2 (generate 16:9; the slicer crops the height to 2:1 and cuts two squares). An odd value slide is generated standalone at 1:1 -- the uniform background keeps the seam invisible. The CTA slide is ALWAYS a standalone normal 1:1 generation (no floating UI card; carries a reserved right-side portrait panel for Rich's face -- see "Rich's Face").

| Total slides | Grouping |
|---|---|
| 5 | 2 + 2 + CTA |
| 6 | 2 + 2 + 1 + CTA |
| 7 | 2 + 2 + 2 + CTA |
| 8 | 2 + 2 + 2 + 1 + CTA |
| 9 | 2 + 2 + 2 + 2 + CTA |
| 10 | 2 + 2 + 2 + 2 + 1 + CTA |

Seams BETWEEN groups (and into the CTA) stay invisible because every image shares the same uniform `#080B14` background. Two rules guarantee it:

- Keep floating cards and glows away from the outer left and right edges of each panorama — the outer ~12% of each panorama is plain background
- The thin amber accent line must FADE OUT softly before reaching the panorama's outer edges, never hard-stop at them — a hard line meeting the next group at a slightly different height breaks the illusion

#### Panorama Prompt Construction

One JSON prompt file per group (`pano-01.json`, `pano-02.json`, ...), not per slide. Write ONE dense narrative describing a single continuous scene divided into N equal **invisible vertical zones** — one zone per slide:

- **Opening**: "One single ultra-wide continuous panoramic image, premium dark tech design, that will later be sliced vertically into [N] equal social media carousel slides. The entire panorama is ONE unbroken scene: no vertical divider lines, no borders, no frames, no visible panel edges anywhere."
- **Background**: "perfectly uniform deep near-black #080B14 with a subtle dark navy undertone, identical brightness across the full width, no vignette, no gradient falloff at the left or right edges"
- **Each zone gets ALL standard slide furniture**: large slide number in the top-left OF THAT ZONE (number only -- NO word-label above it), headline, bullets with golden-amber dash markers, and '@bishop_ai_' at the bottom center OF EACH ZONE (every sliced slide must keep the handle)
- **Bleed elements**: position each 3D floating card AT the boundary between two zones so half lands on each slide — "positioned so its right half extends across into the [next] zone, with a warm golden-amber #E0B848 glow radiating from behind the card and spilling smoothly across both zones". A thin golden-amber horizontal line flows through all zones at one consistent height, fading out before the outer edges.
- **Text safety**: "All text kept well inside its own zone with generous padding away from the zone boundaries; only the floating cards, glow and the horizontal amber line cross between zones." Only graphics cross the cut lines — never text.
- **Negative**: add "vertical divider lines, visible panel borders, frames, seams, vignette, word labels, category titles, website URLs" to the usual negatives

`api_parameters`: `"aspect_ratio": "16:9"` for 2-slide groups, `"resolution": "4K"` (mandatory — each slide only gets half of the panorama width), `"output_format": "jpg"`.

Because the slicer crops 16:9 down to 2:1 (about 5.5% off the top and bottom), every panorama prompt must state: all zone furniture (slide numbers, headlines, bullets, handle) sits within the central ~85% of the image height, with plain background in the top and bottom ~7%.

#### Proven Panorama Prompt Example (validated 3-slide group)

A validated example set (panorama prompt JSON, generated panorama, and the three sliced slides) lives at `C:\Users\richm\.claude\skills\carousel\references\seamless-example\` -- view it before your first seamless generation. NOTE: the example below is from the earlier 4:5 three-zone era -- use it for STYLE and narrative structure only. Current decks are square: write the same kind of prompt with TWO zones per panorama, and add the vertical-margin rule (furniture in the central ~85% of height).

```
One single ultra-wide continuous panoramic image, premium dark tech design, that will later be sliced vertically into three equal social media carousel slides. The entire panorama is ONE unbroken scene: no vertical divider lines, no borders, no frames, no visible panel edges anywhere. Background: perfectly uniform deep near-black #080B14 with a subtle dark navy undertone, identical brightness across the full width, no vignette, no gradient falloff at the left or right edges. A single thin golden-amber #E0B848 horizontal accent line flows continuously across the entire width of the panorama at the same height, tying the whole scene together. The composition has three equal invisible vertical zones. LEFT ZONE (hook): top-left corner of this zone has a large bold muted-white number '01' (number only, no word-label); below that, large ultra-bold white sans-serif headline text reading 'AI runs my whole pipeline' stacked on two lines; under it one line of medium-weight muted gray-white text reading 'Here is the exact system.' All of this hook text is kept on the LEFT half of the zone. On the RIGHT of this zone stands a tall dark rounded vertical portrait panel, completely plain and empty, taller than it is wide, with a soft warm golden-amber #E0B848 glow radiating from behind it, its right edge extending slightly into the middle zone; no text, no icons, nothing on this panel (a real headshot is composited over it later). MIDDLE ZONE: top-left corner of this zone has a large bold muted-white number '02' (number only, no word-label); ultra-bold white sans-serif headline reading 'Research on autopilot'; below it three short list items in muted gray-white text with golden-amber dash markers: 'Account briefs in minutes', 'Earnings calls summarized', 'Zero manual digging'. A 3D floating dark UI card showing a research dashboard with charts sits at the far right of this zone, tilted in perspective, its right edge crossing into the right zone, golden-amber glow behind it bleeding across the boundary. RIGHT ZONE: top-left corner of this zone has a large bold muted-white number '03' (number only, no word-label); ultra-bold white sans-serif headline reading 'Outreach that sounds human'; below it three short list items in muted gray-white text with golden-amber dash markers: 'Drafts in your voice', 'Follow-ups automated', 'You just hit send'. The golden-amber accent line ends with a soft glow near the right edge. At the bottom of EACH of the three zones, centered within that zone, small muted gray text reading '@bishop_ai_' so each future slide keeps the handle. All text kept well inside its own zone with generous padding away from the zone boundaries; only the floating cards, the portrait panel, glow and the horizontal amber line cross between zones. Cinematic, premium, clean dark aesthetic. Negative: vertical divider lines, visible panel borders, frames, seams, blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter, vignette.
```

#### Generate and Slice

1. Generate each panorama (note the panorama aspect ratio argument):

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py .\prompts\carousels\<carousel-name>\pano-01.json .\images\carousels\<carousel-name>\pano-01.jpg "16:9"
```

2. Slice each panorama into square slides. The 4th argument is the slide number of the FIRST panel, so numbering continues across groups (group 1 of 2 starts at 1, group 2 starts at 3, etc.):

```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\slice_panorama.py .\images\carousels\<carousel-name>\pano-01.jpg 2 .\images\carousels\<carousel-name> 1 "1:1"
```

The slicer center-crops the panorama to exactly N x 1:1 and cuts equal panels, so adjacent slides share the exact boundary pixels — the bleed is pixel-perfect by construction.

3. Generate the CTA (and any odd standalone value slide) as a normal standalone 1:1 slide.
4. Upload the sliced `slide-XX.jpg` files to Drive as usual — never upload the `pano-XX.jpg` files.
5. Build the LinkedIn PDF from the finished slides (see "LinkedIn PDF Version" below) and upload it alongside the JPGs.

If a panorama comes back with garbled text or a broken zone, regenerate the WHOLE group — never try to patch one zone.

---

### Slide-to-Image Prompt Construction (Standalone Mode)

Used for the CTA slide always, and for full decks only when the user asks for standalone slides. For each slide, create a JSON prompt file. Every prompt must produce a single, clean carousel card.

**IMPORTANT**: Write prompts as dense, descriptive narratives -- not templated fill-in-the-blanks. Each slide's prompt should be unique and describe its specific visual composition in detail. Use the proven examples below as your guide.

**Prompt structure (follow this order, but write as flowing narrative):**

```
Social media carousel slide, [ASPECT]. Premium dark tech design.
Background: deep near-black #080B14 with subtle dark navy undertone.
Top-left: large bold muted-white number '[N]' (number only -- NO word-label above or beside it).
[SLIDE-SPECIFIC VISUAL COMPOSITION -- describe the unique layout, 3D floating element, and text for this slide in detail. See examples below.]
Bottom center: small gray '@bishop_ai_' text.
Cinematic, premium dark aesthetic.
Negative: blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter.
```

**Key phrasing rules for prompts:**
- Say "Premium dark tech design" NOT "Bishop AI brand design"
- Say "ultra-bold white sans-serif" NOT "Poppins ExtraBold 72pt"
- Say "medium-weight muted gray-white text" for body copy
- Say "warm golden-amber #E0B848 glow radiating from behind the card"
- Say "3D floating dark UI card tilted in perspective" for the floating element
- Say "golden-amber dash markers" for bullet points
- Describe the floating card content specifically -- what interface is shown inside it
- EVERY prompt's negative list must include: "word labels, category titles, website URLs" (this is what stops the model drawing "HOOK"-style titles next to the slide number or a domain in the footer)

#### Proven Prompt Examples (from best-performing set)

**Hook slide (Slide 1):**
```
Social media carousel slide, square 1:1 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: large bold number '01' in muted white (number only, no word-label). On the LEFT side, large ultra-bold white sans-serif headline text reading 'Enterprise reps are losing deals' at 52pt, stacked. Below it, medium-weight muted gray text reading 'to AI-equipped competitors.' and smaller text 'and blaming it on pricing.' A thin golden-amber horizontal accent line below the headline text. On the RIGHT side stands a tall dark rounded vertical portrait panel, completely plain and empty, taller than it is wide, with a soft warm golden-amber #E0B848 glow radiating from behind it casting light onto the dark background; nothing on the panel (a real headshot is composited over it later). All headline text stays on the left half, clear of the panel. Bottom center: small gray '@bishop_ai_' text. Ultra-premium, cinematic, no clutter. Negative: blurry text, garbled typography, busy layouts, photorealistic faces, lens flare, cream or white backgrounds.
```

**Value slide with floating tool UI (Slide 2):**
```
Social media carousel slide, square 1:1 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: large bold number '02' in muted white (number only, no word-label). Right side: a 3D floating dark UI card tilted in perspective showing a Claude AI chat interface with context settings panel, with a warm golden-amber #E0B848 glow radiating from behind the card onto the dark background, card appears to hover with depth and subtle drop shadow. Left side text column: bold white ultra-heavy sans-serif headline 'Setting Up Your AI' at 48pt. Below, four small list items in muted gray-white text with golden-amber dash markers: 'Claude with your context', 'Expert prompts via PromptAnything', 'When to use which tool', 'Getting AI to sound like you'. Bottom center: small gray '@bishop_ai_' text. Cinematic, premium, clean dark aesthetic. Negative: blurry text, garbled typography, cream backgrounds, white backgrounds, photorealistic faces, busy clutter.
```

**Value slide with floating data UI (Slide 3):**
```
Social media carousel slide, square 1:1 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: large bold number '03' in muted white (number only, no word-label). Right side: a 3D floating dark UI card tilted in perspective showing a research dashboard with company data, financial figures and bullet points visible, with a warm golden-amber #E0B848 glow radiating from behind the card. Card appears to hover with depth and subtle shadow. Left side text: bold white ultra-heavy sans-serif headline 'Account Research & Targeting' at 44pt stacked. Below, four list items in muted gray-white text with golden-amber dash markers: 'Full account research in Perplexity', 'Lead list building with Manus', '10-Ks and earnings call analysis', 'Reusable account brief template'. Bottom center: small gray '@bishop_ai_' text. Cinematic, premium dark aesthetic. Negative: blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter.
```

**CTA slide (Final) -- TEXT ONLY, no floating card:**
```
Social media carousel slide, square 1:1 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. No floating UI cards, no UI mockups, no illustrations. Top-left: large bold number '08' in muted white (number only, no word-label). All text is LEFT-aligned in the left half with generous whitespace. Small muted gray text reading 'comment' near the top. Then bold ultra-heavy white sans-serif text reading 'AI Sales' at 64pt with a subtle warm golden-amber #E0B848 glow effect on the text itself and a soft ambient amber glow in the background behind the words. Below that, medium-weight muted gray text reading 'for early access.' A thin golden-amber horizontal line below. Below the line, small muted gray text reading 'Not selling for $15k. Even though we should.' On the RIGHT side stands a tall dark rounded vertical portrait panel, completely plain and empty, taller than it is wide, with a soft warm golden-amber #E0B848 glow radiating from behind it; nothing on the panel (a real headshot is composited over it later). All the CTA text stays on the left half, clear of the panel. Bottom center: small gray '@bishop_ai_' text. Cinematic, premium dark aesthetic, clean and minimal. Negative: blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter, floating UI cards, UI mockups, illustrations, images.
```

### Aspect Ratios

**All carousels are SQUARE (`1:1`) -- Instagram and LinkedIn both.** No 4:5, no exceptions unless the user explicitly asks for a different ratio.

| Platform | Ratio | Use |
|----------|-------|-----|
| Instagram carousel | `1:1` | Always |
| LinkedIn carousel | `1:1` | Always (image post AND the PDF document version) |

These are the FINAL slide ratios. In seamless mode the generation ratio differs (16:9 panoramas at 4K) and the slicer produces the final 1:1.

### LinkedIn PDF Version (Every Deck)

Every carousel also ships as a PDF so Rich can post it as a LinkedIn document post. After all slides are final (sliced, composited, verified), build it:

```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\make_pdf.py .\images\carousels\<carousel-name>
```

This writes `<carousel-name>-linkedin.pdf` in the slides folder (one full-bleed square page per slide, in order). Upload the PDF to Drive alongside the slide JPGs. Never build the PDF from panoramas or pre-composite slides -- final slides only.

### Execution

1. Create a `prompts/carousels/<carousel-name>/` directory
2. Seamless mode: save one JSON file per panorama group (`pano-01.json`, ...) plus `slide-XX.json` for the CTA. Standalone mode: one JSON file per slide: `slide-01.json`, `slide-02.json`, etc.

Each JSON file follows this structure:
```json
{
  "task": "carousel_slide_generation",
  "schema_version": "prism-2.0",
  "model_target": "nano-banana-2",
  "prompt": "<dense narrative prompt for this specific slide>",
  "api_parameters": {
    "aspect_ratio": "1:1",
    "resolution": "2K",
    "output_format": "jpg"
  }
}
```

3. Run generate_kie.py for each slide. Use the Agent tool to run slides in parallel (up to 4 at a time):

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py .\prompts\carousels\<carousel-name>\slide-01.json .\images\carousels\<carousel-name>\slide-01.jpg "1:1"
```

4. After all slides generate, upload each to Google Drive:

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\upload_gdrive.py .\images\carousels\<carousel-name>\slide-01.jpg
```

### Slide-Specific Prompt Tips

Each slide type should have a DISTINCT visual composition. Vary the layout across the set -- this is what makes the carousel feel hand-crafted, not templated.

| Slide Type | Prompt Emphasis |
|------------|----------------|
| **Hook (Slide 1)** | Warm off-white `#F9F6F0` background. Reserved right-side portrait panel for Rich's composited headshot (NOT a floating UI card). Bold white headline left side, stacked. Thin golden-amber accent line. Number ONLY top-left -- never a category/word label like "HOOK". |
| **Value slide (tool/process)** | Floating dark UI card showing the relevant tool interface (Claude, Perplexity, CRM, email builder, etc.) on right. Headline + bullet list with amber dashes on left. |
| **Value slide (workflow)** | Floating dark UI card showing a workflow diagram, pipeline board, or step sequence. Amber glow behind it. Headline + numbered steps on left. |
| **Value slide (comparison)** | Floating dark card showing two-column comparison or before/after inside it. Headline on left. Can skip the floating card and use two dark inline cards side by side instead. |
| **Value slide (data/stats)** | Floating dark UI card with dashboard or data visualization. Big stat or finding as headline on left. |
| **Tool/Resource List** | Floating dark card listing the tools as rows with icons. Headline on left explaining what the tools do. |
| **CTA (Final Slide)** | No floating UI card, no illustrations. Keyword (comment trigger) glows in golden-amber. Thin amber divider line. Text left-aligned, with a reserved right-side portrait panel for Rich's composited face. |

### Title Slide (Hook) Typography

The title slide's text must be deliberately FORMATTED, never a single blob of words:

- Break the headline into 2-3 short stacked lines and write the exact line breaks into the prompt ("stacked on two lines: 'AI runs my' / 'whole pipeline'") -- never leave line-wrapping to the model
- Clear hierarchy: big ultra-bold white headline, then ONE smaller muted gray-white subline. Nothing else -- no paragraphs, no bullets on the title slide
- Max ~6 words per headline line; generous padding between the headline block, the accent line, and the subline
- All title text on the LEFT half; Rich's composited headshot owns the right half (mandatory on every title slide -- same treatment as the thumbnails)

### Visual Consistency Rules

These are non-negotiable across all slides in a set:

- **Same warm off-white `#F9F6F0` background** on every slide (light is the default, see Visual Style Presets)
- **Same "ultra-bold white sans-serif" headline style** across all slides
- **Same golden-amber `#E0B848` glow** as the only accent color throughout
- **Square 1:1** on every slide, Instagram and LinkedIn alike -- plus the LinkedIn PDF built from the same slides
- **Slide number only** top-left on every slide (large number, NO word-label above or beside it). If a generated slide comes back with a word label ("HOOK", "STEP 1", garbled title text) next to the number, regenerate the group -- never ship it
- **`@bishop_ai_`** in muted gray at the bottom center of every slide -- and NEVER a website/domain (promptanything.io or any URL) anywhere on a slide
- **Title slide is formatted + carries Rich** -- stacked headline lines with explicit line breaks, one subline, and his composited headshot on the right (see "Title Slide (Hook) Typography")
- **Cutout quality** -- Rich's outline is a clean hard edge: no white fringe, no blurred halo, and he is never cropped by the top or sides of a slide (bottom-edge torso anchor only)
- **Varied 3D floating elements** -- each value slide shows a DIFFERENT UI interface, never the same card twice
- **Real screenshots stay real** -- screenshot-slide cards are composited from actual captures (capture_screenshot.py -> render_card.py -> composite_card.py), never redrawn by the image model
- **CTA slide** -- no floating UI card; keyword glows in amber, text left-aligned. Carries a reserved right-side portrait panel for Rich's composited face (see "Rich's Face")
- **Rich's face on Hook + CTA** -- slides 01 and the CTA reserve a right-side portrait panel that is covered after generation with a real transparent headshot cutout (cutout_headshot.py -> composite_card.py); text always stays on the opposite side so no words cross his face
- **Seamless mode**: floating cards sit ON the slide boundaries (half per slide), text never touches them, and panorama outer edges stay plain background so group seams are invisible

### Prerequisites

- `.env` file: Uses the one at `C:\Users\richm\.claude\skills\infographic-generator\.env`
- `generate_kie.py`: At `C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py`
- `upload_gdrive.py`: At `C:\Users\richm\.claude\skills\infographic-generator\scripts\upload_gdrive.py`
- `slice_panorama.py`: At `C:\Users\richm\.claude\skills\carousel\scripts\slice_panorama.py` (seamless mode; requires Pillow)
- `capture_screenshot.py`, `render_card.py`, `composite_card.py`: At `C:\Users\richm\.claude\skills\carousel\scripts\` (screenshot cards; require Playwright chromium -- `python -m playwright install chromium` if missing)
- Create output dirs if they don't exist: `images/carousels/<name>/` and `prompts/carousels/<name>/`
- If generate_kie.py fails with `SSL: CERTIFICATE_VERIFY_FAILED`, install the fix dependency: `pip install truststore --trusted-host pypi.org --trusted-host files.pythonhosted.org` (the script auto-uses it when present)

### Execution Workflow (Proven Pattern)

Follow this exact sequence every time. Do not improvise — these steps come from session-validated behavior.

**Step 1 — Write all JSON prompt files** using the Write tool. Do not use Bash or ctx_execute.

**Step 1.5 — Capture screenshot cards AND cut out Rich's faces.** While panoramas generate: (a) for any `[SCREENSHOT:]` slides run capture_screenshot.py + render_card.py; (b) run `cutout_headshot.py` twice to produce two transparent face PNGs (one for the hook, one for the CTA -- different poses). After panoramas land, run composite_card.py to lay the screenshot cards and the hook face onto the panorama, then continue with the composited files.

**Step 2 — Generate images in parallel.**

*Seamless mode (default):* there are only 2–3 panoramas plus the CTA slide. Run them in parallel with two Agent calls:
- Agent A: pano-01 and pano-02 (sequentially inside the agent)
- Agent B: pano-03 (if any) and the CTA slide

*Standalone mode:* two simultaneous Agent calls (do NOT run sequentially):
- Agent A: slides 1–4 (run generate_kie.py for each sequentially inside the agent)
- Agent B: slides 5–7 (same)

Both agents use working directory `C:\Users\richm\.claude` and report success/failure per slide.

**Step 2.5 — Composite the CTA face, then slice panoramas.** First composite Rich's CTA face onto the finished CTA slide with composite_card.py (the hook face was already composited onto the panorama in Step 1.5). Then run slice_panorama.py on each panorama (use the -comp.jpg composited version for panoramas that received screenshot cards or the hook face) with the correct starting slide number. View the sliced panels with the Read tool and check: no text cut at a panel edge, each panel has its number and handle, headlines legible, and on the hook slide Rich's face sits on its panel with no text crossing it. If a panorama fails these checks, regenerate that whole group.

**Step 3 — Check then upload** using ONE agent (not two). This agent:
1. Runs `PowerShell Get-Item` on every expected output file
2. Runs generate_kie.py for any that are MISSING (agent reports don't always reflect reality)
3. Uploads ALL final `slide-XX.jpg` files sequentially via upload_gdrive.py (in seamless mode: the sliced panels + CTA, never the pano files)
4. Returns the Drive link for every slide

Run this agent in the **background** (`run_in_background: true`) while you output captions or other content inline — do not wait.

**Step 4 — Post the Drive links** when the background agent notification fires.

### JSON Prompt Safety Rules

**Never use curly/smart quotes inside prompt strings.** Characters like `"word"` or `'word'` break JSON parsing. Use straight single quotes `'word'` only when quoting is unavoidable, or rephrase to avoid quoting entirely (e.g., `the word team in coral-red` instead of `"team"`).

**Always use `run_in_background: true`** for the upload agent so captions can be delivered immediately without blocking.

### Report Back

After generation, tell the user:
- Total slides generated (with local file paths)
- Google Drive links for each slide (from background agent notification)
- Which style preset was used
- Prompt directory (for iteration)
- Any slides that failed (offer to retry)


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
