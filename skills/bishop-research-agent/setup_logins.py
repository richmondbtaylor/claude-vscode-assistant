"""
Automated login setup for LinkedIn and Facebook Playwright sessions.
Fills credentials automatically and saves session files.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "bishop-research-agent.env")

SESSION_DIR = Path(__file__).parent / ".browser_sessions"
SESSION_DIR.mkdir(exist_ok=True)

LINKEDIN_SESSION = SESSION_DIR / "linkedin_session.json"
FACEBOOK_SESSION = SESSION_DIR / "facebook_session.json"


def setup_linkedin(pw):
    print("\n" + "=" * 50)
    print("  LINKEDIN LOGIN")
    print("=" * 50)
    email = os.environ.get("LINKEDIN_USERNAME", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")
    if not email or not password:
        print("[linkedin] No credentials in .env — skipping.")
        return False

    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    time.sleep(2)

    page.fill('input#username', email)
    page.fill('input#password', password)
    page.click('button[type="submit"]')
    print(f"[linkedin] Logging in as {email}...")
    print("[linkedin] Complete any security challenge in the browser if prompted...")

    # Wait up to 2 min for login + any security challenge
    for _ in range(60):
        time.sleep(2)
        url = page.url.lower()
        if "feed" in url or ("linkedin.com" in url and "login" not in url and "authwall" not in url and "challenge" not in url and "checkpoint" not in url):
            break
    else:
        print(f"[linkedin] Timed out. Last URL: {page.url}")
        browser.close()
        return False

    time.sleep(3)
    context.storage_state(path=str(LINKEDIN_SESSION))
    print(f"[linkedin] Session saved to {LINKEDIN_SESSION}")
    browser.close()
    return True


def setup_facebook(pw):
    print("\n" + "=" * 50)
    print("  FACEBOOK LOGIN")
    print("=" * 50)
    # Use same email as LinkedIn — typical for personal accounts
    email = os.environ.get("LINKEDIN_USERNAME", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")
    if not email or not password:
        print("[facebook] No credentials found — skipping.")
        return False

    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()
    page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
    time.sleep(3)

    # Try multiple selectors — FB login page varies
    try:
        page.fill('input#email', email, timeout=5000)
    except Exception:
        try:
            page.fill('input[name="email"]', email, timeout=5000)
        except Exception:
            print("[facebook] Could not find email field. Log in manually in the browser...")

    try:
        page.fill('input#pass', password, timeout=5000)
    except Exception:
        try:
            page.fill('input[name="pass"]', password, timeout=5000)
        except Exception:
            print("[facebook] Could not find password field. Log in manually in the browser...")

    try:
        page.click('button[name="login"]', timeout=5000)
    except Exception:
        print("[facebook] Could not find login button. Click it manually...")

    print(f"[facebook] Logging in as {email}...")
    print("[facebook] Complete any security checkpoint in the browser if prompted...")

    # Wait up to 2 min for login + any checkpoint
    for _ in range(60):
        time.sleep(2)
        url = page.url.lower()
        if "facebook.com" in url and "login" not in url and "checkpoint" not in url:
            break
    else:
        print(f"[facebook] Timed out. Last URL: {page.url}")
        browser.close()
        return False

    time.sleep(3)
    context.storage_state(path=str(FACEBOOK_SESSION))
    print(f"[facebook] Session saved to {FACEBOOK_SESSION}")
    browser.close()
    return True


if __name__ == "__main__":
    with sync_playwright() as pw:
        li = setup_linkedin(pw)
        fb = setup_facebook(pw)

    print("\n" + "=" * 50)
    print(f"  LinkedIn: {'OK' if li else 'FAILED'}")
    print(f"  Facebook: {'OK' if fb else 'FAILED'}")
    print("=" * 50)
