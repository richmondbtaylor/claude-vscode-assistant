"""
LinkedIn monitor using Playwright + saved session.
Session file: .browser_sessions/linkedin.json
"""

import time
import random
import urllib.parse
from pathlib import Path
from typing import Generator

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from analyzer import RawPost
from config import LINKEDIN_KEYWORDS, LINKEDIN_RESULTS_PER_KEYWORD

SESSION_FILE = Path(__file__).parent / ".browser_sessions" / "linkedin.json"

_SEARCH_URL = (
    "https://www.linkedin.com/search/results/content/"
    "?keywords={query}&sortBy=date_posted"
)

_EXTRACT_POSTS_JS = """() => {
    const results = [];
    const seenUrls = new Set();

    function getContainer(el, maxSteps) {
        let cur = el;
        for (let i = 0; i < maxSteps && cur; i++) {
            const text = cur.innerText || "";
            if (text.length > 150) return cur;
            if (!cur.parentElement) break;
            cur = cur.parentElement;
            if (cur.tagName === "MAIN" || cur.tagName === "BODY") return null;
        }
        return null;
    }

    function findAuthor(container) {
        const profileLink = container.querySelector('a[href*="/in/"]');
        if (profileLink) {
            const t = (profileLink.innerText || "").trim().split("\\n")[0].trim();
            if (t.length >= 3) return { name: t, url: profileLink.getAttribute("href") || "" };
        }
        return { name: "unknown", url: "" };
    }

    // Strategy 1: start from post-level anchors (stable LinkedIn URL pattern)
    const postAnchors = document.querySelectorAll(
        'a[href*="/feed/update/urn:li:activity"], a[href*="/posts/"]'
    );
    for (const anchor of postAnchors) {
        let postUrl = anchor.getAttribute("href") || "";
        if (!postUrl) continue;
        if (postUrl.startsWith("/")) postUrl = "https://www.linkedin.com" + postUrl;
        postUrl = postUrl.split("?")[0];
        if (seenUrls.has(postUrl)) continue;
        seenUrls.add(postUrl);

        const container = getContainer(anchor, 15);
        if (!container) continue;
        const fullText = container.innerText || "";
        if (fullText.length < 50) continue;

        const { name: author, url: profileUrl } = findAuthor(container);
        const lines = fullText.split("\\n").filter(l => l.trim().length > 0);
        const body = lines.slice(2, -3).join(" ").substring(0, 800);

        results.push({ author, profileUrl, postUrl, body, fullText: fullText.substring(0, 120) });
    }

    // Strategy 2: containers with chameleon result URN (LinkedIn search result wrappers)
    if (results.length === 0) {
        const URN_RE = /urn:li:activity:(\\d+)/;
        const urnEls = document.querySelectorAll(
            "[data-chameleon-result-urn], [data-urn], [data-entity-urn]"
        );
        for (const el of urnEls) {
            const urnAttrs = ["data-chameleon-result-urn", "data-urn", "data-entity-urn"];
            let activityId = null;
            for (const attr of urnAttrs) {
                const v = el.getAttribute(attr) || "";
                const m = v.match(URN_RE);
                if (m) { activityId = m[1]; break; }
            }
            if (!activityId) continue;

            const postUrl = "https://www.linkedin.com/feed/update/urn:li:activity:" + activityId + "/";
            if (seenUrls.has(postUrl)) continue;
            seenUrls.add(postUrl);

            const fullText = el.innerText || "";
            if (fullText.length < 50) continue;

            const { name: author, url: profileUrl } = findAuthor(el);
            const lines = fullText.split("\\n").filter(l => l.trim().length > 0);
            const body = lines.slice(2, -3).join(" ").substring(0, 800);

            results.push({ author, profileUrl, postUrl, body, fullText: fullText.substring(0, 120) });
        }
    }

    return results;
}"""


def _make_post_id(url: str, snippet: str) -> str:
    return f"linkedin_{abs(hash(url + snippet[:40]))}"


def poll() -> Generator[RawPost, None, None]:
    print("[linkedin] Starting Playwright poll cycle...")

    if not SESSION_FILE.exists():
        print(f"[linkedin] No session file at {SESSION_FILE} -- skipping.")
        print("[linkedin] Run login_linkedin.py to create a session.")
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

        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        if "authwall" in page.url or "login" in page.url.lower():
            print("[linkedin] Session expired. Run login_linkedin.py to re-login.")
            browser.close()
            return

        for keyword in LINKEDIN_KEYWORDS:
            print(f"[linkedin] Searching: {keyword}")
            encoded = urllib.parse.quote(keyword)
            url = _SEARCH_URL.format(query=encoded)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(random.uniform(3, 5))

                page.keyboard.press("End")
                time.sleep(random.uniform(1.5, 2.5))

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

        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    print(f"[linkedin] Poll complete -- {total} candidate posts found")
