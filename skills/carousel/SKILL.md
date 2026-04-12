---
name: carousel
description: Generates complete, slide-by-slide social media carousel content AND images for Instagram and LinkedIn using the CAROUSEL Framework + KIE AI pipeline. Use this skill whenever the user wants to create a carousel post, needs slide content for Instagram or LinkedIn, wants to turn a topic or piece of content into a swipeable carousel, asks for carousel copy or structure, or says things like "make me a carousel about X", "write carousel slides for Y", "help me create a LinkedIn carousel", "turn this into a carousel", or "I need carousel content". Generates actual slide images via KIE AI -- not just text. Always trigger for carousel creation even if the user only mentions a topic and platform -- infer the rest.
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

After finalizing slide content, generate an actual image for each slide using the KIE AI pipeline.

### Visual Style Presets

**All carousels use the Bishop AI Editorial style by default.** This is the proven style from the best-performing carousel sets. No other preset should be used unless the user explicitly requests it.

#### Bishop AI Editorial Style (Default -- Always Use)

This style is based on the proven "claude-code-vscode-tips" carousel set. It uses a warm, premium editorial aesthetic with hand-painted brush-stroke accents and varied per-slide compositions.

| Element | Value |
|---------|-------|
| **Background** | Warm cream off-white `#F5F0E8` -- solid, consistent across all slides |
| **Primary Text** | Black (headlines) -- use "bold black sans-serif" in prompts, never specific font names |
| **Body Text** | Medium-weight black or dark gray -- use "medium-weight black text" in prompts |
| **Primary Accent** | Golden-amber `#D4A853` -- brush-stroke highlights behind key words (like a hand-painted marker swipe) |
| **Secondary Accent** | Coral-red -- circled step numbers, bullet markers, label text for categories (e.g., "BAD PROMPT" / "GOOD PROMPT") |
| **Step Numbers** | Large coral-red circled numbers (e.g., circled 1, circled 2) as decorative elements above headlines on value slides |
| **Slide Counter** | Small muted gray text in top-right corner (e.g., "3/8") |
| **Handle** | `@bishop_ai_` small muted gray text at bottom center, every slide |
| **Illustrations** | Minimal thin-line black outline illustrations relevant to the slide topic |
| **Cards/Boxes** | Dark background cards with cream/gold borders for code snippets, prompts, or examples |

**CRITICAL: Never reference specific font names** (Poppins, Montserrat, Open Sans, etc.) in image generation prompts. Image gen models don't know fonts -- font names add noise and degrade output quality. Instead use descriptive terms: "ultra-bold black sans-serif", "medium-weight black text", "small clean white monospace text".

#### Key Visual Elements (What Makes This Style Work)

1. **Brush-stroke highlights**: Key words in headlines get a soft golden-amber `#D4A853` brush-stroke highlight behind them -- described as "like a hand-painted marker swipe". This is the signature visual element.
2. **Coral-red circled numbers**: Value slides (2 through N-1) use a large coral-red circled number above the headline as a step indicator. Much more engaging than text labels like "STEP 01".
3. **Varied compositions per slide**: Each slide should have a DIFFERENT layout/visual element. Mix and match from: comparison cards, dark code boxes, bullet lists with coral markers, thin-line illustrations, side-by-side columns, checkmark lists. Monotonous slides kill engagement.
4. **Dark content cards**: When showing examples, prompts, or code, use dark background cards (`#1A1A1A` or similar) with cream or gold borders. White monospace text inside.
5. **Generous whitespace**: Let the content breathe. No decorative clutter, no busy backgrounds, no gradients.
6. **No progress bars**: The circled step numbers and slide counter handle navigation. No gold segmented progress bars.

#### Alternate Presets (Only When User Explicitly Requests)

| Preset | Background | Text Color | Accent | Best For |
|--------|-----------|------------|--------|----------|
| **Dark Professional** | Near-black `#0A0A0A` | White `#FFFFFF` | Orange `#FF6B35` or blue `#4A9FD9` | Tech, tools, comparisons |
| **Bold Minimal** | White `#FFFFFF` | Black `#000000` | Red-coral `#E8453C` accent | Hooks, contrarian takes, CTAs |
| **Notebook/Sketch** | Grid paper `#F8F6F0` with faint lines | Dark gray `#2D2D2D` | Watercolor-style brush highlights | Story arcs, personal insights |

