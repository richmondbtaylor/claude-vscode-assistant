"""
Facebook Groups monitor using Playwright.

Scrapes public AI/automation Facebook groups for recent posts, filters by
keywords, and yields RawPost objects for Claude to score.

Session is saved to .browser_sessions/facebook_session.json after first login.
On first run (no session file), a browser window opens for manual login —
complete the login, then press Enter in the terminal to continue.
"""

import time
import random
from pathlib import Path
from typing import Generator

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from analyzer import RawPost
from config import FACEBOOK_GROUPS, FACEBOOK_POSTS_PER_GROUP, FACEBOOK_KEYWORDS

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "facebook_session.json"
SESSION_FILE.parent.mkdir(exist_ok=True)

_KEYWORD_SET = {kw.lower() for kw in FACEBOOK_KEYWORDS}


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in _KEYWORD_SET)


def _make_post_id(url: str) -> str:
    return f"facebook_{abs(hash(url))}"


def _scrape_group(page, group_url: str, limit: int) -> list[dict]:
    """Navigate to a group and extract recent posts. Returns list of raw dicts."""
    posts = []
    try:
        page.goto(group_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(random.uniform(3, 5))

        # Scroll to load more posts
        for _ in range(4):
            page.keyboard.press("End")
            time.sleep(random.uniform(1.5, 2.5))

        # Extract post containers — Facebook uses role="article" for feed posts
        articles = page.query_selector_all('div[role="article"]')

        for article in articles[:limit]:
            try:
                # Get all visible text from the post
                text = article.inner_text()
                if not text or len(text) < 20:
                    continue

                # Try to get the post permalink
                link_el = article.query_selector('a[href*="/groups/"][href*="/posts/"], a[href*="story_fbid"], a[href*="permalink"]')
                url = ""
                if link_el:
                    url = link_el.get_attribute("href") or ""
                    if url.startswith("/"):
                        url = "https://www.facebook.com" + url

                if not url:
                    url = group_url  # fallback to group URL

                # Try to get author name
                author = "unknown"
                author_el = article.query_selector('a[role="link"] strong, h2 a, h3 a')
                if author_el:
                    author = author_el.inner_text().strip()

                posts.append({"url": url, "text": text, "author": author, "group_url": group_url})

            except Exception:
                continue

    except PlaywrightTimeout:
        print(f"[facebook] Timeout loading {group_url}")
    except Exception as e:
        print(f"[facebook] Error scraping {group_url}: {e}")

    return posts


def poll() -> Generator[RawPost, None, None]:
    """Main entry point — scrapes each configured Facebook group."""
    print("[facebook] Starting Playwright poll cycle...")
    seen_in_this_cycle: set[str] = set()
    total_candidates = 0

    with sync_playwright() as pw:
        # Launch browser — headless if session exists, headed if first-time login needed
        session_exists = SESSION_FILE.exists()
        browser = pw.chromium.launch(headless=session_exists)

        ctx_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1280, "height": 900},
        }
        if session_exists:
            ctx_kwargs["storage_state"] = str(SESSION_FILE)

        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()

        # ── First-run login flow ──────────────────────────────────────────────
        if not session_exists:
            print("[facebook] No session found — opening browser for manual login.")
            print("[facebook] Log in to Facebook in the browser window. Will auto-detect when done...")
            page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
            # Poll until the URL leaves the login page (user completed login)
            for _ in range(120):  # wait up to ~4 minutes
                time.sleep(2)
                current = page.url.lower()
                if "login" not in current and "facebook.com" in current:
                    break
            else:
                print("[facebook] Timed out waiting for login. Try again.")
                browser.close()
                return
            time.sleep(3)  # Let cookies settle
            context.storage_state(path=str(SESSION_FILE))
            print(f"[facebook] Session saved to {SESSION_FILE}")

        # ── Verify we're logged in ────────────────────────────────────────────
        page.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        if "login" in page.url.lower():
            print("[facebook] Session expired — delete facebook_session.json and re-run to log in again.")
            browser.close()
            return

        # ── Scrape each group ─────────────────────────────────────────────────
        for group_url in FACEBOOK_GROUPS:
            print(f"[facebook] Scraping: {group_url}")
            raw_posts = _scrape_group(page, group_url, FACEBOOK_POSTS_PER_GROUP)

            for raw in raw_posts:
                text = raw["text"]
                url = raw["url"]
                author = raw["author"]

                if not _matches_keywords(text):
                    continue

                post_id = _make_post_id(url + text[:50])
                if post_id in seen_in_this_cycle:
                    continue
                seen_in_this_cycle.add(post_id)
                total_candidates += 1

                # Build title from first non-empty line of post text
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                title = lines[0][:120] if lines else text[:120]
                body = text[:800]

                yield RawPost(
                    id=post_id,
                    platform="facebook",
                    url=url,
                    author=author,
                    title=title,
                    body=body,
                    subreddit=None,
                    published_at=None,
                )

            time.sleep(random.uniform(3, 6))

        # Save refreshed session
        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    print(f"[facebook] Poll complete — {total_candidates} keyword-matched posts found")
