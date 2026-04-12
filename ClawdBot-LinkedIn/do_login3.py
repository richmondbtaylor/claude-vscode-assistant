"""
LinkedIn login script v3 - properly handles verification code entry
"""
import os
import sys
import time

EMAIL = "richmondbtaylor@gmail.com"
PASSWORD = "Narsil202532?"
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_session')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_FILE = os.path.join(SCRIPT_DIR, 'linkedin_code.txt')
SIGNAL_FILE = os.path.join(SCRIPT_DIR, 'linkedin_needs_code.txt')


def kill_chrome():
    import subprocess
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                   capture_output=True, shell=True)
    time.sleep(2)


def remove_lock(d):
    for fname in ['SingletonLock', 'lockfile', 'SingletonSocket', 'SingletonCookie']:
        p = os.path.join(d, fname)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def wait_for_url_change(page, not_containing='/login', timeout=45):
    """Poll until URL no longer contains the given string."""
    for _ in range(timeout):
        try:
            url = page.url
            if not_containing not in url:
                return url
        except Exception:
            pass
        time.sleep(1)
    return page.url


def is_feed(url):
    return (url.startswith('https://www.linkedin.com/feed') or
            url.startswith('https://www.linkedin.com/mynetwork'))


def is_verification(url):
    keywords = ['checkpoint', 'challenge', 'verification', 'pin', 'uas/login']
    return any(k in url for k in keywords)


