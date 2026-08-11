# AIOS Setup Overlay Edit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Composite 5 full-screen Bishop-light animated cards onto the talking moments of `AIOS Setup.mp4`, audio untouched, with a hard verification gate.

**Architecture:** Each card is a self-contained HTML page whose GSAP master timeline is driven by a `window.seekTo(t)` API. A Python/Playwright script captures deterministic frames (seek → screenshot) at 30fps, so there is no wall-clock drift and no setpts stretching. Frames encode to per-card MP4s, then one ffmpeg pass overlays them at measured windows with `enable=between(t,in,out)` while stream-copying the audio. A gate script asserts boundaries, mutation beats, duration, and audio integrity.

**Tech Stack:** Playwright (Python), GSAP 3 (vendored locally), ffmpeg/ffprobe, PIL, Whisper transcript (already produced).

## Global Constraints

- Source: `C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4` (542.650998s, 2560x1440, 30fps). NEVER overwrite it.
- Output: `C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup - overlays.mp4`, identical duration, audio stream byte-identical (`-c:a copy`, verified by stream MD5).
- Working dir: `C:\Users\richm\.claude\aios-overlay-edit\` (cards/, scripts/, build/). `build/` is gitignored.
- Brand: bg `#FAFBFA` primary / `#E6E2DE` secondary panels, text `#000813` and `#1D2333`, accents gold `#E0B848` and blue `#1894C9`, red `#E05252` sparingly. Fonts: Poppins 800/900 display, Montserrat 600/700 uppercase labels, Open Sans 400-600 body (Google Fonts, wait for `document.fonts.ready`).
- Copy rules: no em dashes, no invented acronyms, no AI-lingo banned phrases; card copy tightened from the voiceover, never new claims.
- Motion: a visible change at least every 1.5s on every card; hard cut in/out; no shake, no swoosh (audio untouched).
- Measure, never estimate: all composite windows come from `build/boundaries.json`, not hardcoded guesses.

## Card timeline (from spec, subject to Task 1 measurement)

| id | file | in | out | beats (absolute s) |
|---|---|---|---|---|
| promise | cards/promise.html | 12.7 | 22.6 | 12.7 title; 16.4 subtitle joins |
| buildables | cards/buildables.html | 141.2 | 157.6 | 6 icons pop 141.2→146.0 (~0.8s apart: agent, employee, workflow, web app, image, video); 148.6 promptanything.io closing beat |
| diagram | cards/diagram.html | 163.2 | 184.0 | 163.2 "Your idea" node; 166.5 Orchestrator node + arrow; 172.2 "most efficient path" label; 176.2 skills fan out; 179.5 sub-skills fan out |
| tips | cards/tips.html | 441.6 | 491.2 | 441.6 header; 445.0 tip 1; 454.2 tip 2; 470.1 tip 3; 481.9 recap stack |
| cta | cards/cta.html | 526.4 | 542.65 | 526.4 "Share this with the masses"; 536.9 "Comment: what AI skill did you build today?" joins |

Card-local beat time = absolute − in. Face break 157.6–163.2 and outro face 491.2–526.4 get no overlay.

---

### Task 1: Workspace + boundary measurement

**Files:**
- Create: `aios-overlay-edit/.gitignore` (content: `build/`)
- Create: `aios-overlay-edit/scripts/boundary_check.py`
- Output: `aios-overlay-edit/build/boundaries.json`

**Interfaces:**
- Produces: `boundaries.json` = `{"cards": [{"id": "promise", "in": <float>, "out": <float>}, ...]}` consumed by Tasks 6 and 7. IDs exactly: `promise, buildables, diagram, tips, cta`.

- [ ] **Step 1: Write boundary_check.py**

The classifier from brainstorming (validated on 25 frames): mean R minus mean B over a 48x27 thumbnail; warmth > 15 = talking head, else screen. Scan 1s-granularity frames in zones [8,26], [135,190], [435,500], [518,542]; find the talking↔screen transition nearest each spec boundary; snap card in/out per these rules and write JSON:

