# Carousel Real-Screenshot Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let carousel value slides show real, pixel-readable Playwright screenshots inside the existing signature 3D floating card, composited onto panoramas before slicing so seamless mode keeps working.

**Architecture:** Three small standalone scripts (matching the argv style of `slice_panorama.py`): `capture_screenshot.py` grabs a live page at 2x, `render_card.py` wraps the capture in a CSS-built tilted card with amber glow on a transparent background, `composite_card.py` pastes the card onto the panorama/slide with Pillow. SKILL.md gains a `[SCREENSHOT: ...]` planning tag, a prompt rule (plain background where a real card will go), workflow updates, and a fallback rule.

**Tech Stack:** Python, Playwright (async chromium), Pillow, pytest.

**Spec:** `docs/superpowers/specs/2026-07-06-carousel-screenshots-design.md`

## Global Constraints

- **Do NOT commit or push anything.** Rich commits on request only (standing rule; overrides the usual commit-per-task steps — they are intentionally absent).
- Working directory for all commands: `C:\Users\richm\.claude` (Windows, PowerShell).
- Brand constants: deck background `#080B14`, accent glow golden-amber `#E0B848`, handle `@bishop_ai_`.
- Seamless rule: cards and glow must stay out of the outer 12% of a panorama's width.
- Scripts follow the existing pattern of `skills/carousel/scripts/slice_panorama.py`: module docstring with usage, positional argv, `print()` progress, no argparse.
- Never let the image model redraw a screenshot; real pixels only.
- If pytest is missing, install with: `pip install pytest --trusted-host pypi.org --trusted-host files.pythonhosted.org`

---

### Task 1: capture_screenshot.py

**Files:**
- Create: `skills/carousel/scripts/capture_screenshot.py`
- Test: `skills/carousel/tests/test_capture_screenshot.py`

**Interfaces:**
- Consumes: nothing (leaf script).
- Produces: CLI `python skills/carousel/scripts/capture_screenshot.py <url> <output_path> [selector|-] [viewport_w] [viewport_h] [extra_wait_ms]` → PNG at 2x device scale (viewport 1440x900 default → 2880x1800 PNG). Later tasks feed this PNG to `render_card.py`.

- [ ] **Step 1: Write the failing test**

Create `skills/carousel/tests/test_capture_screenshot.py`:

```python
import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "capture_screenshot.py"


def test_captures_local_page_at_2x(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(
        "<html><body style='margin:0;background:#123456'>"
        "<h1 style='color:white'>Hello</h1></body></html>"
    )
    out = tmp_path / "shot.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), page.resolve().as_uri(), str(out),
         "-", "1200", "700", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.size == (2400, 1400)  # 2x device scale
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/carousel/tests/test_capture_screenshot.py -v`
Expected: FAIL (returncode != 0, script file does not exist).

- [ ] **Step 3: Write the implementation**

Create `skills/carousel/scripts/capture_screenshot.py`:

```python
"""Capture a screenshot of a URL or local HTML file for carousel cards.

Usage:
    python capture_screenshot.py <url> <output_path> [selector] [viewport_w] [viewport_h] [extra_wait_ms]

    url            Page to capture (https://... or file:///...)
    output_path    PNG output path (parent dirs created if missing)
    selector       Optional CSS selector -- capture just that element.
                   Pass '-' to capture the full viewport (default).
    viewport_w     Viewport width in CSS px (default 1440)
    viewport_h     Viewport height in CSS px (default 900)
    extra_wait_ms  Extra settle time after networkidle (default 1500)

Captures at 2x device scale so text stays crisp when the capture is
shrunk into a slide card. Feed the output to render_card.py.
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    out_path = sys.argv[2]
    selector = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    vw = int(sys.argv[4]) if len(sys.argv) > 4 else 1440
    vh = int(sys.argv[5]) if len(sys.argv) > 5 else 900
    wait_ms = int(sys.argv[6]) if len(sys.argv) > 6 else 1500

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": vw, "height": vh}, device_scale_factor=2
        )
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(wait_ms)
        if selector:
            await page.locator(selector).first.screenshot(path=out_path)
        else:
            await page.screenshot(path=out_path)
        await browser.close()

    print(f"Saved {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/carousel/tests/test_capture_screenshot.py -v`
Expected: PASS. (If chromium is missing: `python -m playwright install chromium`, then re-run.)

---

### Task 2: render_card.py

**Files:**
- Create: `skills/carousel/scripts/render_card.py`
- Test: `skills/carousel/tests/test_render_card.py`

**Interfaces:**
- Consumes: a capture PNG/JPG (from Task 1, or any image).
- Produces: CLI `python skills/carousel/scripts/render_card.py <screenshot_path> <output_path> [tilt] [card_width]` → RGBA PNG at 2x, transparent background, amber glow baked in. `tilt` is `right` (default) or `left`; `card_width` default 820 CSS px. Output stage is square, 1.5x the card width (glow padding), rendered at 2x → default 2460x2460 px. Task 3 composites this PNG.

