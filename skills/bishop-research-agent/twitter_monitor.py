"""
Twitter / X monitor using DuckDuckGo search — no API key required.

Searches for tweets matching intent keywords using DuckDuckGo's site: operator.
Note: Twitter/X has significantly restricted search engine indexing since 2023 —
results are limited. For higher volume, the Twitter API v2 would be needed.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import TWITTER_KEYWORDS, TWITTER_RESULTS_PER_KEYWORD

# Seconds between keyword searches — DuckDuckGo rate-limits aggressive scrapers
_REQUEST_DELAY = 3


def _make_query(keyword: str) -> str:
    """Build a DuckDuckGo query targeting Twitter/X."""
    return f'(site:twitter.com OR site:x.com) "{keyword}"'


def _parse_date(result: dict) -> Optional[datetime]:
    """Try to parse a publish date from a DuckDuckGo result. Returns UTC datetime or None."""
    raw = result.get("published", "") or ""
    if not raw:
        return None
    try:
        date_part = raw.strip().split("T")[0]
        return datetime.fromisoformat(date_part).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_result(result: dict, keyword: str) -> RawPost | None:
    """Convert a DuckDuckGo search result into a RawPost."""
    try:
        url = result.get("href", "")
        title = result.get("title", "")
        body = result.get("body", "")

        if not url or not body:
            return None

        # Extract author from title — Twitter/X titles: "Name on X: ..." or "Name (@handle)..."
        author = "unknown"
        if " on X:" in title:
            author = title.split(" on X:")[0].strip()
        elif " on Twitter:" in title:
            author = title.split(" on Twitter:")[0].strip()
        elif " (@" in title:
            author = title.split(" (@")[0].strip()

        post_id = f"twitter_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform="twitter",
            url=url,
            author=author,
            title=title[:120],
            body=body,
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[twitter] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Searches DuckDuckGo for each keyword and yields unique RawPosts.
    Uses timelimit='d' to restrict results to the past week.
    """
    print("[twitter] Starting poll cycle...")
    seen_in_this_cycle: set[str] = set()

    with DDGS() as ddgs:
        for keyword in TWITTER_KEYWORDS:
            query = _make_query(keyword)
            print(f"[twitter] Searching: {query}")
            try:
                results = ddgs.text(query, max_results=TWITTER_RESULTS_PER_KEYWORD, timelimit='d')
                for result in (results or []):
                    post = _parse_result(result, keyword)
                    if post and post.id not in seen_in_this_cycle:
                        seen_in_this_cycle.add(post.id)
                        yield post
            except Exception as e:
                print(f"[twitter] Search error for '{keyword}': {e}")

            time.sleep(_REQUEST_DELAY)

    print(f"[twitter] Poll complete — {len(seen_in_this_cycle)} candidate posts found")
