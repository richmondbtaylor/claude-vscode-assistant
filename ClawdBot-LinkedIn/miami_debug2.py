"""
Debug: navigate to people search, dump buttons + first result card HTML.
Outputs to stdout (captured in task output file).
"""
import os, sys, time
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(__file__), "linkedin_session")

def p(s):
    print(s, flush=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        SESSION_DIR, headless=False,
        args=["--start-maximized"],
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # Go to people search with 1st connections
    url = "https://www.linkedin.com/search/results/people/?network=%5B%22F%22%5D"
    p(f"Navigating to: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(6)
    p(f"Current URL: {page.url}")

    # Screenshot
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "debug2_search.png"))
    p("Screenshot: debug2_search.png")

    # Dump ALL buttons
    btns = page.evaluate("""() => Array.from(document.querySelectorAll('button, [role=button]'))
        .filter(b => b.offsetParent !== null)
        .map(b => ({
            tag: b.tagName,
            text: (b.innerText||'').trim().slice(0,50),
            label: (b.getAttribute('aria-label')||'').slice(0,80),
            cls: (b.className||'').slice(0,60)
        }))
    """)
    p(f"\n=== Visible buttons/role=button ({len(btns)}) ===")
    for b in btns:
        safe = repr(b['text']) + " | " + repr(b['label'])
        p(f"  <{b['tag']}> {safe}")

    # Dump first result card HTML
    card_html = page.evaluate("""() => {
        const selectors = [
            '.reusable-search__result-container',
            'li.reusable-search__result-container',
            '[data-view-name*="search"]',
            'ul.reusable-search__entity-result-list > li',
            '.search-results-container li',
        ];
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) return {selector: sel, html: el.outerHTML.slice(0, 2000)};
        }
        // fallback: first li in main
        const main = document.querySelector('main');
        const li = main ? main.querySelector('li') : null;
        return li ? {selector: 'main li (fallback)', html: li.outerHTML.slice(0,2000)} : {selector: 'NONE', html: ''};
    }""")
    p(f"\n=== First result card (selector: {card_html['selector']}) ===")
    p(card_html['html'][:3000])

    # Also dump how many results we see with various selectors
    counts = page.evaluate("""() => {
        const sels = [
            '.reusable-search__result-container',
            'li.reusable-search__result-container',
            '[data-view-name]',
            '.entity-result',
            '.search-result',
            'ul > li',
            'main li',
        ];
        const out = {};
        for (const s of sels) out[s] = document.querySelectorAll(s).length;
        return out;
    }""")
    p("\n=== Selector hit counts ===")
    for sel, count in counts.items():
        p(f"  {repr(sel)}: {count}")

    ctx.close()
    p("\nDone.")
