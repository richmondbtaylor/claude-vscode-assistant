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

Playwright is available via `python -m playwright`. Write a temp async script: launch chromium, goto url, wait networkidle, return page content.

## Memory Enhancements

These rules override the auto-memory instructions where they conflict.

- **Project subtypes:** Label memories as `**Subtype:** experience` (facts/events/decisions) or `**Subtype:** mental-model` (patterns/strategies). Mental-models should be kept current; experiences can stale out.
- **Tag recalls:** Before acting on a recalled memory, classify it internally as `fresh` (verified), `assumed` (unverified -- check before acting), or `stale` (contradicted -- update/delete it first).
- **Reflect:** When 3+ experiences point at the same pattern, write a mental-model memory synthesizing them.
