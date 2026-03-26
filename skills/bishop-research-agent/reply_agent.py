"""
Bishop AI — Auto-Reply Agent

Reads leads from Google Sheets where Should Contact = Yes and Status is blank,
then uses Playwright to post the Suggested Reply on Reddit or n8n Community.

Usage:
    python reply_agent.py              # Process all pending leads
    python reply_agent.py --dry-run    # Preview without posting
    python reply_agent.py --limit 5    # Process at most 5 leads
"""

import argparse
import os
import random
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import gspread
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Config ─────────────────────────────────────────────────────────────────────

SHEET_ID           = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS       = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
REDDIT_USER        = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASS        = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_CLIENT_ID   = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
N8N_USER         = os.environ.get("N8N_COMMUNITY_USERNAME", "")
N8N_EMAIL        = os.environ.get("N8N_COMMUNITY_EMAIL", "")
N8N_PASS         = os.environ.get("N8N_COMMUNITY_PASSWORD", "")
LINKEDIN_USER    = os.environ.get("LINKEDIN_USERNAME", "")
LINKEDIN_PASS    = os.environ.get("LINKEDIN_PASSWORD", "")

# Column indices (1-based, matching notifier.py row order)
COL_TIMESTAMP     = 1
COL_PLATFORM      = 2
COL_URL           = 4
COL_AUTHOR        = 5
COL_TITLE         = 6
COL_SCORE         = 7
COL_SUGGESTED     = 17   # Suggested Reply
COL_SHOULD_CONTACT = 18  # Should Contact
COL_STATUS        = 20   # Status — we write "Auto-Replied" here
COL_REPLY_DATE    = 21   # Reply Sent Date
COL_COMMENT_SENT  = 22   # Comment Posted (Yes/No)
COL_DM_SENT       = 23   # DM Sent (Yes/No)

MIN_SCORE_TO_COMMENT = 70  # Only post public comments on leads scoring 70+

def random_delay(min_s: float = 45, max_s: float = 150) -> None:
    """Sleep for a randomized duration to avoid bot detection."""
    delay = random.uniform(min_s, max_s)
    print(f"  [delay] Waiting {delay:.0f}s before next action...")
    time.sleep(delay)