- [ ] **Step 1: Write the failing test**

Create `skills/carousel/tests/test_render_card.py`:

```python
import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_card.py"


def test_renders_tilted_card_on_transparency(tmp_path):
    src = tmp_path / "shot.png"
    Image.new("RGB", (800, 600), (30, 60, 200)).save(src)
    out = tmp_path / "card.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.mode == "RGBA"
    assert img.width >= 2000  # 2x render incl. glow padding
    assert img.getpixel((2, 2))[3] == 0  # corners transparent
    cx, cy = img.width // 2, img.height // 2
    assert img.getpixel((cx, cy))[3] == 255  # card center opaque
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/carousel/tests/test_render_card.py -v`
Expected: FAIL (script file does not exist).

- [ ] **Step 3: Write the implementation**

Create `skills/carousel/scripts/render_card.py`:

```python
"""Wrap a screenshot in the signature carousel card: dark rounded frame,
3D perspective tilt, drop shadow, golden-amber glow, transparent background.

Usage:
    python render_card.py <screenshot_path> <output_path> [tilt] [card_width]

    screenshot_path  PNG/JPG capture to place inside the card
    output_path      RGBA PNG output (parent dirs created if missing)
    tilt             'right' (default -- for cards on the right side of a
                     slide, right edge rotated away) or 'left'
    card_width       Card width in CSS px before the 2x render (default 820)

Output is a square RGBA PNG (stage = 1.5x card width, rendered at 2x) with
the amber #E0B848 glow baked in on transparency. The glow blends cleanly on
the uniform #080B14 deck background. Feed the output to composite_card.py.
"""
import asyncio
import base64
import os
import sys

from playwright.async_api import async_playwright

HTML = """<!doctype html>
<html><head><style>
  html, body {{ margin: 0; background: transparent; }}
  .stage {{ width: {stage}px; height: {stage}px; position: relative;
            display: flex; align-items: center; justify-content: center;
            perspective: 1400px; }}
  .glow {{ position: absolute; width: 78%; height: 78%; border-radius: 50%;
           background: radial-gradient(circle,
             rgba(224,184,72,0.55) 0%, rgba(224,184,72,0.22) 38%,
             rgba(224,184,72,0.0) 70%);
           filter: blur(28px); }}
  .card {{ position: relative; width: {width}px; border-radius: 14px;
           overflow: hidden; transform: rotateY({rot}deg) rotateX(4deg);
           border: 1px solid rgba(255,255,255,0.10);
           box-shadow: 0 40px 80px rgba(0,0,0,0.65);
           background: #0d1220; }}
  .card img {{ display: block; width: 100%; }}
</style></head>
<body><div class="stage"><div class="glow"></div>
<div class="card"><img src="data:image/{ext};base64,{b64}"></div>
</div></body></html>"""


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    out_path = sys.argv[2]
    tilt = sys.argv[3] if len(sys.argv) > 3 else "right"
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 820

    rot = -12 if tilt == "right" else 12
    stage = int(width * 1.5)
    ext = "png" if src.lower().endswith(".png") else "jpeg"
    with open(src, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    html = HTML.format(stage=stage, width=width, rot=rot, ext=ext, b64=b64)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": stage, "height": stage}, device_scale_factor=2
        )
        await page.set_content(html)
        await page.wait_for_timeout(400)
        await page.locator(".stage").screenshot(path=out_path, omit_background=True)
        await browser.close()

    print(f"Saved {out_path} (card {width}px, tilt {tilt}, stage {stage}px @2x)")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/carousel/tests/test_render_card.py -v`
Expected: PASS.

- [ ] **Step 5: Visual sanity check**

