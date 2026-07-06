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

**Banned words/phrases**: leverage, synergy, empower, optimize, utilize, facilitate, streamline, you won't believe, this one trick, mind-blowing, game-changer, limited time, act now, don't miss out, basically, essentially, literally, very, really

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

**All carousels use the Dark Mode AI style by default.** This is the proven style from the best-performing carousel sets. No other preset should be used unless the user explicitly requests it.

#### Dark Mode AI Style (Default -- Always Use)

This style is based on the proven "ai-enterprise-sales" carousel set. It uses a premium cinematic dark aesthetic with 3D floating UI elements and golden-amber glow accents.

| Element | Value |
|---------|-------|
| **Background** | Deep near-black `#080B14` with subtle dark navy undertone -- solid, consistent across all slides |
| **Primary Text** | White (headlines) -- use "ultra-bold white sans-serif" in prompts, never specific font names |
| **Body Text** | Muted gray-white -- use "medium-weight muted gray-white text" in prompts |
| **Primary Accent** | Golden-amber `#E0B848` -- glow effects on text, thin divider lines, bullet dash markers |
| **Slide Number** | Large bold muted-white number (e.g., "02") top-left, with tiny uppercase muted gray category label above it |
| **Handle** | `@bishop_ai_` small muted gray text at bottom center, every slide |
| **3D Floating Element** | Right-side 3D UI card tilted in perspective with golden-amber `#E0B848` glow radiating from behind it -- unique per slide, relevant to the slide topic |
| **CTA Slide** | Text only -- no floating card. Keyword glows in golden-amber. |

**CRITICAL: Never reference specific font names** (Poppins, Montserrat, Open Sans, etc.) in image generation prompts. Image gen models don't know fonts -- font names add noise and degrade output quality. Instead use descriptive terms: "ultra-bold white sans-serif", "medium-weight muted gray-white text", "small clean white monospace text".

#### Key Visual Elements (What Makes This Style Work)

1. **3D floating UI card**: Every value slide (2 through N-1) has a dark UI card on the RIGHT side, tilted in 3D perspective, showing an interface relevant to the slide topic (Claude chat, CRM dashboard, email sequence, workflow diagram, etc.). The card appears to hover with depth and a subtle drop shadow.
2. **Golden-amber glow**: A soft warm `#E0B848` glow radiates from BEHIND the floating card onto the dark background. This is the signature visual element -- it creates depth and makes the slide feel cinematic.
3. **Left-side text column**: Slide number + label top-left, headline, then bullet list with golden-amber dash markers. Text is LEFT-ALIGNED, not centered.
4. **Muted category label**: Above the slide number, a tiny uppercase muted gray label (e.g., "MODULE 1", "HOOK", "EARLY ACCESS") contextualizes the slide without competing with the headline.
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
Compute center_x/center_y against the POST-CROP dimensions, not the raw panorama: slice_panorama.py center-crops to exactly N x panel ratio (e.g. a 3-slide 4:5 group crops to 12:5, a 2-slide group to 8:5) before slicing. Work out the crop box first (same center-crop math: if the panorama is wider than N x ratio, width is cropped symmetrically; if taller, height is), place the card relative to that box, then convert back to raw-panorama pixels by adding the crop offset. Zone boundaries sit at crop_x0 + k * (cropped_width / N). For the common case (card on a boundary, vertically centered) this reduces to: center_x = crop_x0 + cropped_width * k / N, center_y = height // 2.

Then run slice_panorama.py on the composited file. In standalone mode, composite onto the individual slide image instead.

