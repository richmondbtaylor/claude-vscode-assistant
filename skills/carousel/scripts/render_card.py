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
    from PIL import Image
    with Image.open(src) as probe:
        est_h = width * probe.height / probe.width
    # stage must fit the card in both dimensions (tall portrait captures included)
    stage = int(1.5 * max(width, est_h))
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