```python
import json, subprocess, sys
from PIL import Image
from io import BytesIO

SRC = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4"
SPEC = [  # id, in, out, snap_in_rule, snap_out_rule
    ("promise",    12.7, 22.6,  None,       "before_screen"),  # out must be <= first screen frame
    ("buildables", 141.2, 157.6, "after_talk", None),          # in must be >= talking start
    ("diagram",    163.2, 184.0, None,       "before_screen"),
    ("tips",       441.6, 491.2, None,       "before_talk"),   # out must be <= outro face return
    ("cta",        526.4, 542.65, None,      None),
]
ZONES = [(8, 26), (135, 190), (435, 500), (518, 542)]

def warmth(t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC,
                        "-frames:v", "1", "-vf", "scale=48:27", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True)
    im = Image.open(BytesIO(r.stdout)).convert("RGB")
    px = list(im.getdata())
    return sum(p[0] for p in px)/len(px) - sum(p[2] for p in px)/len(px)

def classify(t): return "talk" if warmth(t) > 15 else "screen"

# 1s scan, then 0.25s refine around each transition
labels = {}
for a, b in ZONES:
    for t in range(a, b + 1):
        labels[t] = classify(t)
transitions = []  # (time, from, to) with time = first instant of `to` at 0.25s precision
for a, b in ZONES:
    for t in range(a, b):
        if labels[t] != labels[t + 1]:
            lo, hi = float(t), float(t + 1)
            while hi - lo > 0.25:
                mid = (lo + hi) / 2
                if classify(mid) == labels[t]: lo = mid
                else: hi = mid
            transitions.append((hi, labels[t], labels[t + 1]))
print("transitions:", transitions)

def nearest(kind, near):  # first instant of `kind` transition nearest `near`
    c = [tr for tr in transitions if tr[2] == kind]
    return min(c, key=lambda tr: abs(tr[0] - near))[0] if c else None

out = {"cards": []}
for cid, tin, tout, snap_in, snap_out in SPEC:
    if snap_in == "after_talk":
        tt = nearest("talk", tin)
        if tt is not None and tt > tin: tin = tt
    if snap_out == "before_screen":
        ts = nearest("screen", tout)
        if ts is not None and abs(ts - tout) < 2.0 and ts < tout: tout = ts
    if snap_out == "before_talk":
        tt = nearest("talk", tout)
        if tt is not None and abs(tt - tout) < 2.0 and tt < tout: tout = tt
    out["cards"].append({"id": cid, "in": round(tin, 2), "out": round(tout, 2)})
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "build/boundaries.json", "w"), indent=1)
print(json.dumps(out))
```

- [ ] **Step 2: Run it**

Run from `aios-overlay-edit/`: `mkdir build; python scripts/boundary_check.py`
Expected: transitions found near 23, ~139, 184, ~491; every card window within 1s of spec values. If a window moved >1s from spec, STOP and re-inspect frames manually before proceeding.

- [ ] **Step 3: Commit** — `.gitignore` + script (`feat(aios-edit): boundary measurement`)

---

### Task 2: Shared brand assets + promise card

**Files:**
- Create: `aios-overlay-edit/cards/brand.css`, `aios-overlay-edit/cards/gsap.min.js` (vendored from CDN once), `aios-overlay-edit/cards/promise.html`

**Interfaces:**
- Produces (contract for ALL cards, Tasks 2-5): each card HTML is 2560x1440, loads `brand.css` + `gsap.min.js` relatively, builds one paused master timeline `tl`, and exposes `window.seekTo = (t) => tl.seek(Math.min(t, tl.duration()), false)` plus `window.cardReady` (Promise resolving after `document.fonts.ready`). Beat times inside the timeline are card-local (absolute − in).

- [ ] **Step 1: Vendor GSAP** — `curl -o cards/gsap.min.js https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`

- [ ] **Step 2: Write brand.css**

```css
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@800;900&family=Montserrat:wght@600;700&family=Open+Sans:wght@400;600&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 2560px; height: 1440px; overflow: hidden; background: #FAFBFA; }
.card { position: relative; width: 2560px; height: 1440px; background: #FAFBFA;
        font-family: 'Open Sans', sans-serif; color: #000813; }
.tag { font-family: 'Montserrat', sans-serif; font-weight: 700; letter-spacing: .22em;
       text-transform: uppercase; font-size: 34px; color: #1D2333; }
.tag .dot { display: inline-block; width: 18px; height: 18px; border-radius: 50%;
            background: #E0B848; margin-right: 22px; vertical-align: middle; }
.display { font-family: 'Poppins', sans-serif; font-weight: 900; line-height: 1.04;
           letter-spacing: -0.02em; color: #000813; }
.gold { color: #E0B848; } .blue { color: #1894C9; }
.panel { background: #E6E2DE; border-radius: 28px; }
.footer { position: absolute; left: 90px; bottom: 60px; font-family: 'Montserrat', sans-serif;
          font-weight: 600; font-size: 26px; letter-spacing: .16em; text-transform: uppercase;
          color: #1D2333; opacity: .55; }
```

