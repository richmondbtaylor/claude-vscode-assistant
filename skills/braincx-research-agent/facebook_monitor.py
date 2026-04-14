"""
Facebook monitor using Playwright + saved session.

Searches Facebook native post search (facebook.com/search/posts/?q=...) for
each keyword and yields RawPost objects for Claude to score. Mirrors the
twitter_monitor.py model.

Session is saved to .browser_sessions/facebook_session.json after first login.
On first run (no session file), a browser window opens for manual login --
complete the login, then the script auto-detects when done and continues.
"""

import time
import random
import urllib.parse
from pathlib import Path
from typing import Generator

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from analyzer import RawPost
from config import FACEBOOK_KEYWORDS, FACEBOOK_RESULTS_PER_KEYWORD

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "facebook_session.json"
SESSION_FILE.parent.mkdir(exist_ok=True)

_SEARCH_URL = "https://www.facebook.com/search/posts/?q={query}"


def _make_post_id(url: str, snippet: str) -> str:
    return f"facebook_{abs(hash(url + snippet[:40]))}"


def _scrape_keyword(page, keyword: str, limit: int) -> list[dict]:
    """Search FB posts for a keyword and return raw post dicts."""
    url = _SEARCH_URL.format(query=urllib.parse.quote(keyword))
    posts = []
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        time.sleep(random.uniform(4, 6))

        # Scroll to load more results
        for _ in range(4):
            page.keyboard.press("End")
            time.sleep(random.uniform(2, 3))

        # FB renders each post inside div[role="article"] in the search feed
        articles = page.query_selector_all('div[role="feed"] div[role="article"]')
        if not articles:
            articles = page.query_selector_all('div[role="article"]')

        seen_snippets = set()
        for article in articles:
            if len(posts) >= limit:
                break
            try:
                text = article.inner_text() or ""
                text = text.strip()
                if len(text) < 30 or len(text) > 5000:
                    continue

                # Skip ads and obvious non-post containers
                lower = text.lower()
                if lower.startswith("sponsored") or "suggested for you" in lower[:60]:
                    continue

                snippet = text[:120]
                if snippet in seen_snippets:
                    continue
                seen_snippets.add(snippet)

                # Author from first h2/h3/strong link
                author = "unknown"
                author_el = article.query_selector('h2 a, h3 a, strong a, a strong')
                if author_el:
                    raw = (author_el.inner_text() or "").strip()
                    if raw:
                        author = raw[:80]

                # Permalink: prefer /groups/.../posts/, /permalink/, story_fbid
                post_url = ""
                link_els = article.query_selector_all(
                    'a[href*="/posts/"], a[href*="/permalink/"], '
                    'a[href*="story_fbid"], a[href*="/groups/"][href*="/posts/"]'
                )
                for link in link_els:
                    href = link.get_attribute("href") or ""
                    if not href or href.startswith("#"):
                        continue
                    if href.startswith("/"):
                        href = "https://www.facebook.com" + href
                    post_url = href.split("?")[0]
                    break

                if not post_url:
                    post_url = url  # fall back to the search URL

                posts.append({"url": post_url, "text": text, "author": author})
            except Exception:
                continue

    except PlaywrightTimeout:
        print(f"[facebook] Timeout searching for '{keyword}'")
    except Exception as e:
        print(f"[facebook] Error searching for '{keyword}': {e}")

    return posts


def poll() -> Generator[RawPost, None, None]:
    """Main entry point -- searches FB posts for each keyword and yields RawPosts."""
    print("[facebook] Starting Playwright poll cycle...")
    seen_in_this_cycle: set[str] = set()
    total = 0

    with sync_playwright() as pw:
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

        # First-run login flow
        if not session_exists:
            print("[facebook] No session found -- opening browser for manual login.", flush=True)
            print("[facebook] Log in to Facebook. Script will save session and continue automatically.", flush=True)
            print("[facebook] You have 10 minutes.", flush=True)
            page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
            logged_in = False
            for i in range(300):  # ~10 minutes
                time.sleep(2)
                try:
                    current = page.url.lower()
                except Exception:
                    continue
                if i % 15 == 0:
                    print(f"[facebook] waiting... url={current[:80]}", flush=True)
                # Any facebook URL that isn't the login/checkpoint page means we're in
                if "facebook.com" in current and not any(x in current for x in [
                    "/login", "/checkpoint", "two_step", "recover", "signup", "reg"
                ]):
                    logged_in = True
                    break
            if not logged_in:
                print("[facebook] Timed out waiting for login. Try again.", flush=True)
                browser.close()
                return
            time.sleep(5)  # let the page settle
            context.storage_state(path=str(SESSION_FILE))
            print(f"[facebook] Session saved to {SESSION_FILE}", flush=True)

        # Verify we are logged in
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        if "login" in page.url.lower():
            print("[facebook] Session expired -- delete facebook_session.json and re-run to log in again.")
            browser.close()
            return

        # Search each keyword
        for keyword in FACEBOOK_KEYWORDS:
            print(f"[facebook] Searching: {keyword}")
            raw_posts = _scrape_keyword(page, keyword, FACEBOOK_RESULTS_PER_KEYWORD)

            for raw in raw_posts:
                post_id = _make_post_id(raw["url"], raw["text"])
                if post_id in seen_in_this_cycle:
                    continue
                seen_in_this_cycle.add(post_id)
                total += 1

                lines = [l.strip() for l in raw["text"].splitlines() if l.strip()]
                title = lines[0][:120] if lines else raw["text"][:120]

                yield RawPost(
                    id=post_id,
                    platform="facebook",
                    url=raw["url"],
                    author=raw["author"],
                    title=title,
                    body=raw["text"][:800],
                    subreddit=None,
                    published_at=None,
                )

            time.sleep(random.uniform(4, 7))

        # Refresh saved session
        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    print(f"[facebook] Poll complete -- {total} candidate posts found")
