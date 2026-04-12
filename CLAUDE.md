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

## Memory Enhancements (supplements the auto-memory system)

These rules extend — they do not replace — the auto-memory instructions. Where they conflict, these win.

### 1. Split `project` memories into two subtypes

When saving a `project` memory, decide which subtype it is and label it in the body:

- **experience** — something that happened or was decided (a fact, an event, a deadline, a stakeholder ask). Static, dated, observable.
  - Example: "2026-04-08 — user decided not to install Hindsight; current markdown memory is sufficient at this scale."
- **mental-model** — a synthesized belief, strategy, or pattern that informs future judgment. Dynamic, refinable.
  - Example: "Vector-based memory systems only pay off above ~hundreds of entries; below that, keyword-indexed markdown is faster and greppable."

Both still use `type: project` in frontmatter — add a `**Subtype:** experience` or `**Subtype:** mental-model` line at the top of the body. Mental-models are more valuable to keep updated; experiences can stale out and get archived.

### 2. Use Retain / Recall / Reflect as the explicit verbs

When working with memory, narrate which operation is happening (in your own thinking, not necessarily user-facing):

- **Retain** — extracting and saving a new memory. Ask: is this surprising? non-derivable from code? worth future-me's time?
- **Recall** — pulling a memory into the current context. Ask: is this still likely true? Does the current code/state agree?
- **Reflect** — reasoning over multiple memories to form or update a mental-model. This is when you should consider *writing* a new mental-model memory that synthesizes what you've learned across several experiences.

If three or more `experience` memories point at the same pattern, that's a signal to **Reflect** and write a `mental-model` memory that captures the pattern.

### 3. Tag confidence and staleness on recall

When recalling a memory that names a specific file, function, flag, person, or date, before acting on it note (internally) one of:

- **fresh** — verified this conversation, safe to act on
- **assumed** — not verified, treat as a hint not a fact; verify before any user-visible action
- **stale** — contradicted by current state; update or delete the memory now, do not act on it

Never recommend, edit, or message based on an `assumed` memory without verifying first. If you find a `stale` memory, fixing the memory is part of the current task — do it before continuing.
