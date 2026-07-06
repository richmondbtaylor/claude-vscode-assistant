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
