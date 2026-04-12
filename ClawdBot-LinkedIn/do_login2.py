"""
LinkedIn login script v2 - clicks Sign In button explicitly
"""
import asyncio
import os
import sys
import time

EMAIL = "richmondbtaylor@gmail.com"
PASSWORD = "Narsil202532?"
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_session')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def kill_chrome():
    import subprocess
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                   capture_output=True, shell=True)
    time.sleep(2)

def remove_lock(session_dir):
    for fname in ['SingletonLock', 'lockfile', 'SingletonSocket', 'SingletonCookie']:
        path = os.path.join(session_dir, fname)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[OK] Removed {fname}")
            except Exception as e:
                print(f"[!] Could not remove {fname}: {e}")

def main():
    kill_chrome()
    os.makedirs(SESSION_DIR, exist_ok=True)
    remove_lock(SESSION_DIR)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print("[*] Launching browser...")
        context = p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=False,
            ignore_https_errors=True,
            args=[
                '--start-maximized',
                '--ignore-certificate-errors',
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ],
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        page = context.new_page() if not context.pages else context.pages[0]

        # Go to feed first to check if already logged in
        print("[*] Checking if already logged in...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(3)
        url = page.url
        print(f"[*] URL: {url}")

        if url.startswith('https://www.linkedin.com/feed') or url.startswith('https://www.linkedin.com/mynetwork'):
            print("[OK] Already logged in! Session is active.")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_success.png'))
            context.close()
            return True

        # Go to login page
        print("[*] Navigating to login page...")
        page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
        time.sleep(3)
        url = page.url
        print(f"[*] URL after login nav: {url}")

        if 'checkpoint' in url or 'challenge' in url or 'verification' in url:
            print("[!] VERIFICATION REQUIRED - need code from user")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_debug.png'))
            # Signal file for code
            with open(os.path.join(SCRIPT_DIR, 'linkedin_needs_code.txt'), 'w') as f:
                f.write('VERIFICATION')
            print("[!] Wrote linkedin_needs_code.txt - waiting for code in linkedin_code.txt")
            wait_for_code_and_handle(page, context)
            return True

        if url.startswith('https://www.linkedin.com/feed') or url.startswith('https://www.linkedin.com/mynetwork'):
            print("[OK] Already logged in (redirect)!")
            context.close()
            return True

        # Find visible input fields
        print("[*] Finding visible input fields...")
        result = page.evaluate("""() => {
            const allInputs = document.querySelectorAll('input');
            const fields = [];
            for (const inp of allInputs) {
                const r = inp.getBoundingClientRect();
                if (r.width > 50 && r.height > 10) {
                    const style = window.getComputedStyle(inp);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        fields.push({
                            type: inp.type,
                            id: inp.id,
                            name: inp.name,
                            autocomplete: inp.autocomplete,
                            x: r.left + r.width/2,
                            y: r.top + r.height/2,
                            width: r.width,
                            height: r.height
                        });
                    }
                }
            }
            return fields;
        }""")
        print(f"[*] Found {len(result)} visible fields: {result}")

        # Find email and password fields
        email_field = None
        password_field = None
        for f in result:
            if f['type'] in ('email', 'text') and email_field is None:
                email_field = f
            elif f['type'] == 'password' and password_field is None:
                password_field = f

        if not email_field or not password_field:
            print("[X] Could not find email/password fields")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_debug.png'))
            context.close()
            return False

        print(f"[*] Email field: x={email_field['x']:.0f}, y={email_field['y']:.0f}")
        print(f"[*] Password field: x={password_field['x']:.0f}, y={password_field['y']:.0f}")

        # Click email field and type
        print("[*] Filling email...")
        page.mouse.click(email_field['x'], email_field['y'])
        time.sleep(0.5)
        # Clear any existing content
        page.keyboard.press('Control+a')
        page.keyboard.press('Delete')
        time.sleep(0.3)
        page.keyboard.type(EMAIL, delay=80)
        time.sleep(0.5)

        # Tab to password field
        page.keyboard.press('Tab')
        time.sleep(0.5)

        # Also click on password field directly
        page.mouse.click(password_field['x'], password_field['y'])
        time.sleep(0.5)
        page.keyboard.press('Control+a')
        page.keyboard.press('Delete')
        time.sleep(0.3)
        page.keyboard.type(PASSWORD, delay=80)
        time.sleep(0.5)

        # Find and click the Sign In button
        print("[*] Looking for Sign In button...")
        btn_info = page.evaluate("""() => {
            // Look for submit button
            const buttons = document.querySelectorAll('button[type="submit"], button.btn__primary--large, button[aria-label*="Sign"], button[aria-label*="sign"]');
            for (const btn of buttons) {
                const r = btn.getBoundingClientRect();
                if (r.width > 50 && r.height > 10) {
                    const style = window.getComputedStyle(btn);
                    if (style.display !== 'none') {
                        return {x: r.left + r.width/2, y: r.top + r.height/2, text: btn.textContent.trim()};
                    }
                }
            }
            // Fallback: find by text
            const allBtns = document.querySelectorAll('button');
            for (const btn of allBtns) {
                if (btn.textContent.trim().toLowerCase() === 'sign in') {
                    const r = btn.getBoundingClientRect();
                    if (r.width > 50) {
                        return {x: r.left + r.width/2, y: r.top + r.height/2, text: btn.textContent.trim()};
                    }
                }
            }
            return null;
        }""")

        if btn_info:
            print(f"[*] Sign In button at x={btn_info['x']:.0f}, y={btn_info['y']:.0f} text='{btn_info['text']}'")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'before_submit.png'))
            page.mouse.click(btn_info['x'], btn_info['y'])
            print("[*] Clicked Sign In button, waiting for navigation...")
        else:
            print("[!] No button found, pressing Enter...")
            page.mouse.click(password_field['x'], password_field['y'])
            page.keyboard.press('Enter')
            print("[*] Pressed Enter, waiting for navigation...")

        # Wait for navigation
        time.sleep(8)
        url = page.url
        print(f"[*] URL after submit: {url}")
        page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_debug.png'))

        if url.startswith('https://www.linkedin.com/feed') or url.startswith('https://www.linkedin.com/mynetwork'):
            print("[OK] LOGIN SUCCESS!")
            context.close()
            return True

        if 'checkpoint' in url or 'challenge' in url or 'verification' in url:
            print("[!] VERIFICATION REQUIRED")
            wait_for_code_and_handle(page, context)
            return True

        if '/login' in url:
            print("[X] Still on login page - checking for error message...")
            error = page.evaluate("""() => {
                const errs = document.querySelectorAll('.alert-content, [role="alert"], .error-for-username, .error-for-password, #error-for-username, #error-for-password');
                for (const e of errs) {
                    if (e.textContent.trim()) return e.textContent.trim();
                }
                return null;
            }""")
            if error:
                print(f"[X] LinkedIn error: {error}")
            else:
                print("[X] No error message found - login silently failed")

            # Try waiting longer - sometimes LinkedIn redirects after delay
            print("[*] Waiting 10 more seconds...")
            time.sleep(10)
            url = page.url
            print(f"[*] URL after extra wait: {url}")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_debug2.png'))

            if url.startswith('https://www.linkedin.com/feed') or url.startswith('https://www.linkedin.com/mynetwork'):
                print("[OK] LOGIN SUCCESS (delayed)!")
                context.close()
                return True

            print("[X] Login failed. See login_debug.png and login_debug2.png")
            # Keep browser open for manual intervention
            print("[!] Browser staying open - log in manually if needed")
            print("[!] Write 'done' to linkedin_code.txt when logged in")
            wait_for_manual_signal(page)

        context.close()
        return False


