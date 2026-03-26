"""
Facebook Groups monitor using DuckDuckGo search — no API key required.

Searches for Facebook Group posts matching intent keywords using DuckDuckGo's
site: operator. Note: Facebook heavily restricts search engine indexing of
group content — results will be limited but can surface high-intent public posts.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import FACEBOOK_KEYWORDS, FACEBOOK_RESULTS_PER_KEYWORD

# Seconds between keyword searches — DuckDuckGo rate-limits aggressive scrapers
_REQUEST_DELAY = 3


def _make_query(keyword: str) -> str:
    """Build a DuckDuckGo query targeting Facebook Groups."""
    return f'site:facebook.com/groups "{keyword}"'


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

        # Prefer group posts; skip top-level group pages with no post content
        if "facebook.com/groups" not in url.lower():
            return None

        post_id = f"facebook_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform="facebook",
            url=url,
            author="unknown",
            title=title[:120],
            body=body,
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[facebook] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Searches DuckDuckGo for each keyword and yields unique RawPosts.
    Uses timelimit='d' to restrict results to the past week.
    """
    print("[facebook] Starting poll cycle...")
    seen_in_this_cycle: set[str] = set()

    with DDGS() as ddgs:
        for keyword in FACEBOOK_KEYWORDS:
            query = _make_query(keyword)
            print(f"[facebook] Searching: {query}")
            try:
                results = ddgs.text(query, max_results=FACEBOOK_RESULTS_PER_KEYWORD, timelimit='d')
                for result in (results or []):
                    post = _parse_result(result, keyword)
                    if post and post.id not in seen_in_this_cycle:
                        seen_in_this_cycle.add(post.id)
                        yield post
            except Exception as e:
                print(f"[facebook] Search error for '{keyword}': {e}")

            time.sleep(_REQUEST_DELAY)

    print(f"[facebook] Poll complete — {len(seen_in_this_cycle)} candidate posts found")
