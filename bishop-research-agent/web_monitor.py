"""
Web monitor — searches across LinkedIn, Quora, Twitter, Facebook,
Indie Hackers, and the general web using DuckDuckGo.

No API key required. Runs every hour to complement Reddit's 15-min cycle.
"""

import time
import re
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import WEB_SEARCH_QUERIES, WEB_RESULTS_PER_QUERY

# Seconds between queries — avoids DuckDuckGo rate-limiting
_REQUEST_DELAY = 4


def _detect_platform(url: str) -> str:
    """Tag each result with its source platform based on URL."""
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "linkedin"
    elif "quora.com" in url_lower:
        return "quora"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "facebook.com" in url_lower:
        return "facebook"
    elif "indiehackers.com" in url_lower:
        return "indiehackers"
    elif "producthunt.com" in url_lower:
        return "producthunt"
    elif "youtube.com" in url_lower:
        return "youtube"
    elif "reddit.com" in url_lower:
        return "reddit"  # skip — reddit_monitor already covers this
    else:
        return "web"


def _extract_author(title: str, url: str, platform: str) -> str:
    """Best-effort author extraction from title strings."""
    if platform == "linkedin" and " on LinkedIn" in title:
        return title.split(" on LinkedIn")[0].strip()
    if platform == "quora":
        # Quora titles are often "Question - Quora" or "Name's answer to..."
        if "'s answer to" in title:
            return title.split("'s answer")[0].strip()
    if platform == "twitter" and " on X:" in title:
        return title.split(" on X:")[0].strip()
    return "unknown"


def _parse_web_date(result: dict) -> Optional[datetime]:
    """Try to parse a publish date from a DuckDuckGo result. Returns UTC datetime or None."""
    raw = result.get("published", "") or ""
    if not raw:
        return None
    try:
        # DDG sometimes returns ISO-style dates: "2024-01-15" or "2024-01-15T12:00:00"
        date_part = raw.strip().split("T")[0]
        return datetime.fromisoformat(date_part).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_result(result: dict) -> RawPost | None:
    """Convert a DuckDuckGo result into a RawPost."""
    try:
        url = result.get("href", "")
        title = result.get("title", "")
        body = result.get("body", "")

        if not url or not body:
            return None

        platform = _detect_platform(url)
        if platform == "reddit":
            return None  # Covered by reddit_monitor

        author = _extract_author(title, url, platform)
        post_id = f"{platform}_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform=platform,
            url=url,
            author=author,
            title=title[:120],
            body=body,
            subreddit=None,
            published_at=_parse_web_date(result),
        )
    except Exception as e:
        print(f"[web] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Runs all WEB_SEARCH_QUERIES through DuckDuckGo and yields unique RawPosts.
    """
    print(f"[web] Starting poll — {len(WEB_SEARCH_QUERIES)} queries across LinkedIn, Quora, Twitter, and web...")
    seen_in_this_cycle: set[str] = set()
    counts: dict[str, int] = {}

    with DDGS() as ddgs:
        for query in WEB_SEARCH_QUERIES:
            try:
                results = ddgs.text(query, max_results=WEB_RESULTS_PER_QUERY, timelimit='w')
                for result in (results or []):
                    post = _parse_result(result)
                    if post and post.id not in seen_in_this_cycle:
                        seen_in_this_cycle.add(post.id)
                        counts[post.platform] = counts.get(post.platform, 0) + 1
                        yield post
            except Exception as e:
                print(f"[web] Query error '{query[:50]}...': {e}")

            time.sleep(_REQUEST_DELAY)

    summary = ", ".join(f"{p}: {n}" for p, n in sorted(counts.items()))
    print(f"[web] Poll complete — {len(seen_in_this_cycle)} posts found ({summary})")