### Slide-to-Image Prompt Construction

For each slide, create a JSON prompt file. Every prompt must produce a single, clean carousel card.

**IMPORTANT**: Write prompts as dense, descriptive narratives -- not templated fill-in-the-blanks. Each slide's prompt should be unique and describe its specific visual composition in detail. Use the proven examples below as your guide.

**Prompt structure (follow this order, but write as flowing narrative):**

```
Social media carousel slide, [ASPECT]. Clean editorial design.
Background: solid warm cream off-white #F5F0E8.
In the top-right corner, small text reading '[N/TOTAL]' in muted gray.
[SLIDE-SPECIFIC VISUAL COMPOSITION -- describe the unique layout, elements, and text for this slide in detail. See examples below.]
Small text '@bishop_ai_' in muted gray at the bottom center.
Ultra-clean, minimal, maximum whitespace.
Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter, multiple fonts, colorful backgrounds.
```

**Key phrasing rules for prompts:**
- Say "Clean editorial design" NOT "Bishop AI brand design"
- Say "bold black sans-serif headline text" NOT "Poppins ExtraBold 72pt"
- Say "medium-weight black text" NOT "Open Sans Regular 24pt"
- Say "soft golden-amber #D4A853 brush-stroke highlight behind [words], like a hand-painted marker swipe"
- Say "large coral-red circled number [N]" for step indicators
- Describe visual elements specifically: "dark card-style box with cream border", "thin-line illustration of [X] in black outlines"

#### Proven Prompt Examples (from best-performing set)

**Hook slide (Slide 1):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '1/8' in muted gray. Centered layout with generous whitespace. Large ultra-bold black sans-serif headline text reading '7 Claude Code Tips' at 64pt size, perfectly centered horizontally in the upper-middle area. Below it, a second line in elegant medium-weight black text reading 'That Cut My Build Time in Half' at 32pt. The words 'Claude Code' have a soft golden-amber #D4A853 brush-stroke highlight behind them, like a hand-painted marker swipe. Below the text, a minimal line illustration of a code editor window outline in thin black strokes. Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, minimal, no clutter. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter, multiple fonts, colorful backgrounds.
```

**Value slide with illustration (Slide 2):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '2/8' in muted gray. Top section has a large coral-red circled number '1' as a decorative element. Below it, bold black sans-serif headline text reading 'Screenshot, Don't Describe' at 56pt, centered. The word 'Screenshot' has a soft golden-amber #D4A853 brush-stroke highlight behind it. Below, smaller medium-weight black text at 24pt reading 'Drag a screenshot into Claude Code.' on one line and 'It rebuilds what it sees.' on the next line. A minimal thin-line illustration of a browser screenshot being dragged into a code editor, simple black outlines only. Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, minimal, maximum whitespace. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter.
```

**Value slide with comparison cards (Slide 3):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '3/8' in muted gray. Top section has a large coral-red circled number '2' as a decorative element. Below it, bold black sans-serif headline text reading 'Describe the End Result' at 56pt, centered. The words 'End Result' have a soft golden-amber #D4A853 brush-stroke highlight behind them. Below the headline, two small card-style boxes side by side. Left card labeled 'BAD PROMPT' in small red text with dark background card containing the text 'Create an HTML file, add CSS, use flexbox for layout, make it responsive...' in small white text. Right card labeled 'GOOD PROMPT' in small green text with dark background card containing 'I want a clean landing page. Big headline, 4 services, footer with my socials.' in small white text. Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, editorial. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter.
```

**Value slide with dark code box + bullets (Slide 4):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '4/8' in muted gray. Top section has a large coral-red circled number '3' as a decorative element. Below it, bold black sans-serif headline text reading 'Point Claude to Your Files' at 56pt, centered. The word 'Your Files' has a soft golden-amber #D4A853 brush-stroke highlight behind it. Below, a dark card-style box with cream border containing the text 'Read the files in my project folder. Use my tone and style for the website copy.' in small clean white monospace text, styled like a code prompt. Below the card, two small bullet points with coral-red dot markers: 'Brand guidelines or style docs' and 'Existing code files for reference'. Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, minimal. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter.
```

