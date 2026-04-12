"""
Standalone LinkedIn login script — uses mouse coordinates to fill visible fields.
Saves session to linkedin_session/ for bot reuse.
"""
import time
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')

def login():
    with sync_playwright() as p:
        session_dir = os.path.join(os.path.dirname(__file__), 'linkedin_session')
        os.makedirs(session_dir, exist_ok=True)

        ctx = p.chromium.launch_persistent_context(
            session_dir,
            headless=False,
            ignore_https_errors=True,
            args=['--start-maximized', '--ignore-certificate-errors'],
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("Navigating to LinkedIn login...")
        page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
        time.sleep(4)

        url = page.url
        print(f"URL: {url}")

        if 'feed' in url or 'mynetwork' in url:
            print("[OK] Already logged in!")
            ctx.close()
            return True

        if 'checkpoint' in url or 'challenge' in url:
            print(f"[!] Challenge page: {url}")
            # Wait for manual resolution
            print("Waiting up to 5 min for challenge to be resolved...")
            for _ in range(100):
                time.sleep(3)
                u = page.url
                if 'feed' in u or 'mynetwork' in u:
                    print("[OK] Challenge resolved!")
                    ctx.close()
                    return True
            ctx.close()
            return False

        # Find visible inputs by bounding box
        print("Finding visible form fields...")
        result = page.evaluate("""() => {
            const allInputs = document.querySelectorAll('input');
            const fields = [];
            for (const inp of allInputs) {
                const r = inp.getBoundingClientRect();
                if (r.width > 50 && r.height > 10) {
                    fields.push({
                        type: inp.type,
                        x: r.left + r.width / 2,
                        y: r.top + r.height / 2,
                        w: r.width,
                        h: r.height
                    });
                }
            }
            return fields;
        }""")

        print(f"Visible fields: {result}")

        email_field = next((f for f in result if f['type'] in ('text', 'email')), None)
        password_field = next((f for f in result if f['type'] == 'password'), None)

        if not email_field or not password_field:
            print("[!] Could not find email or password field coordinates")
            page.screenshot(path='login_debug.png')
            print("Screenshot saved: login_debug.png")
            ctx.close()
            return False

        # Click email field at actual screen coordinates
        print(f"Clicking email at ({email_field['x']}, {email_field['y']})")
        page.mouse.click(email_field['x'], email_field['y'])
        time.sleep(0.5)
        page.keyboard.type(EMAIL, delay=80)
        time.sleep(0.5)

        # Click password field
        print(f"Clicking password at ({password_field['x']}, {password_field['y']})")
        page.mouse.click(password_field['x'], password_field['y'])
        time.sleep(0.5)
        page.keyboard.type(PASSWORD, delay=80)
        time.sleep(0.5)

        # Submit
        page.keyboard.press('Enter')
        print("Submitted. Waiting for redirect...")
        time.sleep(8)

        url = page.url
        print(f"Post-login URL: {url}")

        if 'feed' in url or 'mynetwork' in url:
            print("[OK] Logged in successfully! Session saved.")
            ctx.close()
            return True
        elif 'checkpoint' in url or 'challenge' in url:
            print(f"[!] Verification required: {url}")
            print("Waiting up to 5 min for verification...")
            # Write signal file
            with open(os.path.join(os.path.dirname(__file__), 'linkedin_needs_code.txt'), 'w') as f:
                f.write(url)
            for _ in range(100):
                time.sleep(3)
                u = page.url
                if 'feed' in u or 'mynetwork' in u:
                    print("[OK] Verified and logged in!")
                    ctx.close()
                    return True
                # Check for code file
                code_file = os.path.join(os.path.dirname(__file__), 'linkedin_code.txt')
                if os.path.exists(code_file):
                    with open(code_file) as cf:
                        code = cf.read().strip()
                    os.remove(code_file)
                    print(f"Entering code: {code}")
                    try:
                        code_input = page.locator('input[autocomplete="one-time-code"], input[type="number"], input[name="pin"]').first
                        code_input.fill(code, force=True)
                        page.keyboard.press('Enter')
                        time.sleep(5)
                        u2 = page.url
                        if 'feed' in u2 or 'mynetwork' in u2:
                            print("[OK] Code accepted!")
                            ctx.close()
                            return True
                    except Exception as e:
                        print(f"Code entry failed: {e}")
            ctx.close()
            return False
        else:
            print(f"[!] Unexpected URL: {url}")
            page.screenshot(path='login_debug.png')
            ctx.close()
            return False

if __name__ == '__main__':
    success = login()
    print(f"\nLogin {'SUCCEEDED' if success else 'FAILED'}")
