"""
LinkedIn monitor using Playwright + saved session.

Searches LinkedIn's content search (sorted by date) for each keyword and yields
RawPost objects for Claude to score. Uses the existing LinkedIn session saved
at .browser_sessions/linkedin_session.json.

If the session doesn't exist or is expired, prints a message and skips.
"""

import time
import random
import urllib.parse
from pathlib import Path
from typing import Generator

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from analyzer import RawPost
from config import LINKEDIN_KEYWORDS, LINKEDIN_RESULTS_PER_KEYWORD

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "linkedin_session.json"

# LinkedIn content search -- sortBy=date_posted gets most recent first
_SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords={query}&sortBy=date_posted"
)

# JavaScript to extract post containers from LinkedIn search results.
# LinkedIn uses obfuscated CSS classes, so we walk the DOM from stable
# anchor points (profile links) to find post containers.
_EXTRACT_POSTS_JS = """() => {
    const results = [];
    const profileLinks = document.querySelectorAll('a[href*="/in/"]');
    const seen = new Set();

    // Helper: extract urn:li:activity:NNN from any string
    const URN_RE = /urn:li:activity:(\\d+)/;
    function findActivityUrn(el) {
        // Walk up the tree looking for data-urn / data-id containing an activity URN
        let cur = el;
        for (let i = 0; i < 15 && cur; i++) {
            for (const attr of ["data-urn", "data-id", "data-chameleon-result-urn"]) {
                const v = cur.getAttribute && cur.getAttribute(attr);
                if (v) {
                    const m = v.match(URN_RE);
                    if (m) return m[1];
                }
            }
            cur = cur.parentElement;
        }
        return null;
    }

    for (const link of profileLinks) {
        const authorText = link.innerText.trim();
        if (!authorText || authorText.length < 3) continue;

        const href = link.getAttribute("href");
        if (seen.has(href)) continue;
        seen.add(href);

        // Walk up from the profile link to find the post container
        let container = link;
        for (let i = 0; i < 12; i++) {
            if (!container.parentElement) break;
            container = container.parentElement;
            if (container.tagName === "MAIN" || container.tagName === "BODY") break;
            const text = container.innerText || "";
            // Post containers have Like/Comment buttons
            if (text.length > 200 && text.includes("Like") && text.includes("Comment")) break;
        }

        const fullText = container.innerText || "";
        if (fullText.length < 50) continue;

        // 1. Try to find a direct anchor to the post
        let postUrl = "";
        const postLink = container.querySelector(
            'a[href*="/feed/update/"], a[href*="/posts/"], a[href*="urn:li:activity"]'
        );
        if (postLink) postUrl = postLink.getAttribute("href") || "";

        // 2. Fall back to scanning for an activity URN on container/ancestors
        if (!postUrl) {
            const activityId = findActivityUrn(container);
            if (activityId) {
                postUrl = "https://www.linkedin.com/feed/update/urn:li:activity:" + activityId + "/";
            }
        }

        // 3. If we still have no real post URL, skip this result entirely --
        //    we never want to log the profile URL as the lead "post link".
        if (!postUrl) continue;

        // Extract just the post body (skip the author header and action buttons)
        const lines = fullText.split("\\n").filter(l => l.trim().length > 0);
        const bodyLines = lines.slice(4, -4);
        const body = bodyLines.join(" ").substring(0, 800);

        results.push({
            author: authorText.split("\\n")[0].trim(),
            profileUrl: href,
            postUrl: postUrl,
            body: body,
            fullText: fullText.substring(0, 120),
        });
    }
    return results;
}"""


def _make_post_id(url: str, snippet: str) -> str:
    return f"linkedin_{abs(hash(url + snippet[:40]))}"


def poll() -> Generator[RawPost, None, None]:
    """Main entry point -- searches LinkedIn for each keyword."""
    print("[linkedin] Starting Playwright poll cycle...")

    if not SESSION_FILE.exists():
        print(f"[linkedin] No session file at {SESSION_FILE} -- skipping.")
        print("[linkedin] Run the login script to create a LinkedIn session.")
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
            print("[linkedin] Session expired. Delete linkedin_session.json and re-login.")
            browser.close()
            return

        for keyword in LINKEDIN_KEYWORDS:
            print(f"[linkedin] Searching: {keyword}")
            encoded = urllib.parse.quote(keyword)
            url = _SEARCH_URL.format(query=encoded)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(random.uniform(3, 5))

                # Scroll to load more results
                page.keyboard.press("End")
                time.sleep(random.uniform(1.5, 2.5))

                # Extract posts using JS DOM walker
                raw_posts = page.evaluate(_EXTRACT_POSTS_JS)

                for raw in raw_posts[:LINKEDIN_RESULTS_PER_KEYWORD]:
                    post_url = raw["postUrl"]
                    if post_url.startswith("/"):
                        post_url = "https://www.linkedin.com" + post_url
                    post_url = post_url.split("?")[0]

                    post_id = _make_post_id(post_url, raw["body"])
                    if post_id in seen_in_this_cycle:
                        continue
                    seen_in_this_cycle.add(post_id)
                    total += 1

                    title = raw["fullText"][:120]
                    print(f"[linkedin]   -> {post_url}")

                    yield RawPost(
                        id=post_id,
                        platform="linkedin",
                        url=post_url,
                        author=raw["author"],
                        title=title,
                        body=raw["body"][:800],
                        subreddit=None,
                        published_at=None,
                    )

            except PlaywrightTimeout:
                print(f"[linkedin] Timeout searching for '{keyword}'")
            except Exception as e:
                print(f"[linkedin] Error searching for '{keyword}': {e}")

            time.sleep(random.uniform(3, 6))

        # Refresh saved session
        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    print(f"[linkedin] Poll complete -- {total} candidate posts found")
