"""
LinkedIn monitor using Playwright + saved session.

Searches LinkedIn's content search (past week) for each keyword and yields
RawPost objects for Claude to score. Uses the existing LinkedIn session saved
by reply_agent.py at .browser_sessions/linkedin_session.json.

If the session doesn't exist or is expired, prints a message and skips.
"""

import time
import random
from pathlib import Path
from typing import Generator

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from analyzer import RawPost
from config import LINKEDIN_KEYWORDS, LINKEDIN_RESULTS_PER_KEYWORD

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "linkedin_session.json"

# LinkedIn content search — filters to posts only, past week
_SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords={query}&datePosted=past-week&sortBy=date"
)


def _make_post_id(url: str, snippet: str) -> str:
    return f"linkedin_{abs(hash(url + snippet[:40]))}"


def _scrape_keyword(page, keyword: str, limit: int) -> list[dict]:
    """Search LinkedIn for a keyword and return raw post dicts."""
    import urllib.parse
    url = _SEARCH_URL.format(query=urllib.parse.quote(keyword))
    posts = []
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(random.uniform(2, 4))

        # Scroll once to load more results
        page.keyboard.press("End")
        time.sleep(random.uniform(1.5, 2.5))

        # LinkedIn search results use data-urn attributes on post containers
        # Each result card has a class containing "search-result" or similar
        cards = page.query_selector_all(
            'div[data-chameleon-result-urn], '
            'li.reusable-search__result-container, '
            'div.search-results-container li'
        )

        for card in cards[:limit]:
            try:
                text = card.inner_text()
                if not text or len(text) < 30:
                    continue

                # Try to get the post URL
                link = card.query_selector('a[href*="/posts/"], a[href*="activity"], a[href*="ugcPost"]')
                post_url = ""
                if link:
                    post_url = link.get_attribute("href") or ""
                    if post_url.startswith("/"):
                        post_url = "https://www.linkedin.com" + post_url
                    # Strip tracking params
                    post_url = post_url.split("?")[0]

                if not post_url:
                    post_url = url  # fallback to search URL

                # Author name — usually in a span with actor's name
                author = "unknown"
                author_el = card.query_selector(
                    'span.entity-result__title-text a, '
                    'span[aria-hidden="true"] + span, '
                    'a[data-field="actor_name"]'
                )
                if author_el:
                    author = author_el.inner_text().strip().split("\n")[0]

                posts.append({"url": post_url, "text": text, "author": author})

            except Exception:
                continue

    except PlaywrightTimeout:
        print(f"[linkedin] Timeout searching for '{keyword}'")
    except Exception as e:
        print(f"[linkedin] Error searching for '{keyword}': {e}")

    return posts


def poll() -> Generator[RawPost, None, None]:
    """Main entry point — searches LinkedIn for each keyword."""
    print("[linkedin] Starting Playwright poll cycle...")

    if not SESSION_FILE.exists():
        print(f"[linkedin] No session file at {SESSION_FILE} — skipping.")
        print("[linkedin] Run reply_agent.py once to create a LinkedIn session.")
        return

    seen_in_this_cycle: set[str] = set()
    total = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Verify session is still valid
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        if "authwall" in page.url or "login" in page.url.lower():
            print("[linkedin] Session expired. Delete linkedin_session.json and re-run reply_agent.py.")
            browser.close()
            return

        for keyword in LINKEDIN_KEYWORDS:
            print(f"[linkedin] Searching: {keyword}")
            raw_posts = _scrape_keyword(page, keyword, LINKEDIN_RESULTS_PER_KEYWORD)

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
                    platform="linkedin",
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

    print(f"[linkedin] Poll complete — {total} candidate posts found")