- [ ] **Step 3: Write promise.html** (in 12.7 → out 22.6; local beats: 0.0 title, 3.7 subtitle)

```html
<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="brand.css"><script src="gsap.min.js"></script></head>
<body><div class="card">
  <div style="position:absolute;left:90px;top:90px" class="tag"><span class="dot"></span>AIOS Setup</div>
  <div id="title" class="display" style="position:absolute;left:90px;top:420px;font-size:170px;max-width:2200px">
    Build your own<br><span class="gold">AI Operating System</span></div>
  <div id="sub" class="display" style="position:absolute;left:90px;top:920px;font-size:92px;color:#1D2333">
    Become a <span class="blue">master prompt engineer</span> in minutes</div>
  <div id="bar" style="position:absolute;left:90px;top:880px;width:0;height:10px;background:#E0B848;border-radius:5px"></div>
  <div class="footer">Bishop AI</div>
</div>
<script>
  const tl = gsap.timeline({ paused: true });
  tl.set({}, {}, 10);                       // pad to full card duration (9.9s)
  tl.from("#title", { y: 80, opacity: 0, duration: .6, ease: "power3.out" }, 0.05);
  tl.to("#bar", { width: 700, duration: .8, ease: "power2.inOut" }, 1.2);
  tl.from("#sub", { y: 60, opacity: 0, duration: .6, ease: "power3.out" }, 3.7);
  tl.to("#title .gold", { color: "#c9a23c", duration: .4, yoyo: true, repeat: 1 }, 5.5);
  tl.to("#bar", { width: 1500, duration: 1.2, ease: "power2.inOut" }, 6.5);
  tl.to("#sub .blue", { color: "#0f6f99", duration: .4, yoyo: true, repeat: 1 }, 8.2);
  window.seekTo = t => tl.seek(Math.min(t, tl.duration() - 0.001), false);
  window.cardReady = document.fonts.ready;
</script></body></html>
```

Note the cadence fillers (bar growth, accent pulses) keeping a visible change every ≤1.5s through the 9.9s hold.

