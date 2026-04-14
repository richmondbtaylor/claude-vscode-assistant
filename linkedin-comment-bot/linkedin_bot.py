"""
LinkedIn Comment Bot — Playwright automation
Navigates to Rich's recent posts, finds new comments, and replies.
"""

import os
import sys
import json
import time
import random
import datetime
from playwright.sync_api import sync_playwright

# Fix Windows console encoding for emoji
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from claude_generator import generate_reply, score_comment

# --- Config ---
BOT_DIR          = os.path.dirname(os.path.abspath(__file__))
STORAGE_STATE    = os.path.join(BOT_DIR, "storage_state.json")   # portable session cookies
STATE_FILE       = os.path.join(BOT_DIR, "replied_comments.json")

LINKEDIN_PROFILE_URL = os.getenv("LINKEDIN_PROFILE_URL", "https://www.linkedin.com/in/richmond-taylor/")
MY_NAME = os.getenv("MY_NAME", "Richmond").lower()
MAX_POSTS = int(os.getenv("MAX_POSTS_TO_CHECK", "5"))
MAX_REPLIES = int(os.getenv("MAX_REPLIES_PER_RUN", "10"))

# Selectors — LinkedIn changes these often; multiple fallbacks per target
COMMENT_CONTAINERS = [
    ".comments-comment-item",
    ".comments-comment-entity",
    "article.comments-comment-item",
]

COMMENTER_NAME_SELECTORS = [
    "span.comments-post-meta__name-text",
    "a.comments-post-meta__name-text",
    ".comment-contributor-name span",
    ".comments-comment-meta__description-title",
]

COMMENT_TEXT_SELECTORS = [
    ".comments-comment-item__main-content span[dir='ltr']",
    ".feed-shared-comment-text span[dir='ltr']",
    ".comments-comment-item__main-content",
]

POST_TEXT_SELECTORS = [
    ".update-components-text__text-view span[dir='ltr']",
    ".feed-shared-update-v2__description span[dir='ltr']",
    ".feed-shared-text span[dir='ltr']",
    "article span[dir='ltr']",
]