**Cookie banners / overlays:** if a consent banner or popup lands in the capture, re-capture with a CSS selector that targets the content region below/behind it (capture_screenshot.py's selector argument), or pick a deeper page URL without the overlay. Never ship a slide with a consent dialog visible.

**Prompt rule (placeholder-cover method -- session-validated):** do NOT ask for plain empty background where the real card will go; the model will not keep text out of a reserved empty area (validated failure, two attempts). Instead, prompt a placeholder the model manages itself: 'A medium-sized plain 3D floating dark card with a completely blank empty dark screen showing absolutely nothing sits at the far right of this zone, tilted in perspective, its right half crossing into the next zone, with a warm golden-amber #E0B848 glow radiating from behind it.' The model lays out all zone text around its own card. After generation, cover the placeholder with the real card: view the panorama, estimate the placeholder body's bbox and center, then composite with center on the placeholder's center and target_width sized so the opaque card (about 2/3 of the card PNG's width) covers the placeholder body with ~10% margin. Any drawn-glow remnants outside the cover blend into the real card's own glow -- only the placeholder's opaque body must be fully covered.

**Capture shape:** drawn placeholder cards come out portrait, so capture the target at a mobile portrait viewport (capture_screenshot.py viewport args: 430 660 for ~3:2 cards, 430 860 for ~2:1) -- mobile screenshots cover them naturally and read great at slide size. Landscape desktop captures cannot cover a portrait placeholder without colliding with neighboring text.

**Group shape:** prefer 21:9 three-zone groups even when it means adding a value slide to the deck -- 16:9 two-zone groups get ~5% cropped off each side by the slicer and edge text gets cut (validated failure).

**Verify after slicing:** screenshot text legible, card tilt/glow matches neighboring generated cards, bleed intact across the boundary, no zone furniture covered, no ghost edges of the placeholder card peeking out from behind the real one.

**Fallback:** if a target needs a login you cannot reach or will not render, use a generated card for that slide or ask Rich for a manual capture.

### Seamless Mode (Default) — Slides Bleed Into Each Other

By default, do NOT generate one image per slide. Generate the deck as continuous panoramas and slice them: adjacent slides are literal pixel slices of one unbroken scene, so floating cards, amber glow, and the accent line cross the slide boundaries. When the viewer swipes, the other half of a card appears on the next slide — the carousel reads as one continuous picture with no visible seams.

Only use per-slide standalone generation when the user explicitly asks for isolated slides.

#### Group Planning (do this before writing prompts)

Split the deck into panorama groups. Value slides go in groups of 3 (generate 21:9) or 2 (generate 16:9). The CTA slide is ALWAYS a standalone normal 4:5 generation (text-only rules unchanged).

| Total slides | Grouping |
|---|---|
| 5 | 2 + 2 + CTA |
| 6 | 3 + 2 + CTA |
| 7 | 3 + 3 + CTA |
| 8 | 3 + 2 + 2 + CTA |
| 9 | 3 + 3 + 2 + CTA |
| 10 | 3 + 3 + 3 + CTA |

Seams BETWEEN groups (and into the CTA) stay invisible because every image shares the same uniform `#080B14` background. Two rules guarantee it:

- Keep floating cards and glows away from the outer left and right edges of each panorama — the outer ~12% of each panorama is plain background
- The thin amber accent line must FADE OUT softly before reaching the panorama's outer edges, never hard-stop at them — a hard line meeting the next group at a slightly different height breaks the illusion

#### Panorama Prompt Construction

One JSON prompt file per group (`pano-01.json`, `pano-02.json`, ...), not per slide. Write ONE dense narrative describing a single continuous scene divided into N equal **invisible vertical zones** — one zone per slide:

- **Opening**: "One single ultra-wide continuous panoramic image, premium dark tech design, that will later be sliced vertically into [N] equal social media carousel slides. The entire panorama is ONE unbroken scene: no vertical divider lines, no borders, no frames, no visible panel edges anywhere."
- **Background**: "perfectly uniform deep near-black #080B14 with a subtle dark navy undertone, identical brightness across the full width, no vignette, no gradient falloff at the left or right edges"
- **Each zone gets ALL standard slide furniture**: tiny uppercase category label + large slide number in the top-left OF THAT ZONE, headline, bullets with golden-amber dash markers, and '@bishop_ai_' at the bottom center OF EACH ZONE (every sliced slide must keep the handle)
- **Bleed elements**: position each 3D floating card AT the boundary between two zones so half lands on each slide — "positioned so its right half extends across into the [next] zone, with a warm golden-amber #E0B848 glow radiating from behind the card and spilling smoothly across both zones". A thin golden-amber horizontal line flows through all zones at one consistent height, fading out before the outer edges.
- **Text safety**: "All text kept well inside its own zone with generous padding away from the zone boundaries; only the floating cards, glow and the horizontal amber line cross between zones." Only graphics cross the cut lines — never text.
- **Negative**: add "vertical divider lines, visible panel borders, frames, seams, vignette" to the usual negatives

`api_parameters`: `"aspect_ratio": "21:9"` for 3-slide groups, `"16:9"` for 2-slide groups, `"resolution": "4K"` (mandatory — each slide only gets 1/N of the panorama width), `"output_format": "jpg"`.

For 1:1 Instagram-only sets, use groups of 2 max (generate 21:9, the slicer crops to 2:1). Default 4:5 works for both platforms and supports groups of 3 — prefer it.

#### Proven Panorama Prompt Example (validated 3-slide group)

A validated example set (panorama prompt JSON, generated panorama, and the three sliced slides) lives at `C:\Users\richm\.claude\skills\carousel\references\seamless-example\` -- view it before your first seamless generation.

```
One single ultra-wide continuous panoramic image, premium dark tech design, that will later be sliced vertically into three equal social media carousel slides. The entire panorama is ONE unbroken scene: no vertical divider lines, no borders, no frames, no visible panel edges anywhere. Background: perfectly uniform deep near-black #080B14 with a subtle dark navy undertone, identical brightness across the full width, no vignette, no gradient falloff at the left or right edges. A single thin golden-amber #E0B848 horizontal accent line flows continuously across the entire width of the panorama at the same height, tying the whole scene together. The composition has three equal invisible vertical zones. LEFT ZONE: top-left corner of this zone has a tiny uppercase muted gray label 'HOOK' with a large bold muted-white number '01' below it; below that, large ultra-bold white sans-serif headline text reading 'AI runs my whole pipeline' stacked on two lines; under it one line of medium-weight muted gray-white text reading 'Here is the exact system.' A large 3D floating dark UI card showing a chat interface with prompt and response sits at the far right of this zone, tilted in perspective, positioned so its right half extends across into the middle zone, with a warm golden-amber #E0B848 glow radiating from behind the card and spilling smoothly across both zones. MIDDLE ZONE: top-left corner of this zone has a tiny uppercase muted gray label 'STEP 1' with a large bold muted-white number '02' below it; ultra-bold white sans-serif headline reading 'Research on autopilot'; below it three short list items in muted gray-white text with golden-amber dash markers: 'Account briefs in minutes', 'Earnings calls summarized', 'Zero manual digging'. A second 3D floating dark UI card showing a research dashboard with charts sits at the far right of this zone, tilted in perspective, its right edge crossing into the right zone, golden-amber glow behind it bleeding across the boundary. RIGHT ZONE: top-left corner of this zone has a tiny uppercase muted gray label 'STEP 2' with a large bold muted-white number '03' below it; ultra-bold white sans-serif headline reading 'Outreach that sounds human'; below it three short list items in muted gray-white text with golden-amber dash markers: 'Drafts in your voice', 'Follow-ups automated', 'You just hit send'. The golden-amber accent line ends with a soft glow near the right edge. At the bottom of EACH of the three zones, centered within that zone, small muted gray text reading '@bishop_ai_' so each future slide keeps the handle. All text kept well inside its own zone with generous padding away from the zone boundaries; only the floating cards, glow and the horizontal amber line cross between zones. Cinematic, premium, clean dark aesthetic. Negative: vertical divider lines, visible panel borders, frames, seams, blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter, vignette.
```

#### Generate and Slice

1. Generate each panorama (note the panorama aspect ratio argument):

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py .\prompts\carousels\<carousel-name>\pano-01.json .\images\carousels\<carousel-name>\pano-01.jpg "21:9"
```

2. Slice each panorama into 4:5 slides. The 4th argument is the slide number of the FIRST panel, so numbering continues across groups (group 1 of 3 starts at 1, group 2 starts at 4, etc.):

```powershell
python C:\Users\richm\.claude\skills\carousel\scripts\slice_panorama.py .\images\carousels\<carousel-name>\pano-01.jpg 3 .\images\carousels\<carousel-name> 1 "4:5"
```

The slicer center-crops the panorama to exactly N x 4:5 and cuts equal panels, so adjacent slides share the exact boundary pixels — the bleed is pixel-perfect by construction.

3. Generate the CTA as a normal standalone 4:5 slide (text-only, keyword glow, unchanged).
4. Upload the sliced `slide-XX.jpg` files to Drive as usual — never upload the `pano-XX.jpg` files.

If a panorama comes back with garbled text or a broken zone, regenerate the WHOLE group — never try to patch one zone.

---

### Slide-to-Image Prompt Construction (Standalone Mode)

Used for the CTA slide always, and for full decks only when the user asks for standalone slides. For each slide, create a JSON prompt file. Every prompt must produce a single, clean carousel card.

**IMPORTANT**: Write prompts as dense, descriptive narratives -- not templated fill-in-the-blanks. Each slide's prompt should be unique and describe its specific visual composition in detail. Use the proven examples below as your guide.

**Prompt structure (follow this order, but write as flowing narrative):**

```
Social media carousel slide, [ASPECT]. Premium dark tech design.
Background: deep near-black #080B14 with subtle dark navy undertone.
Top-left: tiny uppercase muted gray label '[CATEGORY]' with large bold muted-white number '[N]' below it.
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

#### Proven Prompt Examples (from best-performing set)

**Hook slide (Slide 1):**
```
Social media carousel slide, 4:5 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: tiny uppercase muted gray label 'HOOK' with large bold number '01' below it in muted white. A large 3D floating UI card hovering in the center-right of the slide, tilted slightly in 3D perspective, showing a dark chat interface with a text prompt and AI response, with a soft warm golden-amber #E0B848 glow emanating from behind the card casting light onto the dark background. The card has depth, subtle shadow, and appears to float. On the left side, large ultra-bold white sans-serif headline text reading 'Enterprise reps are losing deals' at 52pt, stacked. Below it, medium-weight muted gray text reading 'to AI-equipped competitors.' and smaller text 'and blaming it on pricing.' A thin golden-amber horizontal accent line below the headline text. Bottom center: small gray '@bishop_ai_' text. Ultra-premium, cinematic, no clutter. Negative: blurry text, garbled typography, busy layouts, photorealistic faces, lens flare, cream or white backgrounds.
```

**Value slide with floating tool UI (Slide 2):**
```
Social media carousel slide, 4:5 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: tiny uppercase muted gray label 'MODULE 1' with large bold number '02' below it in muted white. Right side: a 3D floating dark UI card tilted in perspective showing a Claude AI chat interface with context settings panel, with a warm golden-amber #E0B848 glow radiating from behind the card onto the dark background, card appears to hover with depth and subtle drop shadow. Left side text column: bold white ultra-heavy sans-serif headline 'Setting Up Your AI' at 48pt. Below, four small list items in muted gray-white text with golden-amber dash markers: 'Claude with your context', 'Expert prompts via PromptAnything', 'When to use which tool', 'Getting AI to sound like you'. Bottom center: small gray '@bishop_ai_' text. Cinematic, premium, clean dark aesthetic. Negative: blurry text, garbled typography, cream backgrounds, white backgrounds, photorealistic faces, busy clutter.
```

**Value slide with floating data UI (Slide 3):**
```
Social media carousel slide, 4:5 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. Top-left: tiny uppercase muted gray label 'MODULE 2' with large bold number '03' below it in muted white. Right side: a 3D floating dark UI card tilted in perspective showing a research dashboard with company data, financial figures and bullet points visible, with a warm golden-amber #E0B848 glow radiating from behind the card. Card appears to hover with depth and subtle shadow. Left side text: bold white ultra-heavy sans-serif headline 'Account Research & Targeting' at 44pt stacked. Below, four list items in muted gray-white text with golden-amber dash markers: 'Full account research in Perplexity', 'Lead list building with Manus', '10-Ks and earnings call analysis', 'Reusable account brief template'. Bottom center: small gray '@bishop_ai_' text. Cinematic, premium dark aesthetic. Negative: blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter.
```

**CTA slide (Final) -- TEXT ONLY, no floating card:**
```
Social media carousel slide, 4:5 aspect ratio. Premium dark tech design. Background: deep near-black #080B14 with subtle dark navy undertone. No floating cards, no UI mockups, no illustrations -- text only. Top-left: tiny uppercase muted gray label 'EARLY ACCESS' with large bold number '08' below it in muted white. Left-aligned text layout with generous whitespace. Small muted gray text reading 'comment' near the top. Then bold ultra-heavy white sans-serif text reading 'AI Sales' at 64pt with a subtle warm golden-amber #E0B848 glow effect on the text itself and a soft ambient amber glow in the background behind the words. Below that, medium-weight muted gray text reading 'for early access.' A thin golden-amber horizontal line below. Below the line, small muted gray text reading 'Not selling for $15k. Even though we should.' Bottom center: small gray '@bishop_ai_' text. Cinematic, premium dark aesthetic, clean and minimal. Negative: blurry text, garbled typography, cream or white backgrounds, photorealistic faces, busy clutter, floating cards, UI mockups, illustrations, images.
```

### Aspect Ratios

| Platform | Ratio | Use |
|----------|-------|-----|
| Instagram carousel | `1:1` | Default for IG |
| LinkedIn carousel | `4:5` | Default for LinkedIn |
| Both platforms | `4:5` | Safe for both |

These are the FINAL slide ratios. In seamless mode the generation ratio differs (21:9 or 16:9 panoramas at 4K) and the slicer produces the final ratio.

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
    "aspect_ratio": "4:5",
    "resolution": "2K",
    "output_format": "jpg"
  }
}
```

3. Run generate_kie.py for each slide. Use the Agent tool to run slides in parallel (up to 4 at a time):

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py .\prompts\carousels\<carousel-name>\slide-01.json .\images\carousels\<carousel-name>\slide-01.jpg "4:5"
```

4. After all slides generate, upload each to Google Drive:

```powershell
python C:\Users\richm\.claude\skills\infographic-generator\scripts\upload_gdrive.py .\images\carousels\<carousel-name>\slide-01.jpg
```

### Slide-Specific Prompt Tips

Each slide type should have a DISTINCT visual composition. Vary the layout across the set -- this is what makes the carousel feel hand-crafted, not templated.

| Slide Type | Prompt Emphasis |
|------------|----------------|
| **Hook (Slide 1)** | Dark `#080B14` background. 3D floating UI card right side with amber glow. Bold white headline left side, stacked. Thin golden-amber accent line. Category label + number top-left. |
| **Value slide (tool/process)** | Floating dark UI card showing the relevant tool interface (Claude, Perplexity, CRM, email builder, etc.) on right. Headline + bullet list with amber dashes on left. |
| **Value slide (workflow)** | Floating dark UI card showing a workflow diagram, pipeline board, or step sequence. Amber glow behind it. Headline + numbered steps on left. |
| **Value slide (comparison)** | Floating dark card showing two-column comparison or before/after inside it. Headline on left. Can skip the floating card and use two dark inline cards side by side instead. |
| **Value slide (data/stats)** | Floating dark UI card with dashboard or data visualization. Big stat or finding as headline on left. |
| **Tool/Resource List** | Floating dark card listing the tools as rows with icons. Headline on left explaining what the tools do. |
| **CTA (Final Slide)** | TEXT ONLY -- no floating card, no illustrations. Keyword (comment trigger) glows in golden-amber. Thin amber divider line. Left-aligned. |

### Visual Consistency Rules

These are non-negotiable across all slides in a set:

- **Same deep near-black `#080B14` background** on every slide
- **Same "ultra-bold white sans-serif" headline style** across all slides
- **Same golden-amber `#E0B848` glow** as the only accent color throughout
- **Slide number + category label** top-left on every slide (number large, label tiny uppercase above it)
- **`@bishop_ai_`** in muted gray at the bottom center of every slide
- **Varied 3D floating elements** -- each value slide shows a DIFFERENT UI interface, never the same card twice
- **Real screenshots stay real** -- screenshot-slide cards are composited from actual captures (capture_screenshot.py -> render_card.py -> composite_card.py), never redrawn by the image model
- **CTA slide is always text-only** -- no floating card, keyword glows in amber
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

**Step 1.5 — Capture and render screenshot cards (if any `[SCREENSHOT:]` slides).** While panoramas generate, run capture_screenshot.py + render_card.py for each screenshot slide. After panoramas land, run composite_card.py on each affected panorama, then continue with the composited files.

**Step 2 — Generate images in parallel.**

*Seamless mode (default):* there are only 2–3 panoramas plus the CTA slide. Run them in parallel with two Agent calls:
- Agent A: pano-01 and pano-02 (sequentially inside the agent)
- Agent B: pano-03 (if any) and the CTA slide

*Standalone mode:* two simultaneous Agent calls (do NOT run sequentially):
- Agent A: slides 1–4 (run generate_kie.py for each sequentially inside the agent)
- Agent B: slides 5–7 (same)

Both agents use working directory `C:\Users\richm\.claude` and report success/failure per slide.

**Step 2.5 — Slice panoramas (seamless mode only).** Run slice_panorama.py on each panorama (use the -comp.jpg composited version for panoramas that received screenshot cards) with the correct starting slide number. Then view the sliced panels with the Read tool and check: no text cut at a panel edge, each panel has its number and handle, headlines legible. If a panorama fails these checks, regenerate that whole group.

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
