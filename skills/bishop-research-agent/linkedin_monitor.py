"""
LinkedIn monitor using DuckDuckGo search — no API key required.

Searches for LinkedIn posts matching intent keywords using DuckDuckGo's
site: operator. Returns the URL + text snippet for each result,
which is enough for Claude to score and classify intent.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import LINKEDIN_KEYWORDS, LINKEDIN_RESULTS_PER_KEYWORD

# Seconds between keyword searches — DuckDuckGo rate-limits aggressive scrapers
_REQUEST_DELAY = 3


def _make_query(keyword: str) -> str:
    """Build a DuckDuckGo query targeting LinkedIn posts."""
    return f'site:linkedin.com/posts "{keyword}"'


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

        # Extract a rough author name from the title
        # LinkedIn titles often look like: "John Doe on LinkedIn: ..."
        author = "unknown"
        if " on LinkedIn" in title:
            author = title.split(" on LinkedIn")[0].strip()

        # Use URL path as a stable ID
        post_id = f"linkedin_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform="linkedin",
            url=url,
            author=author,
            title=title[:120],
            body=body,
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[linkedin] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Searches DuckDuckGo for each keyword and yields unique RawPosts.
    Uses timelimit='d' to restrict results to the past week.
    """
    print("[linkedin] Starting poll cycle...")
    seen_in_this_cycle: set[str] = set()

    with DDGS() as ddgs:
        for keyword in LINKEDIN_KEYWORDS:
            query = _make_query(keyword)
            print(f"[linkedin] Searching: {query}")
            try:
                results = ddgs.text(query, max_results=LINKEDIN_RESULTS_PER_KEYWORD, timelimit='d')
                for result in (results or []):
                    post = _parse_result(result, keyword)
                    if post and post.id not in seen_in_this_cycle:
                        seen_in_this_cycle.add(post.id)
                        yield post
            except Exception as e:
                print(f"[linkedin] Search error for '{keyword}': {e}")

            time.sleep(_REQUEST_DELAY)

    print(f"[linkedin] Poll complete — {len(seen_in_this_cycle)} candidate posts found")
