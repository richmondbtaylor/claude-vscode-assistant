"""
Twitter / X monitor using Playwright + saved session.

Searches X native search (Latest tab) for each keyword and yields
RawPost objects for Claude to score. Session state is saved to
.browser_sessions/twitter_session.json.

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
from config import TWITTER_KEYWORDS, TWITTER_RESULTS_PER_KEYWORD

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "twitter_session.json"
SESSION_FILE.parent.mkdir(exist_ok=True)

# X native search -- &f=live gives the Latest tab
_SEARCH_URL = "https://x.com/search?q={query}&src=typed_query&f=live"


def _make_post_id(url: str, snippet: str) -> str:
    return f"twitter_{abs(hash(url + snippet[:40]))}"


def _scrape_keyword(page, keyword: str, limit: int) -> list[dict]:
    """Search X for a keyword and return raw post dicts."""
    url = _SEARCH_URL.format(query=urllib.parse.quote(keyword))
    posts = []
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(random.uniform(3, 5))

        # Scroll a couple times to load more results
        for _ in range(3):
            page.keyboard.press("End")
            time.sleep(random.uniform(1.5, 2.5))

        # X uses article elements for each tweet
        articles = page.query_selector_all("article")

        for article in articles[:limit]:
            try:
                # Extract tweet text
                text_el = article.query_selector('div[data-testid="tweetText"]')
                text = text_el.inner_text().strip() if text_el else ""
                if not text or len(text) < 15:
                    continue

                # Extract author handle from User-Name area
                author = "unknown"
                username_el = article.query_selector('div[data-testid="User-Name"]')
                if username_el:
                    handle_links = username_el.query_selector_all('a[href^="/"]')
                    for link in handle_links:
                        href = link.get_attribute("href") or ""
                        link_text = link.inner_text().strip()
                        if link_text.startswith("@"):
                            author = link_text
                            break
                    if author == "unknown":
                        raw_name = username_el.inner_text().strip().splitlines()[0]
                        author = raw_name[:60] if raw_name else "unknown"

                # Extract tweet permalink
                tweet_url = ""
                permalink_els = article.query_selector_all('a[href*="/status/"]')
                for plink in permalink_els:
                    href = plink.get_attribute("href") or ""
                    if "/status/" in href:
                        if href.startswith("/"):
                            href = "https://x.com" + href
                        if "/analytics" not in href and "/photo/" not in href and "/video/" not in href:
                            tweet_url = href.split("?")[0]
                            break

                if not tweet_url:
                    tweet_url = url

                posts.append({"url": tweet_url, "text": text, "author": author})

            except Exception:
                continue

    except PlaywrightTimeout:
        print(f"[twitter] Timeout searching for '{keyword}'")
    except Exception as e:
        print(f"[twitter] Error searching for '{keyword}': {e}")

    return posts


def poll() -> Generator[RawPost, None, None]:
    """Main entry point -- searches X for each keyword and yields RawPosts."""
    print("[twitter] Starting Playwright poll cycle...")
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
            print("[twitter] No session found -- opening browser for manual login.")
            print("[twitter] Log in to X in the browser window. Will auto-detect when done...")
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            for _ in range(120):
                time.sleep(2)
                current = page.url.lower()
                if "/home" in current or (
                    "x.com" in current
                    and "login" not in current
                    and "flow" not in current
                ):
                    break
            else:
                print("[twitter] Timed out waiting for login. Try again.")
                browser.close()
                return
            time.sleep(3)
            context.storage_state(path=str(SESSION_FILE))
            print(f"[twitter] Session saved to {SESSION_FILE}")

        # Verify we are logged in
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        current_url = page.url.lower()
        if "login" in current_url or "flow" in current_url:
            print("[twitter] Session expired -- delete twitter_session.json and re-run to log in again.")
            browser.close()
            return

        # Search each keyword
        for keyword in TWITTER_KEYWORDS:
            print(f"[twitter] Searching: {keyword}")
            raw_posts = _scrape_keyword(page, keyword, TWITTER_RESULTS_PER_KEYWORD)

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
                    platform="twitter",
                    url=raw["url"],
                    author=raw["author"],
                    title=title,
                    body=raw["text"][:800],
                    subreddit=None,
                    published_at=None,
                )

            time.sleep(random.uniform(3, 6))

        # Refresh saved session
        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    print(f"[twitter] Poll complete -- {total} candidate posts found")