- [ ] **Step 4: Visual check** — screenshot at local t = 0.5, 4.5, 9.0 (use the Task 6 capture script's `--preview` mode once it exists, or a 10-line inline Playwright snippet: goto file URL, await cardReady, seekTo, screenshot). Read the images: title legible at 0.5, subtitle joined at 4.5, nothing clipped, light bg. Fix and re-check until right.

- [ ] **Step 5: Commit** (`feat(aios-edit): brand assets + promise card`)

---

### Task 3: Buildables + diagram cards

**Files:**
- Create: `aios-overlay-edit/cards/buildables.html`, `aios-overlay-edit/cards/diagram.html`

Same contract as Task 2. Content:

- [ ] **Step 1: buildables.html** (in 141.2 → out 157.6, 16.4s timeline)
  - Header tag "What you can build now" + display line "Anything you can describe".
  - 3x2 grid of `.panel` tiles, each an inline SVG glyph (navy stroke, gold accent) + Montserrat label: Agent, Employee, Workflow, Web app, Image, Video. Pop in (`scale .8→1, opacity 0→1, back.out`) at local 0.0, 0.8, 1.6, 2.4, 3.2, 4.0.
  - Local 7.4 ("prompt anything.io" spoken at 152.6-157.6): bottom band slides up: "Built with strong prompts · promptanything.io" (Poppins 800, blue accent). Filler pulses on grid tiles every ~1.2s between 4.0 and 7.4 (subtle border-color to gold and back, staggered).
- [ ] **Step 2: Visual check** at local 0.5, 4.5, 8.5, 15.0; fix until right.
- [ ] **Step 3: diagram.html** (in 163.2 → out 184.0, 20.8s timeline)
  - Header tag "Your first skill" + title "The Orchestrator Agent".
  - Nodes as rounded `.panel` boxes with navy text, connected by SVG lines drawn with `stroke-dashoffset` animation: local 0.0 "Your idea" node; 3.3 arrow draws + Orchestrator node (gold border, larger); 9.0 right-side label "finds the most efficient way to do it" (Open Sans 600, blue); 13.0 three "Skill" nodes fan out below with stagger .3; 16.3 two "Sub-skill" nodes fan under middle skill, stagger .3. Filler: a small gold dot travels the idea→orchestrator line every ~1.4s from 5.0 onward (repeat), so motion never stops.
- [ ] **Step 4: Visual check** at local 1, 5, 11, 15, 19; fix until right.
- [ ] **Step 5: Commit** (`feat(aios-edit): buildables + diagram cards`)

---

### Task 4: Tips card

**Files:**
- Create: `aios-overlay-edit/cards/tips.html` (in 441.6 → out ~491.2 measured, ~49.6s timeline)

- [ ] **Step 1: Write it.** Single page, four states (this is the longest card; it must never sit still):
  - Local 0.0: header "3 tips for building an AI Operating System" (display, 120px) + three empty numbered slots (gold Poppins 900 numerals 1/2/3 at 30% opacity).
  - 3.4 (=445.0): slot 1 fills: "Be thorough. Speak to your AI the way it likes to be spoken to." sub-line "PromptAnything writes those prompts for you." Numeral 1 to full gold.
  - 12.6 (=454.2): slot 2 fills: "Confused? Ask it to explain like you're five." sub-line "Step by step. Foolproof. Your own cookbook."
  - 28.5 (=470.1): slot 3 fills: "Not satisfied? Demand a full audit." sub-line "Tell it to research the internet for better solutions."
  - 40.3 (=481.9): recap: slots compress upward, tag line "Use all three, every build" slides in at bottom with gold bar.
  - Fillers: within each waiting stretch, stagger word-highlight sweeps (navy to blue and back) across the active tip's sub-line every ~1.3s; numerals tick a subtle scale pulse when their tip is active. Longest gap (tip 2, 15.9s) also underlines "like you're five" at local 18 and "cookbook" at local 24.
- [ ] **Step 2: Visual check** at local 1, 5, 14, 30, 42, 48; fix until right.
- [ ] **Step 3: Commit** (`feat(aios-edit): tips card`)

---

### Task 5: CTA card

**Files:**
- Create: `aios-overlay-edit/cards/cta.html` (in 526.4 → out 542.65, 16.25s timeline)

- [ ] **Step 1: Write it.**
  - Local 0.0: display line "Share this with the masses" (140px) + sub "Nobody gets left behind the curve" (Open Sans 600, #1D2333, 60px).
  - 10.5 (=536.9): panel slides up: gold comment-bubble SVG + "Comment: what AI skill did you build today?" (Poppins 800, 84px); share line compresses to top.
  - Fillers: underline draw at 2.0, bubble bob every 1.2s after 10.5, sub-line color sweep at 5.5 and 8.0.
  - Ends holding recap state through 542.65 (timeline padded to 16.3).
- [ ] **Step 2: Visual check** at local 1, 8, 12, 16; fix until right.
- [ ] **Step 3: Commit** (`feat(aios-edit): cta card`)

---

### Task 6: Deterministic capture + encode

**Files:**
- Create: `aios-overlay-edit/scripts/render_cards.py`

**Interfaces:**
- Consumes: `build/boundaries.json`, card contract (`window.cardReady`, `window.seekTo`).
- Produces: `build/<id>.mp4` per card (2560x1440, 30fps, yuv420p, duration = out − in ± 1 frame) consumed by Task 7. Also `--preview <id> <t...>` mode writing `build/preview_<id>_<t>.png` (used by Tasks 2-5).

- [ ] **Step 1: Write render_cards.py**

```python
import json, math, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS = 30

def capture(page, cid, times, outdir):
    page.goto((ROOT / "cards" / f"{cid}.html").as_uri())
    page.evaluate("() => window.cardReady")
    outdir.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(times):
        page.evaluate(f"window.seekTo({t})")
        page.screenshot(path=str(outdir / f"f{i:05d}.png"))

def main():
    bounds = {c["id"]: c for c in json.load(open(ROOT / "build" / "boundaries.json"))["cards"]}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 2560, "height": 1440})
        if len(sys.argv) > 1 and sys.argv[1] == "--preview":
            cid, times = sys.argv[2], [float(x) for x in sys.argv[3:]]
            page.goto((ROOT / "cards" / f"{cid}.html").as_uri())
            page.evaluate("() => window.cardReady")
            for t in times:
                page.evaluate(f"window.seekTo({t})")
                page.screenshot(path=str(ROOT / "build" / f"preview_{cid}_{t}.png"))
            return
        for cid, b in bounds.items():
            n = math.ceil((b["out"] - b["in"]) * FPS)
            frames = ROOT / "build" / f"frames_{cid}"
            capture(page, cid, [i / FPS for i in range(n)], frames)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                            "-i", str(frames / "f%05d.png"), "-c:v", "libx264",
                            "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
                            str(ROOT / "build" / f"{cid}.mp4")], check=True)
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "csv=p=0", str(ROOT / "build" / f"{cid}.mp4")],
                capture_output=True, text=True).stdout)
            exp = b["out"] - b["in"]
            assert abs(d - exp) <= 1.5 / FPS, f"{cid}: got {d}, expected {exp}"
            print(cid, "ok", d)
        browser.close()

main()
```

- [ ] **Step 2: Run full render** — `python scripts/render_cards.py`. Expected: five `ok` lines, no assertion errors. (~3400 frames; minutes, not seconds.)
- [ ] **Step 3: Spot-check** one mid-card frame per card from `build/frames_<id>/` by reading the PNG. Motion state must match the beat table.
- [ ] **Step 4: Commit** script only (`feat(aios-edit): deterministic card renderer`)

---

### Task 7: Composite

**Files:**
- Create: `aios-overlay-edit/scripts/composite.py`

**Interfaces:**
- Consumes: `build/<id>.mp4`, `build/boundaries.json`.
- Produces: `C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup - overlays.mp4`.

- [ ] **Step 1: Write composite.py** — build one ffmpeg command: inputs = source + 5 card mp4s; per card i: `[i:v]setpts=PTS-STARTPTS+{in_i}/TB[c{i}]`, chain `overlay=enable='between(t,{in_i},{out_i})':eof_action=pass`; map final video + `-map 0:a -c:a copy`; `-c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p`.

```python
import json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4"
DST = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup - overlays.mp4"
cards = json.load(open(ROOT / "build" / "boundaries.json"))["cards"]
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC]
for c in cards: cmd += ["-i", str(ROOT / "build" / f"{c['id']}.mp4")]
fc, prev = [], "0:v"
for i, c in enumerate(cards, start=1):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{c['in']}/TB[c{i}]")
    fc.append(f"[{prev}][c{i}]overlay=enable='between(t,{c['in']},{c['out']})':eof_action=pass[v{i}]")
    prev = f"v{i}"
cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "copy", DST]
subprocess.run(cmd, check=True)
print("done")
```

- [ ] **Step 2: Run it** (long encode, run in background; 9min of 1440p x264).
- [ ] **Step 3: Commit** (`feat(aios-edit): composite pass`)

---

### Task 8: Verification gate

**Files:**
- Create: `aios-overlay-edit/scripts/verify_gate.py`
- Output: `build/verify_report/` boundary frame grid + `PASS`/`FAIL` stdout

- [ ] **Step 1: Write verify_gate.py** asserting, against the OUTPUT file:
  1. Duration: `ffprobe` format.duration within 0.05s of 542.650998.
  2. Audio integrity: `ffmpeg -i <file> -map 0:a -c copy -f md5 -` identical for source and output.
  3. Boundaries: for each card, frames at in+0.5 and out−0.5 are card-light (mean luma > 180, warmth < 15 — all cards are near-white; talking frames measured warmth ≈ +30, luma ≈ 115; screens vary but the four cut-adjacent contexts measured luma ≤ 130 except none near 180) and frames at in−0.5 and out+0.5 are NOT card-light. Save all four frames per card to `build/verify_report/`.
  4. Beats: for each beat listed in the plan table, frames at beat±0.4s inside the output differ (mean abs pixel diff > 1.0) proving the mutation landed.
  Exit 0 only if every assertion passes; print a per-check table either way.
- [ ] **Step 2: Run the gate.** If FAIL: fix the offending card/window, re-render that card only, re-composite, re-run. Repeat until PASS.
- [ ] **Step 3: Read the verify_report frame grid yourself** — final human-eye check that in/out frames look like clean cuts.
- [ ] **Step 4: Commit** (`feat(aios-edit): verification gate`) and report to Rich: output path, gate table, boundary frame grid.

## Self-review notes

- Spec coverage: all 6 spec zones covered (face break + outro face = no-op by design); measurement (T1), cards (T2-5), render (T6), composite (T7), gate (T8). Spec's setpts-stretch step is superseded by deterministic seek-capture (no wall-clock recording anywhere), which the spec's intent (no drift) requires; duration asserts remain in T6.
- Types: card contract (`cardReady`, `seekTo`) consistent across T2-6; `boundaries.json` shape consistent across T1/T6/T7.
- No placeholders: pipeline scripts are complete; card HTML for T3-5 is specified by exact copy, beat tables, and layout/animation rules with T2 as the canonical code pattern (executor is this session, which holds full context).
