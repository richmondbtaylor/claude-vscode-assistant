import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    input_path = r"C:\Users\richm\.claude\exports\bishop-ai-agent-overview.html"
    output_path = r"C:\Users\richm\.claude\exports\bishop-ai-agent-overview.pdf"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1200, "height": 900})
        await page.goto(f"file:///{input_path.replace(chr(92), '/')}")
        await page.wait_for_load_state("networkidle")

        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()
        print(f"Saved: {output_path}")

asyncio.run(main())
