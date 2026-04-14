"""
LinkedIn login helper — saves session as storage_state.json (portable cookies).
Run from your own terminal:  python login.py
"""
import os, time, json
from playwright.sync_api import sync_playwright

PASSWORD       = 'Narsil202532?'
STATE_FILE     = os.path.join(os.path.dirname(__file__), 'storage_state.json')
PROFILE_DIR    = os.path.join(os.path.dirname(__file__), 'linkedin_profile_login')

os.makedirs(PROFILE_DIR, exist_ok=True)
print("Opening browser — log in to LinkedIn, then wait for the feed.")
print("The script saves your session automatically once you reach the feed.\n")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE_DIR, headless=False,
        args=['--start-maximized', '--disable-blink-features=AutomationControlled'],
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = ctx.new_page()
    page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)

    for i in range(120):
        time.sleep(5)
        url = page.url

        # Auto-fill password on remembered-email screen
        try:
            pw = page.query_selector('#password')
            un = page.query_selector('#username')
            if pw and pw.is_visible() and (not un or not un.is_visible()):
                pw.fill(PASSWORD)
                time.sleep(0.5)
                page.click('button[type=submit]')
                print("  Auto-filled password.")
                time.sleep(5)
                continue
        except Exception:
            pass

        on_feed = ('feed' in url or (
            'linkedin.com' in url
            and 'login' not in url
            and 'checkpoint' not in url
            and 'authwall' not in url
            and 'challenge' not in url
            and 'verify' not in url
        ))

        if on_feed:
            time.sleep(3)
            # Save portable storage state
            ctx.storage_state(path=STATE_FILE)
            ctx.close()
            # Verify li_at is in there
            with open(STATE_FILE) as f:
                state = json.load(f)
            cookies = {c['name']: c for c in state.get('cookies', [])}
            if 'li_at' in cookies:
                print(f"\nSession saved to storage_state.json (li_at present).")
            else:
                print(f"\nSession saved (li_at not found — may need re-login if bot fails).")
            print("Run: python main.py --now")
            break

        if i % 6 == 0:
            print(f"  [{i*5}s] {url[:70]}")
    else:
        ctx.close()
        print("Timed out.")
