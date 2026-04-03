# Fix WhatsApp LinkedIn Pod Login: Switch to Persistent Browser Context

## Context

The WhatsApp LinkedIn Pod bot (`whatsapp-linkedin-pod`) is failing to log into LinkedIn because:
1. It launches a **fresh browser every time** (`chromium.launch()` + `new_context()`), forcing a full login flow each run
2. Multiple rapid login attempts triggered LinkedIn's rate limiting and CAPTCHA ("Let's do a quick security check")
3. Meanwhile, **clawdbot-feed works fine** because it uses `launch_persistent_context()` with a saved Chrome profile -- cookies and session survive across restarts, so it rarely needs to re-login

The fix: migrate whatsapp-linkedin-pod to use a persistent browser context (like clawdbot-feed), so LinkedIn sees a returning user instead of a brand-new browser each time.

## Plan

### 1. Add persistent Chrome profile to whatsapp-linkedin-pod

**File:** `C:\Users\richm\.claude\skills\whatsapp-linkedin-pod\linkedin_commenter.py` (lines 30-48)

Change the `start()` method from:
```python
self.browser = self.playwright.chromium.launch(headless=False, args=['--start-maximized'])
context = self.browser.new_context(viewport=..., user_agent=...)
self.page = context.new_page()
```

To:
```python
self.context = self.playwright.chromium.launch_persistent_context(
    user_data_dir=os.path.join(os.path.dirname(__file__), 'linkedin_profile'),
    headless=False,
    args=['--start-maximized'],
    viewport={'width': 1920, 'height': 1080},
)
self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
```

Key changes:
- Use `launch_persistent_context` with a `linkedin_profile/` directory (same pattern as clawdbot-feed's `chrome_profile/`)
- Drop the explicit user agent override (Playwright's default is less detectable than a truncated UA string)
- Store `self.context` instead of `self.browser` for cleanup
- Session cookies persist, so after first successful login, future runs skip the login entirely

### 2. Update `_login()` to check if already authenticated

The existing check at line 88-93 already handles this (`if 'feed' in current`), so no changes needed there. The persistent context means this check will actually work now -- the saved cookies will keep the session alive.

### 3. Update `close()` method

**File:** Same file -- update `close()` to close `self.context` instead of `self.browser`.

### 4. Handle shared Playwright instance with WhatsApp

**File:** `C:\Users\richm\.claude\skills\whatsapp-linkedin-pod\main.py`

The main orchestrator currently creates a shared Playwright instance for both LinkedIn and WhatsApp. Since `launch_persistent_context` creates a browser+context together, we need to ensure LinkedIn and WhatsApp use separate browser instances (they already use separate profiles -- WhatsApp uses `whatsapp_session/`).

Check how `main.py` passes the shared playwright instance and ensure both can coexist.

### 5. Add `--disable-blink-features=AutomationControlled` arg

Add this browser arg to reduce Playwright detection fingerprint. This removes the `navigator.webdriver` flag that LinkedIn checks.

## Files to Modify

- `C:\Users\richm\.claude\skills\whatsapp-linkedin-pod\linkedin_commenter.py` -- browser launch, login, close methods
- `C:\Users\richm\.claude\skills\whatsapp-linkedin-pod\main.py` -- verify shared Playwright handling still works

## Verification

1. Run `python -u main.py` from the skill directory
2. First run: should open browser, navigate to LinkedIn login, fill credentials, handle checkpoint (CAPTCHA/code may still appear this first time due to prior rate limiting)
3. After successful first login, kill and restart the bot
4. Second run: should skip login entirely ("Already logged in to LinkedIn!") because cookies are saved in `linkedin_profile/`
5. Confirm WhatsApp still connects properly alongside LinkedIn
