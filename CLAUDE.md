# Claude Code Global Rules

## Receipt Filing (Claude Code)

When the user shares a receipt image (any format), do the following — no need to ask:

1. **Read the image** using vision to extract: date (YYYY-MM-DD), vendor name, amount (numeric, no $), payment method
2. **Determine the tab**: `Bishop AI` for business expenses, `Prompt Anything` if clearly that brand, `Personal` for non-business
3. **Run the filer script**:
```
python C:\Users\richm\.claude\scripts\file_receipt.py "<image_path>" "<date>" "<vendor>" "<amount>" "<tab>" "<payment_method>"
```
4. Report the confirmation back to the user

The script handles Drive upload + Sheet logging automatically.
If the image was shared as a file attachment in Claude Code, it will be at a temp path — use that path directly.

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