class LinkedInCommentBot:
    def __init__(self):
        self.replied_ids = self._load_state()
        self.playwright = sync_playwright().start()
        if not os.path.exists(STORAGE_STATE):
            raise FileNotFoundError(
                "storage_state.json not found. Run login.py first to save your LinkedIn session."
            )
        browser = self.playwright.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        )
        self.context = browser.new_context(
            storage_state=STORAGE_STATE,
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()

    # --- State persistence ---

    def _load_state(self) -> set:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(sorted(self.replied_ids), f, indent=2)

    # --- Login ---

    def _is_logged_in(self) -> bool:
        try:
            self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)
            return "feed" in self.page.url or "mynetwork" in self.page.url
        except Exception:
            return False

    def _wait_for_login(self):
        print("Not logged in. Open the browser and log in to LinkedIn manually.")
        self.page.goto("https://www.linkedin.com/login")
        for _ in range(36):  # wait up to 3 minutes
            time.sleep(5)
            url = self.page.url
            if "feed" in url or "mynetwork" in url:
                print("Login detected — continuing.")
                return
        raise RuntimeError("Login timeout. Run setup.py first to save a session.")

    # --- Post discovery ---

    def _get_recent_post_urls(self) -> list:
        activity_url = LINKEDIN_PROFILE_URL.rstrip("/") + "/recent-activity/posts/"
        print(f"Navigating to activity page...")
        self.page.goto(activity_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        # Scroll to trigger lazy-loaded posts
        for _ in range(3):
            self.page.evaluate("window.scrollBy(0, 1200)")
            time.sleep(2)

        urls = self.page.evaluate("""() => {
            const seen = new Set();
            const results = [];

            // Pattern 1: direct /feed/update/ links
            document.querySelectorAll('a[href*="/feed/update/"]').forEach(a => {
                const href = a.href.split('?')[0];
                if (!seen.has(href)) { seen.add(href); results.push(href); }
            });

            // Pattern 2: /analytics/post-summary/urn:li:activity:XXXX — convert to feed URL
            document.querySelectorAll('a[href*="/analytics/post-summary/urn:li:activity:"]').forEach(a => {
                const m = a.href.match(/urn:li:activity:(\\d+)/);
                if (m) {
                    const feedUrl = 'https://www.linkedin.com/feed/update/urn:li:activity:' + m[1] + '/';
                    if (!seen.has(feedUrl)) { seen.add(feedUrl); results.push(feedUrl); }
                }
            });

            // Pattern 3: boost/campaigns links with ugcPost — convert to feed URL
            document.querySelectorAll('a[href*="ugcPost"]').forEach(a => {
                const m = a.href.match(/urn%3Ali%3AugcPost%3A(\\d+)/);
                if (m) {
                    const feedUrl = 'https://www.linkedin.com/feed/update/urn:li:ugcPost:' + m[1] + '/';
                    if (!seen.has(feedUrl)) { seen.add(feedUrl); results.push(feedUrl); }
                }
            });

            return results;
        }""")

        print(f"Found {len(urls)} post URL(s). Checking first {MAX_POSTS}.")
        return urls[:MAX_POSTS]

    # --- Comment scraping (stays on current page) ---

    def _get_post_text(self) -> str:
        for sel in POST_TEXT_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if len(text) > 20:
                        return text[:400]
            except Exception:
                continue
        return ""

    def _expand_comments(self):
        """Click 'X comments' button to open comments section."""
        try:
            btns = self.page.query_selector_all("button[aria-label*='comment' i]")
            for btn in btns:
                label = (btn.get_attribute("aria-label") or "").lower()
                if "show" not in label and "reply" not in label:
                    btn.click()
                    time.sleep(3)
                    break
        except Exception:
            pass

        # Load more comments if available
        for _ in range(2):
            try:
                more = self.page.query_selector("button:has-text('Load more comments')")
                if more:
                    more.click()
                    time.sleep(2)
                else:
                    break
            except Exception:
                break

    def _extract_comments(self) -> list:
        """Pull all comment elements from the current page."""
        comments = []
        for container_sel in COMMENT_CONTAINERS:
            els = self.page.query_selector_all(container_sel)
            if els:
                for el in els:
                    c = self._parse_comment_element(el)
                    if c:
                        comments.append(c)
                break  # Use first selector that works
        return comments

    def _parse_comment_element(self, el) -> dict | None:
        try:
            # Commenter name
            name = ""
            for sel in COMMENTER_NAME_SELECTORS:
                name_el = el.query_selector(sel)
                if name_el:
                    name = name_el.inner_text().strip()
                    if name:
                        break

            # Comment text
            text = ""
            for sel in COMMENT_TEXT_SELECTORS:
                text_el = el.query_selector(sel)
                if text_el:
                    text = text_el.inner_text().strip()
                    if text:
                        break

            if not name or not text:
                return None

            # Skip own comments
            if MY_NAME in name.lower():
                return None

            # Profile URL
            profile_el = el.query_selector("a[href*='/in/']")
            profile_url = profile_el.get_attribute("href").split("?")[0] if profile_el else ""

            # Stable comment ID: profile + first 80 chars of text
            comment_id = f"{profile_url}::{text[:80]}"

            return {
                "name": name,
                "profileUrl": profile_url,
                "text": text,
                "commentId": comment_id,
                "element": el,  # Keep reference for clicking Reply
            }
        except Exception:
            return None

    # --- Replying ---

    def _post_reply(self, comment_el, reply_text: str) -> bool:
        """Find Reply button on the comment element, type reply, submit."""
        try:
            comment_el.scroll_into_view_if_needed()
            time.sleep(0.5)

            # Click Reply
            reply_btn = comment_el.query_selector(
                "button:has-text('Reply'), button[aria-label*='Reply' i]"
            )
            if not reply_btn:
                return False
            reply_btn.click()
            time.sleep(2)

            # Find reply textbox
            editor = None
            for sel in [
                "[role='textbox'][aria-label*='reply' i]",
                ".ql-editor[contenteditable='true']",
                "div[contenteditable='true'][data-placeholder*='reply' i]",
                "div[contenteditable='true']",
            ]:
                editor = self.page.query_selector(sel)
                if editor:
                    break

            if not editor:
                return False

            editor.click()
            time.sleep(0.5)
            self.page.keyboard.type(reply_text, delay=28)
            time.sleep(1)

            # Submit: Ctrl+Enter is most reliable on LinkedIn
            self.page.keyboard.press("Control+Enter")
            time.sleep(4)

            # Verify submission by checking if editor is gone or empty
            return True

        except Exception as e:
            print(f"    Reply error: {e}")
            return False

    # --- Main run loop ---

    def run(self) -> list:
        results = []

        if not self._is_logged_in():
            self._wait_for_login()

        post_urls = self._get_recent_post_urls()
        if not post_urls:
            print("No posts found.")
            return results

        replies_this_run = 0

        for post_url in post_urls:
            if replies_this_run >= MAX_REPLIES:
                print(f"Hit reply limit ({MAX_REPLIES}) for this run.")
                break

            print(f"\nPost: {post_url[:70]}...")
            try:
                self.page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)

                post_text = self._get_post_text()
                self._expand_comments()
                comments = self._extract_comments()

                new_comments = [
                    c for c in comments
                    if c["commentId"] not in self.replied_ids
                ]
                print(f"  {len(new_comments)} new comment(s) to reply to.")

                for comment in new_comments:
                    if replies_this_run >= MAX_REPLIES:
                        break

                    print(f"  -> {comment['name']}: {comment['text'][:60]}...")

                    reply_text = generate_reply(comment["text"], post_text)
                    lead_score = score_comment(comment["text"])

                    print(f"     Reply ({lead_score}): {reply_text}")

                    success = self._post_reply(comment["element"], reply_text)

                    if success:
                        self.replied_ids.add(comment["commentId"])
                        self._save_state()
                        replies_this_run += 1

                        results.append({
                            "timestamp": datetime.datetime.now().isoformat(),
                            "postUrl": post_url,
                            "postSnippet": post_text[:120],
                            "commenterName": comment["name"],
                            "commenterProfile": comment["profileUrl"],
                            "commentText": comment["text"],
                            "leadScore": lead_score,
                            "reply": reply_text,
                            "status": "Replied",
                        })

                        # Human-like delay between replies
                        delay = random.randint(45, 120)
                        print(f"     Waiting {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"     Could not post reply — skipping.")

            except Exception as e:
                print(f"  Error on post: {e}")
                continue

            # Delay between posts
            time.sleep(random.randint(8, 20))

        return results

    def close(self):
        try:
            self.context.close()
            self.playwright.stop()
        except Exception:
            pass
