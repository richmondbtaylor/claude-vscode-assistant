"""Open a browser for LinkedIn login, auto-saves after detecting li_at auth cookie."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "linkedin.json"
SESSION_FILE.parent.mkdir(exist_ok=True)

print("Opening LinkedIn login browser...")
print("You have 180 seconds to log in. The session saves automatically once authenticated.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://www.linkedin.com/login")

    for i in range(180):
        time.sleep(1)
        try:
            url = page.url.lower()
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        except Exception:
            break
        if i % 10 == 0:
            authed = "li_at" in cookies
            print(f"  {180 - i}s remaining... url={url[:60]} | authenticated={authed}")
        if "li_at" in cookies:
            print("  Authenticated (li_at cookie found)! Saving session...")
            time.sleep(3)
            break

    ctx.storage_state(path=str(SESSION_FILE))
    print(f"Session saved to {SESSION_FILE}")
    browser.close()