def wait_for_code_and_handle(page, context):
    """Wait for user to provide verification code via file."""
    code_file = os.path.join(SCRIPT_DIR, 'linkedin_code.txt')
    print("[!] Waiting up to 5 minutes for verification code in linkedin_code.txt")
    for i in range(100):
        if os.path.exists(code_file):
            with open(code_file) as f:
                code = f.read().strip()
            os.remove(code_file)
            if code.lower() == 'done':
                print("[OK] User signaled done")
                break
            print(f"[*] Got code: {code}")
            # Type the code
            page.keyboard.type(code)
            time.sleep(0.5)
            page.keyboard.press('Enter')
            time.sleep(5)
            url = page.url
            print(f"[*] URL after code: {url}")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_debug.png'))
            break
        time.sleep(3)
    context.close()


def wait_for_manual_signal(page):
    """Keep browser open, wait for user to write 'done' to linkedin_code.txt."""
    code_file = os.path.join(SCRIPT_DIR, 'linkedin_code.txt')
    for i in range(200):
        if os.path.exists(code_file):
            with open(code_file) as f:
                content = f.read().strip()
            os.remove(code_file)
            if content.lower() == 'done':
                url = page.url
                print(f"[OK] Manual signal received. URL: {url}")
                break
        try:
            url = page.url
            if url.startswith('https://www.linkedin.com/feed') or url.startswith('https://www.linkedin.com/mynetwork'):
                print(f"[OK] Detected navigation to feed!")
                break
        except:
            pass
        time.sleep(3)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
