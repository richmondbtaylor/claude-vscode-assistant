"""
One-shot script: logs into Reddit via Playwright, creates a script app,
extracts client_id + client_secret, and writes them to .env.
"""
import os
import re
import time
from dotenv import load_dotenv, set_key
from playwright.sync_api import sync_playwright

load_dotenv()

REDDIT_EMAIL = os.environ.get("REDDIT_USERNAME", "richmond@richmondbishop.com")
REDDIT_PASS  = os.environ.get("REDDIT_PASSWORD", "")
ENV_FILE     = os.path.join(os.path.dirname(__file__), ".env")
APP_NAME     = "BishopAI"
REDIRECT_URI = "http://localhost:8080"


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=80)
        ctx = browser.new_context()
        page = ctx.new_page()

        # ── Step 1: Log in ──────────────────────────────────────────────────
        print("[reddit] Navigating to login page...")
        page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
        time.sleep(3)

        # Fill email
        for selector in ['input[name="username"]', 'faceplate-text-input input']:
            try:
                el = page.locator(selector).first
                el.wait_for(timeout=5000)
                el.click()
                el.fill(REDDIT_EMAIL)
                print(f"  Filled email using: {selector}")
                break
            except Exception:
                continue

        time.sleep(0.5)

        # Fill password
        for selector in ['input[name="password"]', 'input[type="password"]']:
            try:
                el = page.locator(selector).first
                el.wait_for(timeout=3000)
                el.click()
                el.fill(REDDIT_PASS)
                print(f"  Filled password using: {selector}")
                break
            except Exception:
                continue

        time.sleep(0.5)

        # Submit
        try:
            page.locator('button[type="submit"]').first.click(timeout=3000)
        except Exception:
            page.keyboard.press("Enter")

        print("[reddit] Waiting for login redirect...")
        time.sleep(8)

        if "login" in page.url:
            print(f"\n[!] Still on login page: {page.url}")
            print("    Please log in manually in the browser window, then press Enter here.")
            input("    Press ENTER once you're logged in: ")

        print(f"[reddit] Current URL: {page.url}")

        # Get actual username from the page
        username = None
        try:
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
            time.sleep(2)
            # Try to find username in page source
            content = page.content()
            m = re.search(r'"name"\s*:\s*"([^"]+)"', content)
            if m:
                username = m.group(1)
                print(f"[reddit] Logged in as: {username}")
        except Exception as e:
            print(f"[reddit] Could not detect username: {e}")

        # ── Step 2: Go to app preferences ──────────────────────────────────
        print("[reddit] Going to app preferences...")
        page.goto("https://www.reddit.com/prefs/apps", wait_until="domcontentloaded")
        time.sleep(3)

        # ── Step 3: Check if BishopAI app already exists ───────────────────
        existing = page.locator(f'text="{APP_NAME}"').first
        if existing.is_visible(timeout=2000):
            print(f"[reddit] App '{APP_NAME}' already exists — reading credentials...")
        else:
            # ── Step 4: Create the app ──────────────────────────────────────
            print(f"[reddit] Creating app '{APP_NAME}'...")

            try:
                create_btn = page.locator('button:has-text("create another app"), button:has-text("create app")').first
                create_btn.click(timeout=5000)
                time.sleep(2)
            except Exception:
                print("[!] Could not find 'create app' button — please click it manually.")
                input("    Press ENTER once the form is visible: ")

            # Fill form
            page.locator('input[name="name"]').first.fill(APP_NAME)
            time.sleep(0.3)

            # Select "script" type
            try:
                page.locator('input[value="script"]').first.click()
            except Exception:
                page.locator('label:has-text("script")').first.click()
            time.sleep(0.3)

            # Redirect URI
            try:
                page.locator('input[name="redirect_uri"]').first.fill(REDIRECT_URI)
            except Exception:
                page.locator('input[placeholder*="redirect"]').first.fill(REDIRECT_URI)
            time.sleep(0.3)

            # Submit
            page.locator('button[type="submit"]:has-text("create app")').first.click()
            time.sleep(3)

        # ── Step 5: Extract client_id and client_secret ─────────────────────
        print("[reddit] Extracting credentials...")
        page_html = page.content()

        # Find the app section for BishopAI
        client_id = None
        client_secret = None

        # client_id appears as text directly under the app name
        try:
            # The client ID is the text in the <code> or small element after app name
            app_section = page.locator(f'.developed-app:has-text("{APP_NAME}"), .app:has-text("{APP_NAME}")').first
            if not app_section.is_visible(timeout=3000):
                app_section = page.locator(f'*:has-text("{APP_NAME}")').nth(1)

            # Take screenshot to help debug if needed
            page.screenshot(path="reddit_apps_page.png")
            print("  Screenshot saved: reddit_apps_page.png")
        except Exception as e:
            print(f"  Could not isolate app section: {e}")

        # Try multiple extraction patterns
        patterns = [
            (r'client[_\s]?id["\s:]+([a-zA-Z0-9_\-]{10,30})', 'client_id pattern'),
            (r'"app_id"\s*:\s*"([^"]+)"', 'app_id pattern'),
        ]

        for pattern, name in patterns:
            m = re.search(pattern, page_html, re.IGNORECASE)
            if m and not client_id:
                client_id = m.group(1)
                print(f"  Found client_id via {name}: {client_id}")

        secret_patterns = [
            (r'secret["\s:]+([a-zA-Z0-9_\-]{20,50})', 'secret pattern'),
            (r'"secret"\s*:\s*"([^"]+)"', 'json secret'),
        ]
        for pattern, name in secret_patterns:
            m = re.search(pattern, page_html, re.IGNORECASE)
            if m and not client_secret:
                client_secret = m.group(1)
                print(f"  Found client_secret via {name}: {client_secret[:8]}...")

        if not client_id or not client_secret:
            print("\n[!] Could not auto-extract credentials from page.")
            print("    The browser is still open — please copy the values manually.")
            client_id = input("    Paste CLIENT_ID: ").strip()
            client_secret = input("    Paste CLIENT_SECRET: ").strip()

        if not username:
            username = input("    Paste your Reddit USERNAME (the u/ handle): ").strip()

        # ── Step 6: Write to .env ───────────────────────────────────────────
        print(f"\n[env] Writing to {ENV_FILE}...")
        set_key(ENV_FILE, "REDDIT_CLIENT_ID", client_id)
        set_key(ENV_FILE, "REDDIT_CLIENT_SECRET", client_secret)
        if username:
            set_key(ENV_FILE, "REDDIT_USERNAME", username)

        print("\n✓ Done! Credentials saved to .env:")
        print(f"  REDDIT_CLIENT_ID     = {client_id}")
        print(f"  REDDIT_CLIENT_SECRET = {client_secret[:8]}...")
        print(f"  REDDIT_USERNAME      = {username}")

        browser.close()


if __name__ == "__main__":
    run()