SESSION_DIR = os.path.join(os.path.dirname(__file__), ".browser_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

REDDIT_SESSION   = os.path.join(SESSION_DIR, "reddit_session.json")
N8N_SESSION      = os.path.join(SESSION_DIR, "n8n_session.json")
LINKEDIN_SESSION = os.path.join(SESSION_DIR, "linkedin_session.json")


# ── Google Sheets helpers ──────────────────────────────────────────────────────

def get_pending_leads() -> list[dict]:
    """Return all rows where Should Contact = Yes and Status is blank."""
    gc = gspread.oauth(credentials_filename=GOOGLE_CREDS)
    ws = gc.open_by_key(SHEET_ID).worksheet("Leads")
    rows = ws.get_all_values()

    if len(rows) <= 1:
        return []

    headers = rows[0]
    pending = []
    seen_urls: set[str] = set()  # Deduplicate by URL within this batch
    for i, row in enumerate(rows[1:], start=2):  # start=2 = sheet row number
        # Pad short rows
        while len(row) < COL_STATUS:
            row.append("")

        should_contact = row[COL_SHOULD_CONTACT - 1].strip().lower()
        status         = row[COL_STATUS - 1].strip().lower()
        platform       = row[COL_PLATFORM - 1].strip().lower()
        url            = row[COL_URL - 1].strip()
        reply          = row[COL_SUGGESTED - 1].strip()

        if should_contact == "yes" and status == "" and url and reply and url not in seen_urls:
            seen_urls.add(url)
            pending.append({
                "row":      i,
                "platform": platform,
                "url":      url,
                "author":   row[COL_AUTHOR - 1].strip(),
                "title":    row[COL_TITLE - 1].strip(),
                "score":    row[COL_SCORE - 1].strip(),
                "reply":    reply,
            })

    return pending


def mark_replied(row_num: int, status: str = "Auto-Replied",
                 comment_sent: bool = False, dm_sent: bool = False) -> None:
    """Update Status, Reply Sent Date, Comment Posted, and DM Sent for a given sheet row."""
    from datetime import datetime, timezone
    gc = gspread.oauth(credentials_filename=GOOGLE_CREDS)
    ws = gc.open_by_key(SHEET_ID).worksheet("Leads")
    sent_at = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M UTC")
    ws.update_cell(row_num, COL_STATUS, status)
    ws.update_cell(row_num, COL_REPLY_DATE, sent_at)
    ws.update_cell(row_num, COL_COMMENT_SENT, "Yes" if comment_sent else "No")
    ws.update_cell(row_num, COL_DM_SENT, "Yes" if dm_sent else "No")
    print(f"  [sheets] Row {row_num} marked: {status} | comment={comment_sent} | dm={dm_sent}")


# ── Reddit (Playwright — browser-based, no API key needed) ────────────────────

REDDIT_SESSION = os.path.join(SESSION_DIR, "reddit_session.json")


REDDIT_VERIFICATION_CODE_FILE = os.path.join(os.path.dirname(__file__), "reddit_verification_code.txt")


def _reddit_is_logged_in(page) -> bool:
    """Return True if the current page shows a logged-in Reddit session."""
    page_text = page.content().lower()
    return (
        "already logged in" in page_text
        or page.locator('[aria-label="Open user menu"]').is_visible(timeout=2000)
        or page.locator('button[id*="USER_DROPDOWN"]').is_visible(timeout=1000)
    )


def reddit_login(page) -> bool:
    """Log in to Reddit via browser. Auto-fills credentials if set in .env."""
    print("[reddit] Checking login status...")
    page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
    time.sleep(3)

    if _reddit_is_logged_in(page):
        print("[reddit] Already logged in via saved session")
        return True

    # Auto-login if credentials are available
    placeholder = "YOUR_REDDIT_USERNAME_HERE"
    if REDDIT_USER and REDDIT_USER != placeholder and REDDIT_PASS:
        print(f"[reddit] Auto-logging in as u/{REDDIT_USER}...")
        page.goto("https://www.reddit.com/login", wait_until="domcontentloaded")
        time.sleep(3)

        # Clear any old verification code file
        if os.path.exists(REDDIT_VERIFICATION_CODE_FILE):
            os.remove(REDDIT_VERIFICATION_CODE_FILE)

        try:
            # faceplate-text-input wraps the real <input> — target the child input directly
            username_sel = '#login-username input'
            password_sel = '#login-password input'
            page.wait_for_selector(username_sel, timeout=15000)
            # Click + type fires real keyboard events so faceplate components update their state
            page.locator(username_sel).click()
            page.keyboard.type(REDDIT_USER, delay=50)
            time.sleep(0.5)
            page.locator(password_sel).click()
            page.keyboard.type(REDDIT_PASS, delay=50)
            time.sleep(0.5)
            # Tab to submit button and press Enter
            page.keyboard.press('Tab')
            time.sleep(0.3)
            page.keyboard.press('Enter')
            time.sleep(5)
            print(f"[reddit] URL after submit: {page.url}")
        except Exception as e:
            print(f"[reddit] Auto-login form fill failed: {e}")

        # Handle 2FA / email verification checkpoint
        current_url = page.url
        if "verification" in current_url or "challenge" in current_url or "otp" in current_url:
            print("[reddit] Verification required.")
            print(f"[reddit] Write the code to: {REDDIT_VERIFICATION_CODE_FILE}")
            for _ in range(60):  # wait up to 3 minutes
                time.sleep(3)
                if os.path.exists(REDDIT_VERIFICATION_CODE_FILE):
                    with open(REDDIT_VERIFICATION_CODE_FILE) as f:
                        code = f.read().strip()
                    if code:
                        print(f"[reddit] Got verification code: {code}")
                        try:
                            page.fill('input[name="otp"], input[type="text"]', code)
                        except Exception:
                            pass
                        page.click('button[type="submit"]')
                        time.sleep(5)
                        break

        print(f"[reddit] URL after login attempt: {page.url}")
        page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
        time.sleep(3)
        print(f"[reddit] URL after goto home: {page.url}")
        if _reddit_is_logged_in(page):
            print("[reddit] Auto-login successful")
            return True
        print("[reddit] Auto-login failed — falling back to manual login")

    # Manual fallback
    print("[reddit] Please log in in the browser window. Waiting up to 120 seconds...")
    page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
    for _ in range(24):
        time.sleep(5)
        try:
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
            time.sleep(2)
            if _reddit_is_logged_in(page):
                print("[reddit] Login confirmed")
                return True
            print("[reddit]   Still waiting...")
            page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
        except Exception as e:
            if "closed" in str(e).lower() or "target" in str(e).lower():
                print("[reddit] Browser closed — aborting")
                return False
            raise

    print("[reddit] Login timed out")
    return False


def reddit_reply(page, url: str, reply_text: str, dry_run: bool = False) -> bool:
    """Post a comment on a Reddit thread via browser."""
    if dry_run:
        print(f"  [DRY RUN] Would comment on {url}:\n  {reply_text[:120]}...")
        return True

    print(f"  [reddit] Opening: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(5)

    try:
        # Confirm still logged in — comment box only appears when authenticated
        if not page.locator('[aria-label="Open user menu"]').is_visible(timeout=4000):
            print(f"  [reddit] Not logged in — comment box will not appear. Skipping.")
            return False

        # Scroll down ~40% to trigger lazy-loading of the comment section
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.4)")
        time.sleep(3)

        # Click the "Join the conversation" wrapper to activate the Lexical editor
        join_area = page.locator('text="Join the conversation"').first
        if join_area.is_visible(timeout=4000):
            join_area.click()
            time.sleep(2)

        # Now target the active Lexical editor
        comment_area = page.locator('div[data-lexical-editor="true"]').first
        comment_area.scroll_into_view_if_needed(timeout=5000)
        time.sleep(1)
        comment_area.click(timeout=10000)
        time.sleep(1)
        comment_area.type(reply_text, delay=15)
        time.sleep(1)

        # Submit
        submit = page.locator('button:has-text("Comment")').last
        if not submit.is_visible(timeout=3000):
            submit = page.locator('button[type="submit"]').last
        submit.click()
        time.sleep(4)

        print(f"  [reddit] Comment posted on {url}")
        return True

    except Exception as e:
        print(f"  [reddit] Comment failed: {e}")
        print(f"  [reddit] Copying reply to clipboard for manual post")
        try:
            page.evaluate(f"navigator.clipboard.writeText({repr(reply_text)})")
        except Exception:
            pass
        print(f"  Reply: {reply_text[:300]}")
        return False


def reddit_dm(page, author: str, reply_text: str, dry_run: bool = False) -> bool:
    """Send a Reddit DM via browser compose."""
    if not author or author.lower() in ("[deleted]", "automoderator", ""):
        print(f"  [reddit] Skipping DM — invalid author: {author}")
        return False

    if dry_run:
        print(f"  [DRY RUN] Would DM u/{author}:\n  {reply_text[:120]}...")
        return True

    print(f"  [reddit] Sending DM to u/{author}...")

    try:
        # Reddit message compose — confirmed working via DOM inspection
        compose_url = f"https://www.reddit.com/message/compose/?to={author}&subject=Quick+question+about+your+post"
        page.goto(compose_url, wait_until="domcontentloaded")
        time.sleep(3)

        # The message textarea is the SECOND textarea on this page (nth(1), 0-indexed)
        # textarea[0] is hidden; textarea[1] is the visible message body
        msg_box = page.locator('textarea').nth(1)
        if not msg_box.is_visible(timeout=4000):
            # Fallback: any visible textarea
            msg_box = page.locator('textarea:visible').first

        msg_box.click()
        msg_box.fill(reply_text)
        time.sleep(1)

        # Submit button
        submit = page.locator('button[type="submit"]:has-text("Send"), input[type="submit"][value="send"]').first
        if not submit.is_visible(timeout=3000):
            submit = page.locator('button:has-text("Send")').first
        submit.click()
        time.sleep(3)

        print(f"  [reddit] DM sent to u/{author}")
        return True

    except Exception as e:
        print(f"  [reddit] DM failed for u/{author}: {e}")
        return False


# ── n8n Community (Discourse) ──────────────────────────────────────────────────

def n8n_login(page) -> bool:
    """Log in to n8n Community (Discourse). Returns True on success."""
    print("[n8n] Logging in...")
    page.goto("https://community.n8n.io/login", wait_until="domcontentloaded")
    time.sleep(2)

    try:
        # Try username, then email
        for credential in [N8N_USER, N8N_EMAIL]:
            if not credential:
                continue
            page.fill('#login-account-name', credential)
            page.fill('#login-account-password', N8N_PASS)
            page.click('#login-button')
            time.sleep(4)

            error = page.locator('.alert-error').first
            if error.is_visible(timeout=2000):
                print(f"[n8n] Credential '{credential}' failed, trying next...")
                page.goto("https://community.n8n.io/login", wait_until="domcontentloaded")
                time.sleep(2)
                continue

            if "login" not in page.url:
                print(f"[n8n] Logged in successfully as {credential}")
                return True

        print("[n8n] All credentials failed")
        return False

    except Exception as e:
        print(f"[n8n] Login failed: {e}")
        return False


def n8n_reply(page, url: str, reply_text: str, dry_run: bool = False) -> bool:
    """Navigate to an n8n Community topic and post a reply."""
    print(f"  [n8n] Opening: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(3)

    if dry_run:
        print(f"  [DRY RUN] Would post to {url}:\n  {reply_text[:120]}...")
        return True

    try:
        # Click the Reply button at the bottom of the topic
        reply_btn = page.locator('button.create').first
        reply_btn.click()
        time.sleep(2)

        # Type in the Discourse reply box
        editor = page.locator('.d-editor-input').first
        editor.click()
        editor.fill(reply_text)
        time.sleep(1)

        # Submit
        submit = page.locator('button.btn-primary:has-text("Reply")').first
        submit.click()
        time.sleep(4)

        print(f"  [n8n] Reply posted to {url}")
        return True

    except Exception as e:
        print(f"  [n8n] Failed to post reply: {e}")
        return False


def n8n_dm(page, author: str, reply_text: str, dry_run: bool = False) -> bool:
    """Send a Discourse private message on n8n Community."""
    if not author:
        return False

    dm_url = f"https://community.n8n.io/new-message?username={author}"
    print(f"  [n8n] Sending DM to @{author}...")

    if dry_run:
        print(f"  [DRY RUN] Would DM @{author}:\n  {reply_text[:120]}...")
        return True

    try:
        page.goto(dm_url, wait_until="domcontentloaded")
        time.sleep(3)

        # Discourse new-message composer
        title_box = page.locator('#reply-title')
        if title_box.is_visible(timeout=3000):
            title_box.fill("Quick question about your post")
            time.sleep(0.5)

        editor = page.locator('.d-editor-input').first
        editor.click()
        editor.fill(reply_text)
        time.sleep(1)

        submit = page.locator('button.btn-primary:has-text("Message")').first
        if not submit.is_visible(timeout=2000):
            submit = page.locator('button.create').first
        submit.click()
        time.sleep(4)

        print(f"  [n8n] DM sent to @{author}")
        return True
    except Exception as e:
        print(f"  [n8n] DM failed for @{author}: {e}")
        return False


# ── LinkedIn ───────────────────────────────────────────────────────────────────

def linkedin_login(page) -> bool:
    """Log in to LinkedIn. Returns True on success."""
    print("[linkedin] Logging in...")
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    time.sleep(2)

    try:
        page.fill('#username', LINKEDIN_USER)
        page.fill('#password', LINKEDIN_PASS)
        page.click('button[type="submit"]')
        time.sleep(5)

        if "feed" in page.url or "mynetwork" in page.url or "linkedin.com/in/" in page.url:
            print("[linkedin] Logged in successfully")
            return True

        # May hit a security checkpoint — poll until resolved
        print(f"[linkedin] Login redirect to: {page.url}")
        print("[linkedin] If LinkedIn shows a security check, complete it in the browser. Waiting up to 120 seconds...")
        for _ in range(24):
            time.sleep(5)
            if "feed" in page.url or page.locator('.global-nav__me').is_visible(timeout=2000):
                print("[linkedin] Login confirmed")
                return True
            print("[linkedin]   Still waiting...")
        return True
    except Exception as e:
        print(f"[linkedin] Login error: {e}")
        return False


def linkedin_reply(page, url: str, reply_text: str, dry_run: bool = False) -> bool:
    """Navigate to a LinkedIn post and post a comment."""
    print(f"  [linkedin] Opening: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(3)

    if dry_run:
        print(f"  [DRY RUN] Would post to {url}:\n  {reply_text[:120]}...")
        return True

    try:
        # Click the comment box
        comment_btn = page.locator('button:has-text("Comment")').first
        if comment_btn.is_visible(timeout=5000):
            comment_btn.click()
            time.sleep(1)

        # Find the comment editor
        editor = page.locator('.ql-editor[contenteditable="true"]').first
        if not editor.is_visible(timeout=5000):
            editor = page.locator('[data-placeholder="Add a comment…"]').first

        editor.click()
        time.sleep(0.5)
        editor.type(reply_text, delay=20)  # Type with slight delay to avoid bot detection
        time.sleep(1)

        # Submit with Ctrl+Enter or the Post button
        submit = page.locator('button.comments-comment-box__submit-button').first
        if submit.is_visible(timeout=3000):
            submit.click()
        else:
            editor.press("Control+Enter")

        time.sleep(3)
        print(f"  [linkedin] Reply posted to {url}")
        return True

    except Exception as e:
        print(f"  [linkedin] Failed to post reply: {e}")
        print(f"  [linkedin] Opening post manually — please post the reply yourself:")
        print(f"  {reply_text}")
        return False


def linkedin_dm(page, url: str, author: str, reply_text: str, dry_run: bool = False) -> bool:
    """
    Send a LinkedIn DM by navigating to the post author's profile and clicking Message.
    url is the post URL — we extract the author profile from it or fall back to searching.
    """
    if dry_run:
        print(f"  [DRY RUN] Would DM LinkedIn author of {url}:\n  {reply_text[:120]}...")
        return True

    try:
        # Navigate to post to find author profile link
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)

        # Try to find the author's profile link from the post
        profile_link = page.locator('a.app-aware-link span.feed-shared-actor__name').first
        if not profile_link.is_visible(timeout=3000):
            profile_link = page.locator('a[href*="/in/"]').first

        if profile_link.is_visible(timeout=2000):
            profile_link.click()
            time.sleep(3)
        else:
            print(f"  [linkedin] Could not find author profile from post — skipping DM for {author}")
            return False

        # Click the Message button on their profile
        msg_btn = page.locator('button:has-text("Message")').first
        if not msg_btn.is_visible(timeout=5000):
            print(f"  [linkedin] No Message button visible for {author}")
            return False

        msg_btn.click()
        time.sleep(2)

        # Type the message
        msg_box = page.locator('.msg-form__contenteditable').first
        if not msg_box.is_visible(timeout=4000):
            msg_box = page.locator('[contenteditable="true"]').last
        msg_box.click()
        msg_box.type(reply_text, delay=25)
        time.sleep(1)

        # Send
        send_btn = page.locator('button.msg-form__send-button').first
        if send_btn.is_visible(timeout=3000):
            send_btn.click()
        else:
            msg_box.press("Control+Enter")

        time.sleep(3)
        print(f"  [linkedin] DM sent to {author}")
        return True

    except Exception as e:
        print(f"  [linkedin] DM failed for {author}: {e}")
        return False


# ── Facebook ────────────────────────────────────────────────────────────────────

def facebook_reply_manual(page, url: str, reply_text: str, dry_run: bool = False) -> bool:
    """
    Open a Facebook post and prompt the user to post manually.
    Facebook aggressively blocks automation, so we assist rather than automate.
    """
    if dry_run:
        print(f"  [DRY RUN] Would open Facebook: {url}")
        print(f"  Reply: {reply_text[:120]}...")
        return True

    print(f"  [facebook] Opening: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(3)

    # Copy the reply text to clipboard via JavaScript
    try:
        page.evaluate(f"navigator.clipboard.writeText({repr(reply_text)})")
        print("  [facebook] Reply text copied to clipboard!")
    except Exception:
        pass

    print(f"\n  ┌─ REPLY TEXT (also copied to clipboard) ──────────────────")
    print(f"  │ {reply_text[:300]}")
    print(f"  └───────────────────────────────────────────────────────────\n")
    print("  [facebook] Post the reply shown above, then re-run with --limit to pick up remaining leads.")
    time.sleep(5)
    return True


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Bishop AI Auto-Reply Agent")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview replies without posting")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max leads to process (0 = all)")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==========================================")
    print("     Bishop AI Auto-Reply Agent")
    print("==========================================")
    if args.dry_run:
        print("  *** DRY RUN MODE — nothing will be posted ***")

    # Fetch pending leads from the sheet
    print("\n[sheets] Fetching pending leads...")
    leads = get_pending_leads()

    if not leads:
        print("[sheets] No pending leads found (Should Contact = Yes, Status = blank).")
        return

    if args.limit:
        leads = leads[:args.limit]

    # Split by platform
    reddit_leads   = [l for l in leads if "reddit" in l["platform"]]
    n8n_leads      = [l for l in leads if "n8n" in l["platform"]]
    linkedin_leads = [l for l in leads if "linkedin" in l["platform"]]
    facebook_leads = [l for l in leads if "facebook" in l["platform"]]
    other_leads    = [l for l in leads if not any(p in l["platform"]
                      for p in ("reddit", "n8n", "linkedin", "facebook"))]

    print(f"[agent] Found {len(leads)} pending leads: "
          f"{len(reddit_leads)} Reddit, {len(n8n_leads)} n8n, "
          f"{len(linkedin_leads)} LinkedIn, {len(facebook_leads)} Facebook, "
          f"{len(other_leads)} other")

    with sync_playwright() as pw:
        # Use real Chrome (channel='chrome') so Reddit can't fingerprint Playwright's bundled Chromium
        try:
            browser = pw.chromium.launch(channel='chrome', headless=False, slow_mo=50)
        except Exception:
            browser = pw.chromium.launch(headless=False, slow_mo=50)

        # ── Reddit (Playwright — browser-based) ─────────────────────────────
        if reddit_leads:
            session_file = REDDIT_SESSION if os.path.exists(REDDIT_SESSION) else None
            ctx = browser.new_context(storage_state=session_file) if session_file else browser.new_context()
            page = ctx.new_page()
            # Hide automation signals so Reddit doesn't block the login
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logged_in = reddit_login(page)
            if logged_in:
                ctx.storage_state(path=REDDIT_SESSION)

                success_count = 0
                for lead in reddit_leads:
                    score = int(lead["score"]) if str(lead["score"]).isdigit() else 0
                    print(f"\n→ [{score}] {lead['title'][:60]}...")
                    if score < MIN_SCORE_TO_COMMENT:
                        print(f"  [reddit] Score {score} < {MIN_SCORE_TO_COMMENT} — skipping comment, DM only")
                        comment_ok = False
                    else:
                        comment_ok = reddit_reply(page, lead["url"], lead["reply"], dry_run=args.dry_run)
                        random_delay(45, 120)
                    dm_ok = reddit_dm(page, lead["author"], lead["reply"], dry_run=args.dry_run)
                    random_delay(60, 150)
                    if not args.dry_run:
                        mark_replied(lead["row"], comment_sent=comment_ok, dm_sent=dm_ok)
                        if comment_ok:
                            success_count += 1
                print(f"\n[reddit] Done — {success_count}/{len(reddit_leads)} comments posted")
            else:
                print("[reddit] Skipping Reddit leads — login failed")

            page.close()
            ctx.close()

        # ── n8n Community ────────────────────────────────────────────────────
        if n8n_leads:
            session_file = N8N_SESSION if os.path.exists(N8N_SESSION) else None
            ctx = browser.new_context(storage_state=session_file) if session_file else browser.new_context()
            page = ctx.new_page()

            # Check if already logged in
            page.goto("https://community.n8n.io", wait_until="domcontentloaded")
            time.sleep(2)
            logged_in = page.locator('.current-user').is_visible(timeout=3000)

            if not logged_in:
                logged_in = n8n_login(page)

            if logged_in:
                ctx.storage_state(path=N8N_SESSION)

                success_count = 0
                for lead in n8n_leads:
                    score = int(lead["score"]) if str(lead["score"]).isdigit() else 0
                    print(f"\n→ [{score}] {lead['title'][:60]}...")
                    if score < MIN_SCORE_TO_COMMENT:
                        print(f"  [n8n] Score {score} < {MIN_SCORE_TO_COMMENT} — skipping comment, DM only")
                        comment_ok = False
                    else:
                        comment_ok = n8n_reply(page, lead["url"], lead["reply"], dry_run=args.dry_run)
                        random_delay(45, 120)
                    dm_ok = n8n_dm(page, lead["author"], lead["reply"], dry_run=args.dry_run)
                    random_delay(60, 150)
                    if not args.dry_run:
                        mark_replied(lead["row"], comment_sent=comment_ok, dm_sent=dm_ok)
                        if comment_ok:
                            success_count += 1

                print(f"\n[n8n] Done — {success_count}/{len(n8n_leads)} comments posted")
            else:
                print("[n8n] Skipping n8n leads — login failed")

            page.close()
            ctx.close()

        # ── LinkedIn ─────────────────────────────────────────────────────────
        if linkedin_leads:
            session_file = LINKEDIN_SESSION if os.path.exists(LINKEDIN_SESSION) else None
            ctx = browser.new_context(storage_state=session_file) if session_file else browser.new_context()
            page = ctx.new_page()

            # Check if already logged in
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            time.sleep(2)
            logged_in = "feed" in page.url or page.locator('.global-nav__me').is_visible(timeout=3000)

            if not logged_in:
                logged_in = linkedin_login(page)

            if logged_in:
                ctx.storage_state(path=LINKEDIN_SESSION)
                success_count = 0
                for lead in linkedin_leads:
                    score = int(lead["score"]) if str(lead["score"]).isdigit() else 0
                    print(f"\n→ [{score}] {lead['title'][:60]}...")
                    if score < MIN_SCORE_TO_COMMENT:
                        print(f"  [linkedin] Score {score} < {MIN_SCORE_TO_COMMENT} — skipping comment, DM only")
                        comment_ok = False
                        dm_ok = linkedin_dm(page, lead["url"], lead["author"], lead["reply"], dry_run=args.dry_run)
                        random_delay(90, 180)
                    else:
                        comment_ok = linkedin_reply(page, lead["url"], lead["reply"], dry_run=args.dry_run)
                        random_delay(60, 180)
                        dm_ok = linkedin_dm(page, lead["url"], lead["author"], lead["reply"], dry_run=args.dry_run)
                        random_delay(90, 180)
                    if not args.dry_run:
                        mark_replied(lead["row"], comment_sent=comment_ok, dm_sent=dm_ok)
                        if comment_ok:
                            success_count += 1

                print(f"\n[linkedin] Done — {success_count}/{len(linkedin_leads)} replies posted")
            else:
                print("[linkedin] Skipping LinkedIn leads — login failed")

            page.close()
            ctx.close()

        # ── Facebook ──────────────────────────────────────────────────────────
        if facebook_leads:
            print(f"\n[facebook] {len(facebook_leads)} Facebook leads — opening each post for assisted reply")
            print("  (Facebook blocks full automation — reply text will be copied to clipboard)\n")
            ctx = browser.new_context()
            page = ctx.new_page()

            success_count = 0
            for lead in facebook_leads:
                print(f"\n→ [{lead['score']}] {lead['title'][:60]}...")
                ok = facebook_reply_manual(page, lead["url"], lead["reply"], dry_run=args.dry_run)
                if ok and not args.dry_run:
                    mark_replied(lead["row"], status="Manually Replied", comment_sent=True)
                    success_count += 1

            print(f"\n[facebook] Done — {success_count}/{len(facebook_leads)} leads handled")
            page.close()
            ctx.close()

        # ── Other platforms ───────────────────────────────────────────────────
        if other_leads:
            print(f"\n[agent] {len(other_leads)} leads on other platforms (Twitter/Quora/etc)")
            print("        These require manual replies:")
            for lead in other_leads:
                print(f"\n→ [{lead['score']}] {lead['platform'].capitalize()} — {lead['title'][:60]}")
                print(f"  URL: {lead['url']}")
                print(f"  Reply: {lead['reply'][:200]}")

        browser.close()

    print("\n[agent] All done.")


if __name__ == "__main__":
    main()