**Value slide with checklist (Slide 5):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '5/8' in muted gray. Top section has a large coral-red circled number '4' as a decorative element. Below it, bold black sans-serif headline text reading 'One Feature Per Prompt' at 56pt, centered. The words 'One Feature' have a soft golden-amber #D4A853 brush-stroke highlight behind them. Below, three checklist items each with a coral-red checkmark icon: 'Start with the homepage. Get it right.' then 'Then add the contact page.' then 'Then the blog section.' Smaller muted text at bottom: 'Pro-tip: Small, focused prompts give Claude less room to break things that already work.' Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, minimal. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter.
```

**CTA slide (Final):**
```
Social media carousel slide, 4:5 aspect ratio. Clean editorial design. Background: solid warm cream off-white #F5F0E8. In the top-right corner, small text reading '8/8' in muted gray. Centered layout. Large ultra-bold black sans-serif headline reading 'Want the Full Prompt Library?' at 56pt centered. The words 'Prompt Library' have a soft golden-amber #D4A853 brush-stroke highlight behind them. A thin horizontal divider line below. Below the divider, medium-weight black text reading 'Join AI Builders on Skool' with 'AI Builders' in coral-red. Below that, small muted text 'Link in bio' with a small arrow icon. Small text '@bishop_ai_' in muted gray at the bottom center. Ultra-clean, bold, minimal. Negative: blurry text, garbled typography, illegible fonts, busy layouts, stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, decorative clutter.
```

### Aspect Ratios

| Platform | Ratio | Use |
|----------|-------|-----|
| Instagram carousel | `1:1` | Default for IG |
| LinkedIn carousel | `4:5` | Default for LinkedIn |
| Both platforms | `4:5` | Safe for both |

### Execution

1. Create a `prompts/carousels/<carousel-name>/` directory
2. Save one JSON file per slide: `slide-01.json`, `slide-02.json`, etc.

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
| **Hook (Slide 1)** | Biggest, boldest text. Centered layout. Brush-stroke highlight on key words. Minimal thin-line illustration below text. No circled number on hook slides. |
| **Value slide (simple)** | Coral-red circled number above headline. Brush-stroke highlight on 1-2 key words. Body text below. Optional thin-line illustration. |
| **Value slide (comparison)** | Coral-red circled number. Two side-by-side dark cards with colored labels (red = bad, green = good). |
| **Value slide (code/example)** | Coral-red circled number. Dark card-style box with cream/gold border containing white monospace text. Bullet points with coral markers below. |
| **Value slide (checklist)** | Coral-red circled number. Checklist items with coral-red checkmark icons. Optional pro-tip in smaller muted text at bottom. |
| **Value slide (before/after)** | Coral-red circled number. Two thin-line illustrations side by side with arrow between, X mark on left, checkmark on right. Explanatory text below. |
| **Tool/Resource List** | Each tool gets its own row: logo on left, name + one-line description on right. Dark card-style rows. |
| **CTA (Final Slide)** | No circled number. Centered, large ultra-bold text. Brush-stroke highlight on key phrase. Thin horizontal divider. CTA action in coral-red. |

### Visual Consistency Rules

These are non-negotiable across all slides in a set:

- **Same warm cream `#F5F0E8` background** on every slide
- **Same "bold black sans-serif" headline style** across all slides
- **Same golden-amber `#D4A853` brush-stroke highlight** treatment throughout
- **Same coral-red accent** for circled numbers, markers, and labels
- **Slide number indicator** (e.g., "3/8") in the top-right corner of every slide
- **`@bishop_ai_`** in muted gray at the bottom center of every slide
- **Varied compositions** -- each slide should use a different visual element (illustration, cards, checklist, comparison, etc.)

### Prerequisites

- `.env` file: Uses the one at `C:\Users\richm\.claude\skills\infographic-generator\.env`
- `generate_kie.py`: At `C:\Users\richm\.claude\skills\infographic-generator\scripts\generate_kie.py`
- `upload_gdrive.py`: At `C:\Users\richm\.claude\skills\infographic-generator\scripts\upload_gdrive.py`
- Create output dirs if they don't exist: `images/carousels/<name>/` and `prompts/carousels/<name>/`

### Report Back

After generation, tell the user:
- Total slides generated (with local file paths)
- Google Drive links for each slide
- Which style preset was used
- Prompt directory (for iteration)
- Any slides that failed (offer to retry)
