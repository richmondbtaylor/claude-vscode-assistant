"""
Interactive login script - runs in terminal, asks for code when needed.
"""
import os, sys, time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')
PASSCODE_PATH = os.path.join(os.path.dirname(__file__), '.passcode')

from playwright.sync_api import sync_playwright

user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_profile')

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=['--start-maximized'],
        viewport={'width': 1920, 'height': 1080},
    )
    page = context.pages[0] if context.pages else context.new_page()

    print("Navigating to LinkedIn login...")
    # Go to a neutral page first to clear any error state
    page.goto('https://www.linkedin.com/', wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)

    url = page.url
    print(f"Current URL: {url}")

    # Check if already logged in
    if 'feed' in url and 'login' not in url and 'uas' not in url:
        print("[OK] Already logged in!")
        context.close()
        sys.exit(0)

    # Navigate to login
    page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)
    url = page.url
    print(f"Login page URL: {url}")

    # Fill credentials
    try:
        page.fill('input[name="session_key"]', EMAIL)
        time.sleep(0.5)
        page.fill('input[name="session_password"]', PASSWORD)
        time.sleep(0.5)
        page.click('button[type="submit"]')
        print("[OK] Credentials submitted")
    except Exception as e:
        print(f"[!] Could not fill form: {e}")

    time.sleep(5)

    # Now poll
    code_requested = False
    i = 0
    while True:
        i += 1
        url = page.url
        print(f"[{i}s] URL: {url}", flush=True)

        # Success
        if ('linkedin.com/feed' in url or 'linkedin.com/mynetwork' in url) and 'login' not in url and 'uas' not in url:
            print("[OK] LOGGED IN SUCCESSFULLY!")
            # Save screenshot
            page.screenshot(path=os.path.join(os.path.dirname(__file__), 'logged_in.png'))
            context.close()
            sys.exit(0)

        # On checkpoint - need code
        if 'checkpoint' in url or 'challenge' in url:
            if 'global_internal_error' in url:
                print("[!] LinkedIn rate-limit error. Waiting 60s before retrying...")
                time.sleep(60)
                page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
                time.sleep(3)
                try:
                    page.fill('input[name="session_key"]', EMAIL)
                    time.sleep(0.5)
                    page.fill('input[name="session_password"]', PASSWORD)
                    time.sleep(0.5)
                    page.click('button[type="submit"]')
                    print("[OK] Credentials re-submitted")
                except Exception as e:
                    print(f"[!] Re-submit failed: {e}")
                time.sleep(5)
                continue

            if not code_requested:
                code_requested = True
                print("\n" + "="*50)
                print("VERIFICATION CODE NEEDED")
                print("Check your email/phone and paste the code here")
                print("="*50 + "\n", flush=True)

            # Check for code in .passcode file
            if os.path.exists(PASSCODE_PATH):
                with open(PASSCODE_PATH) as f:
                    code = f.read().strip()
                os.remove(PASSCODE_PATH)
                if code:
                    print(f"[*] Entering code: {code}")
                    # Find PIN input
                    for sel in ['input[autocomplete="one-time-code"]', 'input[name="pin"]:not([type="hidden"])', 'input[type="text"]:not([type="hidden"])']:
                        try:
                            el = page.query_selector(sel)
                            if el and el.is_visible():
                                el.click()
                                time.sleep(0.3)
                                el.fill(code)
                                time.sleep(0.5)
                                page.keyboard.press('Enter')
                                print("[*] Code submitted!")
                                time.sleep(5)
                                break
                        except Exception:
                            continue

        time.sleep(1)
