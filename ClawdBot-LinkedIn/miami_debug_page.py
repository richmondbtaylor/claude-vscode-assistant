"""Debug: screenshot + HTML dump of the connections page."""
import os, time
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(__file__), "linkedin_session")
OUT_DIR = os.path.dirname(__file__)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        SESSION_DIR, headless=False, ignore_https_errors=True,
        args=["--start-maximized"],
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    page.goto("https://www.linkedin.com/mynetwork/invite-connect/connections/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(6)

    page.screenshot(path=os.path.join(OUT_DIR, "connections_page.png"), full_page=False)
    print("Screenshot saved: connections_page.png")

    # Dump buttons
    buttons = page.evaluate("""() => Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null).map(b => ({
        text: b.innerText.trim().slice(0, 60),
        label: (b.getAttribute('aria-label') || '').slice(0, 80),
        cls: (b.className || '').slice(0, 80)
    }))""")
    print(f"\n=== Visible buttons ({len(buttons)}) ===")
    for b in buttons:
        print(f"  text='{b['text']}' | label='{b['label']}'")

    # Dump first 5 list items / cards
    cards = page.evaluate("""() => {
        const all = document.querySelectorAll('li, article, [class*="connection"], [class*="member"]');
        const out = [];
        for (const el of all) {
            const txt = el.innerText.trim().slice(0, 120).replace(/\\n/g, ' | ');
            const cls = (el.className || '').slice(0, 80);
            if (txt.length > 10) out.push({tag: el.tagName, cls, txt});
            if (out.length >= 20) break;
        }
        return out;
    }""")
    print(f"\n=== First 20 list-like elements ===")
    for c in cards:
        print(f"  <{c['tag']} class='{c['cls']}'> {c['txt']}")

    # Save full HTML snippet of main content
    html = page.evaluate("""() => {
        const main = document.querySelector('main') || document.querySelector('[role=main]') || document.body;
        return main.innerHTML.slice(0, 8000);
    }""")
    with open(os.path.join(OUT_DIR, "connections_page.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("\nHTML snippet saved: connections_page.html")

    input("\nPress Enter to close...")
    ctx.close()