def read_code_from_file(timeout=300):
    """Wait for user to write code to linkedin_code.txt. Returns the code or None."""
    print("[!] Waiting for code in linkedin_code.txt (up to {}s)...".format(timeout))
    for _ in range(timeout // 2):
        if os.path.exists(CODE_FILE):
            with open(CODE_FILE) as f:
                code = f.read().strip()
            os.remove(CODE_FILE)
            return code
        time.sleep(2)
    return None


def enter_verification_code(page, code):
    """Find the code input on verification page and submit."""
    print(f"[*] Entering verification code: {code}")
    # Find the code input field
    fields = page.evaluate("""() => {
        const inputs = document.querySelectorAll('input');
        const results = [];
        for (const inp of inputs) {
            const r = inp.getBoundingClientRect();
            if (r.width > 30 && r.height > 10) {
                results.push({
                    type: inp.type,
                    x: r.left + r.width/2,
                    y: r.top + r.height/2
                });
            }
        }
        return results;
    }""")
    print(f"[*] Found {len(fields)} input fields on verification page")

    if not fields:
        print("[X] No input fields found on verification page")
        return False

    # Click first visible input and type code
    field = fields[0]
    page.mouse.click(field['x'], field['y'])
    time.sleep(0.5)
    page.keyboard.press('Control+a')
    page.keyboard.press('Delete')
    page.keyboard.type(code, delay=100)
    time.sleep(0.5)

    # Find and click Submit button
    btn = page.evaluate("""() => {
        const btns = document.querySelectorAll('button[type="submit"], button');
        for (const b of btns) {
            const t = b.textContent.trim().toLowerCase();
            if (t === 'submit' || t === 'verify' || t === 'continue') {
                const r = b.getBoundingClientRect();
                if (r.width > 30) return {x: r.left + r.width/2, y: r.top + r.height/2, text: b.textContent.trim()};
            }
        }
        return null;
    }""")

    if btn:
        print(f"[*] Clicking '{btn['text']}' button")
        page.mouse.click(btn['x'], btn['y'])
    else:
        print("[*] No submit button found, pressing Enter")
        page.keyboard.press('Enter')

    return True


def main():
    kill_chrome()
    os.makedirs(SESSION_DIR, exist_ok=True)
    remove_lock(SESSION_DIR)

    # Clean up old signal files
    for f in [CODE_FILE, SIGNAL_FILE]:
        if os.path.exists(f):
            os.remove(f)

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
            ],
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Check if already logged in
        print("[*] Checking existing session...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(4)
        url = page.url
        print(f"[*] URL: {url}")

        if is_feed(url):
            print("[OK] Already logged in!")
            page.screenshot(path=os.path.join(SCRIPT_DIR, 'login_success.png'))
            context.close()
            return True

        # Go to login
        print("[*] Navigating to login page...")
        page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
        time.sleep(3)
        url = page.url
        print(f"[*] Login page URL: {url}")

        if is_feed(url):
            print("[OK] Already logged in (redirect)!")
            context.close()
            return True

        # Fill credentials
        print("[*] Finding form fields...")
        fields = page.evaluate("""() => {
            const inputs = document.querySelectorAll('input');
            const visible = [];
            for (const inp of inputs) {
                const r = inp.getBoundingClientRect();
                const style = window.getComputedStyle(inp);
                if (r.width > 50 && r.height > 10 && style.display !== 'none' && style.visibility !== 'hidden') {
                    visible.push({type: inp.type, x: r.left + r.width/2, y: r.top + r.height/2});
                }
            }
            return visible;
        }""")
        print(f"[*] Visible fields: {fields}")

        email_f = next((f for f in fields if f['type'] in ('email', 'text')), None)
        pass_f = next((f for f in fields if f['type'] == 'password'), None)

        if not email_f or not pass_f:
            print("[X] Cannot find email/password fields")
            context.close()
            return False

        # Type email
        page.mouse.click(email_f['x'], email_f['y'])
        time.sleep(0.4)
        page.keyboard.press('Control+a')
        page.keyboard.press('Delete')
        page.keyboard.type(EMAIL, delay=80)
        time.sleep(0.4)

        # Type password
        page.mouse.click(pass_f['x'], pass_f['y'])
        time.sleep(0.4)
        page.keyboard.press('Control+a')
        page.keyboard.press('Delete')
        page.keyboard.type(PASSWORD, delay=80)
        time.sleep(0.4)

        # Click Sign In button
        btn = page.evaluate("""() => {
            for (const b of document.querySelectorAll('button[type="submit"], button')) {
                if (b.textContent.trim().toLowerCase() === 'sign in') {
                    const r = b.getBoundingClientRect();
                    if (r.width > 50) return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        }""")

        page.screenshot(path=os.path.join(SCRIPT_DIR, 'before_submit.png'))

        if btn:
            print(f"[*] Clicking Sign In at ({btn['x']:.0f}, {btn['y']:.0f})")
            page.mouse.click(btn['x'], btn['y'])
        else:
            print("[*] No Sign In button found, pressing Enter")
            page.keyboard.press('Enter')

        # Wait for URL to change away from /login
        print("[*] Waiting for page navigation (up to 45s)...")
        url = wait_for_url_change(page, not_containing='/login', timeout=45)
        print(f"[*] URL after navigation: {url}")
        page.screenshot(path=os.path.join(SCRIPT_DIR, 'post_submit.png'))

        if is_feed(url):
            print("[OK] LOGIN SUCCESS!")
            context.close()
            return True

        # Check for verification
        if is_verification(url):
            print("[!] VERIFICATION PAGE DETECTED")
            handle_verification_flow(page, context)
            return True

        # Still on login — might be slow redirect, wait more
        print(f"[*] Still on login area, waiting 20 more seconds...")
        time.sleep(20)
        url = page.url
        print(f"[*] URL after extra wait: {url}")
        page.screenshot(path=os.path.join(SCRIPT_DIR, 'post_submit2.png'))

        if is_feed(url):
            print("[OK] LOGIN SUCCESS (delayed)!")
            context.close()
            return True

        if is_verification(url):
            print("[!] VERIFICATION PAGE DETECTED")
            handle_verification_flow(page, context)
            return True

        # Check if page content shows verification (URL might differ)
        page_text = page.evaluate("() => document.body.innerText")
        if 'Enter the code' in page_text or 'verification' in page_text.lower() or 'sent to' in page_text.lower():
            print("[!] Verification content detected on page")
            handle_verification_flow(page, context)
            return True

        print(f"[X] Unknown state. URL={url}")
        print("[!] Check post_submit2.png for current page state")
        context.close()
        return False


def handle_verification_flow(page, context):
    """Signal for code, enter it, submit."""
    # Signal to user
    with open(SIGNAL_FILE, 'w') as f:
        f.write('NEEDS_CODE')
    print("[!] NEEDS_CODE: Please provide LinkedIn verification code.")
    print("[!] Write the code to: linkedin_code.txt")
    print("[!] Example: echo 123456 > linkedin_code.txt")

    code = read_code_from_file(timeout=300)
    if not code:
        print("[X] No code received within timeout")
        context.close()
        return

    print(f"[*] Got code: {code}")
    success = enter_verification_code(page, code)

    if success:
        time.sleep(8)
        url = page.url
        print(f"[*] URL after code entry: {url}")
        page.screenshot(path=os.path.join(SCRIPT_DIR, 'post_code.png'))

        if is_feed(url):
            print("[OK] FULLY LOGGED IN!")
        elif is_verification(url):
            print("[!] Still on verification — code may have been wrong")
        else:
            print(f"[*] URL: {url}")

    # Keep context open 3s so session saves
    time.sleep(3)
    context.close()
    print("[OK] Session saved. Done.")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
