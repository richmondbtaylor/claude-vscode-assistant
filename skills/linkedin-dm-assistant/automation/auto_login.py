"""
Automated LinkedIn login with SMS verification support.
Signal-file approach: when verification is needed, writes waiting_for_code.txt
then polls for verification_code.txt containing the code to enter.
This allows Claude Code (or any external process) to supply the code.
"""
import os, json, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
cookies_file = os.getenv('LINKEDIN_COOKIES_FILE', './linkedin_cookies.json')

WAITING_FILE = './waiting_for_code.txt'
CODE_FILE = './verification_code.txt'

# Clean up any leftover signal files from previous runs
for f in [WAITING_FILE, CODE_FILE]:
    if os.path.exists(f):
        os.remove(f)

def try_enter_code(page, code):
    """Try multiple selectors for the LinkedIn verification PIN field."""
    code = code.strip()
    selectors = [
        'input[name="pin"]',
        '#input__phone_verification_pin',
        'input[autocomplete="one-time-code"]',
        'input[type="number"]',
        'input[type="text"][name!="session_key"][name!="session_password"]',
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.fill(code)
                time.sleep(0.5)
                # Try clicking submit
                submit = page.query_selector('button[type="submit"], button[aria-label*="Submit"], button[aria-label*="Verify"]')
                if submit:
                    submit.click()
                else:
                    el.press('Enter')
                print(f'  Entered code via selector: {sel}')
                return True
        except Exception as e:
            print(f'  Selector {sel} failed: {e}')
    return False


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=80)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    max_login_attempts = 3
    logged_in = False

    for attempt in range(1, max_login_attempts + 1):
        print(f'Login attempt {attempt}/{max_login_attempts}...')
        page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)

        try:
            page.wait_for_selector('#username', timeout=20000)
        except Exception:
            print('  Could not find login form — taking screenshot')
            page.screenshot(path=f'login_attempt_{attempt}.png')
            time.sleep(3)
            continue

        time.sleep(1)
        page.fill('#username', email)
        time.sleep(0.6)
        page.fill('#password', password)
        time.sleep(0.6)
        page.click('button[type=submit]')
        time.sleep(5)

        current_url = page.url
        print(f'URL after login: {current_url}')

        # Successfully logged in
        if 'feed' in current_url or 'mynetwork' in current_url or 'jobs' in current_url:
            print('Logged in successfully!')
            logged_in = True
            break

        # Error checkpoint (bot detection) — retry
        if 'challenge_global_internal_error' in current_url or 'errorKey' in current_url:
            print(f'  Bot detection error on attempt {attempt}. Waiting 15s before retry...')
            page.screenshot(path=f'login_error_{attempt}.png')
            time.sleep(15)
            continue

        # Real verification challenge — need SMS code
        if 'checkpoint' in current_url or 'challenge' in current_url:
            print()
            print('=' * 60)
            print('VERIFICATION REQUIRED')
            print('A verification code has been sent to your phone.')
            print()
            print('>> Give the code to Claude Code and it will enter it automatically.')
            print('>> Waiting for verification_code.txt ...')
            print('=' * 60)

            # Take screenshot so we can see what the verification page looks like
            page.screenshot(path='verification_page.png')
            print('  Screenshot saved to verification_page.png')

            # Signal that we need the code
            with open(WAITING_FILE, 'w') as f:
                f.write(f'url={current_url}\ntime={time.time()}')

            # Poll for the code file (up to 5 minutes)
            code_entered = False
            for i in range(100):  # 100 * 3s = 5 minutes
                time.sleep(3)

                if os.path.exists(CODE_FILE):
                    with open(CODE_FILE) as f:
                        code = f.read().strip()
                    os.remove(CODE_FILE)
                    if os.path.exists(WAITING_FILE):
                        os.remove(WAITING_FILE)

                    print(f'  Got code: {code} — entering...')
                    success = try_enter_code(page, code)
                    if success:
                        time.sleep(5)
                        final_url = page.url
                        print(f'  URL after code entry: {final_url}')
                        if 'checkpoint' not in final_url and 'challenge' not in final_url and 'login' not in final_url:
                            print('Verification complete!')
                            logged_in = True
                        else:
                            print('  Still on checkpoint page — code may have been wrong')
                    else:
                        print('  Could not find PIN input field — screenshot saved')
                        page.screenshot(path='after_code_attempt.png')
                    code_entered = True
                    break

                # Also check if URL changed (user typed in browser manually)
                url = page.url
                if 'checkpoint' not in url and 'challenge' not in url and 'login' not in url:
                    print(f'  URL changed — verification complete! {url}')
                    if os.path.exists(WAITING_FILE):
                        os.remove(WAITING_FILE)
                    logged_in = True
                    code_entered = True
                    break

                if i % 10 == 9:
                    print(f'  Still waiting for code... ({(i+1)*3}s elapsed)')

            if not code_entered:
                print('Timed out waiting for verification code.')

            break  # Don't retry after hitting the real verification page

    print(f'\nFinal URL: {page.url}')
    cookies = context.cookies()
    with open(cookies_file, 'w') as f:
        json.dump(cookies, f, indent=2)

    li_at = next((c for c in cookies if c['name'] == 'li_at'), None)
    print(f'Saved {len(cookies)} cookies to {cookies_file}')
    print(f'li_at cookie present: {li_at is not None}')
    if logged_in:
        print('SUCCESS: Session authenticated.')
    else:
        print('WARNING: Session may not be fully authenticated.')

    browser.close()
