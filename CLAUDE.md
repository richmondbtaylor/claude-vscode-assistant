# Claude Code Global Rules

## Web Access Fallback

When WebFetch fails to access a URL (due to authentication, JavaScript rendering, redirects, or any other reason), automatically fall back to Playwright to fetch the content instead. Write and run a temporary Python Playwright script to load the page, wait for content to render, and extract the needed data. Do not ask permission — just use Playwright as the fallback.

Playwright is available at: `playwright` (via `python -m playwright` or the `playwright` CLI)
Python packages available: `playwright`, `asyncio`

Example fallback pattern:
```python
import asyncio
from playwright.async_api import async_playwright

async def fetch(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        content = await page.content()
        await browser.close()
        return content

asyncio.run(fetch("URL_HERE"))
```