Run the script on any real capture (or the test's blue rectangle), then view the output PNG with the Read tool. Check: card is tilted, rounded, has a soft amber glow, background fully transparent. If the glow looks weak or the tilt looks wrong versus the generated cards in `skills/carousel/references/seamless-example/slide-01.jpg`, adjust the CSS constants (rot, glow opacities, blur) and re-run the test.

---

### Task 3: composite_card.py

**Files:**
- Create: `skills/carousel/scripts/composite_card.py`
- Test: `skills/carousel/tests/test_composite_card.py`

**Interfaces:**
- Consumes: a base image (panorama `pano-XX.jpg` or standalone slide) + an RGBA card PNG from Task 2.
- Produces: CLI `python skills/carousel/scripts/composite_card.py <base_image> <card_png> <center_x> <center_y> <target_width> <output_path>` → JPG same size as base with the card pasted, card center at (center_x, center_y), card scaled to target_width px. Prints a `WARNING:` line if the card enters the outer 12% of the base width.

- [ ] **Step 1: Write the failing tests**

Create `skills/carousel/tests/test_composite_card.py`:

```python
import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "composite_card.py"


def _make_inputs(tmp_path):
    base = tmp_path / "base.jpg"
    Image.new("RGB", (3000, 1250), (8, 11, 20)).save(base)
    card = tmp_path / "card.png"
    c = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
    for x in range(100, 300):
        for y in range(75, 225):
            c.putpixel((x, y), (255, 255, 255, 255))
    c.save(card)
    return base, card


def test_composites_card_at_center(tmp_path):
    base, card = _make_inputs(tmp_path)
    out = tmp_path / "out.jpg"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(base), str(card),
         "1500", "625", "800", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.size == (3000, 1250)
    assert img.getpixel((1500, 625))[0] > 200  # white card visible at center
    assert img.getpixel((100, 100))[0] < 30    # background untouched
    assert "WARNING" not in result.stdout


def test_warns_when_card_enters_outer_margin(tmp_path):
    base, card = _make_inputs(tmp_path)
    out = tmp_path / "out.jpg"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(base), str(card),
         "200", "625", "800", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest skills/carousel/tests/test_composite_card.py -v`
Expected: FAIL (script file does not exist).

- [ ] **Step 3: Write the implementation**

Create `skills/carousel/scripts/composite_card.py`:

```python
"""Composite a rendered screenshot card onto a panorama or standalone slide.

Usage:
    python composite_card.py <base_image> <card_png> <center_x> <center_y> <target_width> <output_path>

    base_image    Panorama (pano-XX.jpg) or standalone slide image
    card_png      RGBA card from render_card.py (glow included)
    center_x/y    Pixel position in the base image where the card CENTER
                  lands. In seamless mode put center_x on a zone boundary
                  so the card straddles two slides.
    target_width  Final width in base-image pixels for the whole card PNG
                  (glow padding included)
    output_path   Composited image output (jpg)

Run BEFORE slice_panorama.py so boundary-straddling bleed survives slicing.
Warns if the card enters the outer 12% of the base width -- that area must
stay plain background so seams between panorama groups stay invisible.
"""
import sys

from PIL import Image


def run():
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)

    base_path = sys.argv[1]
    card_path = sys.argv[2]
    cx = int(sys.argv[3])
    cy = int(sys.argv[4])
    target_w = int(sys.argv[5])
    out_path = sys.argv[6]

    base = Image.open(base_path).convert("RGB")
    card = Image.open(card_path).convert("RGBA")
    target_h = int(round(card.height * target_w / card.width))
    card = card.resize((target_w, target_h), Image.LANCZOS)

    x0 = cx - target_w // 2
    y0 = cy - target_h // 2

    margin = int(base.width * 0.12)
    if x0 < margin or x0 + target_w > base.width - margin:
        print(
            f"WARNING: card spans x {x0}..{x0 + target_w} inside outer 12% "
            f"margin ({margin}px) -- may break invisible seams between groups"
        )

    base.paste(card, (x0, y0), card)
    base.save(out_path, quality=95)
    print(
        f"Saved {out_path} ({base.width}x{base.height}), "
        f"card at ({x0},{y0}) size {target_w}x{target_h}"
    )


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest skills/carousel/tests/test_composite_card.py -v`
Expected: 2 PASS.

---

### Task 4: End-to-end shakedown against the reference panorama

**Files:**
- Create: nothing permanent — all outputs go to the session scratchpad directory (never into the repo).
- Uses: `skills/carousel/references/seamless-example/pano-01.jpg` (read-only input).

**Interfaces:**
- Consumes: all three CLIs exactly as defined in Tasks 1–3.
- Produces: a visual verdict (and any CSS/placement tuning fed back into `render_card.py` constants).

- [ ] **Step 1: Capture a real page**

```powershell
python skills\carousel\scripts\capture_screenshot.py https://promptanything.io "$env:SCRATCHPAD\shakedown\capture.png"
```

(Substitute the session scratchpad path for `$env:SCRATCHPAD`.)
Expected: `Saved ...capture.png`, 2880x1800 PNG.

- [ ] **Step 2: Render the card**

```powershell
python skills\carousel\scripts\render_card.py "$env:SCRATCHPAD\shakedown\capture.png" "$env:SCRATCHPAD\shakedown\card.png"
```

Expected: RGBA PNG ~2460x2460.

- [ ] **Step 3: Composite onto the reference panorama at a zone boundary**

First get the panorama size, then place the card center on the boundary between zones 1 and 2 (x = width/3), vertically centered, card width ≈ 30% of panorama width:

```powershell
python -c "from PIL import Image; im=Image.open(r'skills\carousel\references\seamless-example\pano-01.jpg'); print(im.size)"
python skills\carousel\scripts\composite_card.py skills\carousel\references\seamless-example\pano-01.jpg "$env:SCRATCHPAD\shakedown\card.png" <width//3> <height//2> <int(width*0.30)> "$env:SCRATCHPAD\shakedown\pano-composited.jpg"
```

Expected: saved composite, NO seam warning.

- [ ] **Step 4: Slice and visually verify**

```powershell
python skills\carousel\scripts\slice_panorama.py "$env:SCRATCHPAD\shakedown\pano-composited.jpg" 3 "$env:SCRATCHPAD\shakedown\slices" 1 "4:5"
```

View `slide-01.jpg` and `slide-02.jpg` with the Read tool and check:
- Screenshot text legible at slide size
- Card tilt/glow plausibly matches the model-drawn cards elsewhere in the panorama
- The card straddles the slide-01/slide-02 boundary with pixel-perfect bleed
- Glow fades into the `#080B14` background with no visible rectangle edge

If the card looks off (glow too strong/weak, tilt angle mismatched, frame too bright), tune the CSS constants in `render_card.py`, re-run Task 2's test, and repeat from Step 2.

---

### Task 5: SKILL.md updates

**Files:**
- Modify: `skills/carousel/SKILL.md`

**Interfaces:**
- Consumes: the three CLIs from Tasks 1–3 (paths and argument orders must match exactly).
- Produces: the updated skill instructions future carousel runs follow.

- [ ] **Step 1: Add the `[SCREENSHOT: ...]` cue to Step 7 (visual notes)**

In the "## Step 7: Add Minimal Visual Notes" bullet list, after the `[LOGOS: ...]` line, add:

```markdown
- `[SCREENSHOT: <url or tool> -- <what to show>]` -- slide will carry a REAL captured screenshot inside the floating card (see Real Screenshot Cards section)
```

- [ ] **Step 2: Insert the "Real Screenshot Cards" section**

Insert immediately BEFORE the line `### Seamless Mode (Default) — Slides Bleed Into Each Other`:

```markdown
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
Then run slice_panorama.py on the composited file. In standalone mode, composite onto the individual slide image instead.

**Prompt rule:** for a screenshot slide's zone, the panorama prompt must describe plain uniform #080B14 background where the card will sit -- explicitly no floating card, no glow drawn by the model in that area. Text furniture (label, number, headline, bullets, handle) is still generated as usual. Neighboring generated-card zones are unchanged. Respect the existing seam rule: composited cards and their glow stay out of the outer 12% of each panorama.

**Verify after slicing:** screenshot text legible, card tilt/glow matches neighboring generated cards, bleed intact across the boundary, no zone furniture covered.

**Fallback:** if a target needs a login you cannot reach or will not render, use a generated card for that slide or ask Rich for a manual capture.
```

- [ ] **Step 3: Update the Execution Workflow**

In "### Execution Workflow (Proven Pattern)", after the **Step 1** paragraph, add:

```markdown
**Step 1.5 — Capture and render screenshot cards (if any `[SCREENSHOT:]` slides).** While panoramas generate, run capture_screenshot.py + render_card.py for each screenshot slide. After panoramas land, run composite_card.py on each affected panorama, then continue with the composited files.
```

And in **Step 2.5**, change the sentence "Run slice_panorama.py on each panorama with the correct starting slide number." to:

```markdown
Run slice_panorama.py on each panorama (use the -comp.jpg composited version for panoramas that received screenshot cards) with the correct starting slide number.
```

- [ ] **Step 4: Update Visual Consistency Rules and Prerequisites**

In "### Visual Consistency Rules", after the "**Varied 3D floating elements**" bullet, add:

```markdown
- **Real screenshots stay real** -- screenshot-slide cards are composited from actual captures (capture_screenshot.py -> render_card.py -> composite_card.py), never redrawn by the image model
```

In "### Prerequisites", add:

```markdown
- `capture_screenshot.py`, `render_card.py`, `composite_card.py`: At `C:\Users\richm\.claude\skills\carousel\scripts\` (screenshot cards; require Playwright chromium -- `python -m playwright install chromium` if missing)
```

- [ ] **Step 5: Verify the edits**

Read the modified sections of SKILL.md and confirm: script paths and argument orders match Tasks 1–3 exactly; the seamless-mode instructions still read coherently start to finish; no smart quotes were introduced.

---

## Self-Review Notes

- Spec coverage: capture (Task 1), card render (Task 2), composite + 12% seam rule (Task 3), verification + shakedown (Task 4), SKILL.md planning tag / prompt rule / workflow / fallback (Task 5). CTA unchanged — no task touches it. ✔
- Types/signatures consistent: argv orders in Task 5's SKILL.md snippets match Tasks 1–3 CLIs. ✔
- No commits by design (Global Constraints — standing user rule). ✔
