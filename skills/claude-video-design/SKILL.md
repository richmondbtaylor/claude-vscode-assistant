# Claude Video Design

A full video production pipeline for Claude Code: transcribe raw footage, cut filler words, color grade, burn subtitles, and composite motion graphics — all from a single conversation.

## What it does

1. **Transcribe** — ElevenLabs Scribe produces word-level timestamps with filler tagging
2. **Edit** — FFmpeg cuts `umm`, `uh`, false starts, and dead air; 30ms audio fades at every cut
3. **Color grade** — warm cinematic, neutral punch, or custom FFmpeg chain applied per-segment
4. **Subtitles** — 2-word UPPERCASE chunks burned in (style is configurable)
5. **Motion graphics** — HyperFrames renders HTML/CSS/GSAP overlays to MP4; video-use composites them in as overlay tracks
6. **Self-evaluate** — rendered output is verified at every cut boundary before delivery

## Tool stack

| Tool | Role |
|---|---|
| **video-use** (browser-use/video-use) | Transcription, filler removal, FFmpeg editing pipeline, subtitle burning, animation compositing |
| **HyperFrames** (heygen-com/hyperframes) | HTML-to-video renderer for motion graphics — write HTML + GSAP, render to MP4 overlay |
| **ElevenLabs Scribe** | Word-level transcription with sub-second gap data and filler detection |
| **FFmpeg / ffprobe** | All video processing — cuts, fades, color, overlays, concat |
| **Manim / PIL** | Alternative animation backends (scientific diagrams, chart reveals, data viz) |

## Pipeline architecture

```
raw_video.mp4
    │
    ▼
[ElevenLabs Scribe]  →  word-level transcript (JSON, verbatim)
    │
    ▼
[video-use strategy] →  propose cut list, confirm with user
    │
    ▼
[FFmpeg]             →  extract segments, apply color grade, 30ms audio fades
    │
    ▼
[HyperFrames]        →  render motion graphic overlays (HTML/CSS/GSAP → MP4)
    │
    ▼
[FFmpeg composite]   →  overlay animations, burn subtitles, concat final
    │
    ▼
edit/final.mp4
```

## Motion graphics with HyperFrames

HyperFrames uses headless Chrome + FFmpeg to render any HTML composition frame-accurately. Use it for:

- Animated lower thirds, titles, callout cards
- Data chart reveals (bar, line, pie with GSAP tweens)
- Logo stingers and brand bumpers
- Full-screen text animations (GSAP SplitText, TypeSplit)
- Website-capture-to-video sequences

Write a composition as `index.html` with `data-composition-id`, `data-start`, `data-duration` attributes. Preview in browser instantly. Render with:

```bash
npx hyperframes render index.html --output overlay.mp4
```

Then pass `overlay.mp4` back to video-use for compositing.

## How to use

### Starting a session

```
Drop raw footage into a folder, then in Claude Code:
> edit this into a [tutorial / launch video / talking head clip]
```

The skill inventories sources, proposes a strategy, waits for your confirmation, then produces `edit/final.mp4`.

### Adding motion graphics

```
> add an animated lower third at 0:12 with my name "Rich Taylor" and title "AI Automation"
> add a stats card overlay at 1:30 showing "10x faster"
> add a branded intro bumper
```

Claude builds the HyperFrames HTML composition, renders it, and composites it onto the final edit.

### Key rules

- **Never edit before confirming strategy.** Always propose cut list first.
- **Never re-transcribe cached sources.** Transcripts are immutable outputs.
- **Never burn subtitles into base before compositing overlays** — overlays will hide them.
- **Never use linear easing** — always `ease_out_cubic` or `ease_in_out_cubic`.
- **30ms audio fades at every cut** — no hard audio pops.
- **One animation per sub-agent** — spawn in parallel, never sequential.

## Output spec

All outputs land in `<videos_dir>/edit/`:

```
edit/
  final.mp4          1920×1080, H.264 CRF 18, AAC 192k
  final.srt          subtitle file
  project.md         session memory (persisted across sessions)
  animations/
    slot_01/render.mp4
    slot_02/render.mp4
```

## Animation easing reference

```python
def ease_out_cubic(t):    return 1 - (1 - t) ** 3
def ease_in_out_cubic(t):
    if t < 0.5: return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2
```

## Anti-patterns (never do these)

- Running Whisper locally on CPU (slow, normalizes fillers — use ElevenLabs Scribe)
- Single-pass filtergraph with overlays (double re-encode — extract segments then concat)
- Sequential sub-agents for animations (always parallel)
- Assuming video type — look first, ask second, edit last
- Hard audio cuts at segment boundaries
- Typing text centered on partial string (text slides left as it grows)
