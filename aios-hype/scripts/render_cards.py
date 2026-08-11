"""Deterministic seek-capture renderer for the aios-hype sarev cards (1080x960)."""
import json, math, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS = 30
CARDS = [  # id, duration (spliced-timeline windows in compose.py)
    ("c1_hook", 13.65),
    ("c2_build", 7.57),
    ("c3_demo", 6.30),
    ("c4_cta", 13.834),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 960})
        if len(sys.argv) > 1 and sys.argv[1] == "--preview":
            cid, times = sys.argv[2], [float(x) for x in sys.argv[3:]]
            page.goto((ROOT / "cards" / f"{cid}.html").as_uri())
            page.evaluate("() => window.cardReady")
            for t in times:
                page.evaluate(f"void window.seekTo({t})")
                page.screenshot(path=str(ROOT / "build" / f"preview_{cid}_{t}.png"))
            browser.close()
            return
        for cid, dur in CARDS:
            n = math.ceil(dur * FPS)
            frames = ROOT / "build" / f"frames_{cid}"
            frames.mkdir(parents=True, exist_ok=True)
            page.goto((ROOT / "cards" / f"{cid}.html").as_uri())
            page.evaluate("() => window.cardReady")
            for i in range(n):
                page.evaluate(f"void window.seekTo({i / FPS})")
                page.screenshot(path=str(frames / f"f{i:05d}.png"))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                            "-i", str(frames / "f%05d.png"), "-c:v", "libx264",
                            "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
                            str(ROOT / "build" / f"{cid}.mp4")], check=True)
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "csv=p=0", str(ROOT / "build" / f"{cid}.mp4")],
                capture_output=True, text=True).stdout)
            assert abs(d - dur) <= 1.5 / FPS, f"{cid}: got {d}, expected {dur}"
            print(cid, "ok", round(d, 3), flush=True)
        browser.close()


main()
