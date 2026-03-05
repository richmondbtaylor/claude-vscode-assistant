---
name: captivate
description: "Two modes in one skill. Mode 1 — Content Repurposing: takes existing content (YouTube URLs, podcast episodes, webinars, LinkedIn posts, transcript files, slide images) and transforms it into ready-to-publish social assets — LinkedIn posts, YouTube captions, Shorts scripts, carousel outlines, quote cards, stat graphics, timestamps, teaser clip recommendations. Mode 2 — Automation Nation Script Writing: writes original, production-ready video scripts for Rich's YouTube channel using his voice, brand, and a scene-by-scene format with visual direction. Applies AIDA/PAS/FAB/BAB frameworks and enforces brand voice. Trigger Mode 1 on: 'process this video', 'make a LinkedIn post from this', 'create content from', 'extract clips', 'repurpose this episode', 'timestamps for this video'. Trigger Mode 2 on: 'write a script for', 'I want to make a video about', 'script this', 'Automation Nation video', 'help me write a video'."
---

# CAPTIVATE Framework

Turn your existing content into multi-platform social media assets. One source, many outputs — with consistent brand voice across all of them.

## Supported Inputs

- **YouTube URL** — extract transcript/captions, metadata, thumbnail
- **LinkedIn post URL** — extract text, engagement data, author info
- **Podcast episode URL** — retrieve transcript, show notes, episode metadata
- **Webinar recording URL** — extract transcript, slide content, speaker info
- **Transcript file** — plain text, SRT (with timestamps), YouTube auto-captions
- **Images** — slide decks, infographics, screenshots (OCR for text extraction)

## Execution Flow

Walk through these steps for every request:

### 1. Acquire Content

Extract all available raw material from the input:
- Full transcript with timestamps (if available)
- Metadata: title, author, date, duration
- Visual assets: thumbnails, slides, embedded images
- Engagement data: views, likes, comments (if accessible)

If a URL is inaccessible, log the error with URL and timestamp and ask for an alternative (transcript file, different URL, or pasted text). Don't silently skip it.

### 2. Process Content

Clean and tag the raw transcript before transforming anything:

**Remove:** um, uh, like, you know, basically, essentially, generally, very, really, off-topic tangents, competitor mentions, personal information (phone numbers, emails, addresses)

**Tag extracted content by type:**
- `[HOOK]` — strong opening statements, surprising facts, bold claims
- `[INSIGHT]` — actionable takeaways with clear application
- `[METRIC]` — specific numbers, percentages, results with context
- `[QUOTE]` — verbatim statements worth attributing to the speaker
- `[CASE STUDY]` — real examples with before/after structure
- `[FRAMEWORK]` — named processes, steps, or systems
- `[CTA]` — calls-to-action

Preserve exact wording for `[QUOTE]` and `[METRIC]` tags — paraphrasing breaks accuracy.

**Timing:** Complete processing within 90 seconds for transcripts under 10,000 words; within 3 minutes for longer content.

### 3. Transform Content

Generate the requested asset types. See `references/platform-specs.md` for exact format requirements per platform.

Apply copywriting frameworks from `references/brand-voice.md` to structure content. Choose the framework based on the goal:
- Building awareness → **AIDA**
- Selling or converting → **PAS**
- Showcasing benefits → **FAB**
- Before/after stories → **BAB**

### 4. Validate Outputs

Before delivering any asset, run these checks:

- **Grammar and spelling** — must be perfect, zero errors
- **Fact accuracy** — all claims and stats verified against source material; flag anything unverifiable
- **Brand voice** — matches approved tone, uses approved terms, avoids banned terms (see `references/brand-voice.md`)
- **Filler words** — none in final copy
- **Platform requirements** — word counts, formatting, hashtag limits met

If critical issues are found (factual errors, brand misalignment, missing required elements): halt and present a validation report. For minor issues (phrasing suggestions, optional improvements): deliver but include notes.

### 5. Generate and Deliver Assets

Organize outputs into a folder named `[ContentTitle]_[Date]/` with subfolders by type:

```
[ContentTitle]_[Date]/
├── manifest.md          (list of all assets with metadata)
├── scripts/             (video scripts, Shorts scripts)
├── captions/            (YouTube descriptions, LinkedIn posts)
├── visuals/             (quote cards, stat graphics, carousel outlines, thumbnail concepts)
└── timestamps/          (timestamp lists, teaser clip recommendations)
```

Each asset includes metadata: source URL or file, creation timestamp, target platform, validation status.

### 6. Handle Errors

- **Insufficient content** (under 100 usable words) → Notify and ask for a better source
- **Ambiguous instructions** → Ask: which platform is priority? What's the primary goal? What tone?
- **Transcript parsing failure** → Attempt OCR on video frames as fallback
- **API failure** (YouTube, LinkedIn) → Retry up to 3 times with exponential backoff; log and continue with available data
- **Validation critical failure** → Halt export, present specific flagged items, request user review

## Asset Types

| Asset | Description |
|-------|-------------|
| YouTube script | Hook (first 3 sec) + body segments with pattern interrupts every 15-20 sec + verbal/visual CTA |
| YouTube caption | Keyword-rich, front-loaded value, 3-5 sentences, primary keyword in first 200 characters |
| YouTube Shorts script | 30-60 sec, immediate hook, on-screen text suggestions, PAS/BAB/list structure |
| Timestamps | HH:MM:SS format with descriptive labels (e.g., `02:34 — Why most AI implementations fail`) |
| Teaser clips | Start/end timestamps for 30-60 sec segments, hook analysis, on-screen text suggestions |
| LinkedIn post | 150-300 words, professional tone, line breaks, 3-5 hashtags, clear CTA |
| LinkedIn carousel | 5-10 slide outlines with headline + bullets + visual recommendation per slide |
| Quote card | Verbatim quote with attribution, sized for 1080×1080 (Instagram) or 1200×628 (LinkedIn) |
| Stat graphic | Key metric with visual emphasis, context label, source citation |
| Infographic text | Headline, subheadlines, stat callouts, source citations, visual element recommendations |
| Thumbnail concept | High-contrast text overlay, visual hook description, emotion/curiosity direction |

## Script Writing Mode (Automation Nation)

When Rich wants to write an **original video script** for his Automation Nation channel — not repurpose existing content, but create something new from an idea or topic — switch to script writing mode.

Read `references/automation-nation.md` for the complete script agent instructions. That file contains:
- Rich's voice, what it sounds like, what to never do
- What never changes across every script (PromptAnything.io placement, no warmup openers, proof before explanation)
- How to think before writing (4 pre-write questions)
- Script output format (classification note + scene-by-scene + caption)
- Scene structures by video type (tool demo, step-by-step build, client result, hot take)
- Visual direction standards
- Rich's full context, mission, approved/banned terms

Also read `references/social-media-check.md` before writing any script to apply the Kane Callaway 7 LEGO BRICK pre-write checklist — evaluate the hook, angle, TAM, and information density before committing to structure.

**Trigger phrases for script writing mode:** "write a script for", "script for my channel", "Automation Nation video", "I want to make a video about", "script this", "help me write a video"

## Reference Files

- `references/platform-specs.md` — Exact format requirements for YouTube, Shorts, LinkedIn, carousels, infographics
- `references/brand-voice.md` — Approved terms, banned terms, copywriting frameworks (AIDA/PAS/FAB/BAB), validation checklist
- `references/automation-nation.md` — Automation Nation video script agent (Rich's voice, script format, video type structures)
- `references/social-media-check.md` — Kane Callaway 7 LEGO BRICK framework for pre-write content evaluation
