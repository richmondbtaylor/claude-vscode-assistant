"""
Web monitor using Brave Search API.

Replaces DuckDuckGo for web queries — gives reliable date filtering,
higher result quality, and no rate-limit blocking on exact-phrase searches.

Free tier: 2,000 queries/month (enough for 36 queries/day = ~1,080/month).
Get your API key at: https://brave.com/search/api/
"""

import os
import time
from datetime import datetime, timezone
from typing import Generator, Optional

import requests

from analyzer import RawPost
from config import WEB_SEARCH_QUERIES, WEB_RESULTS_PER_QUERY

_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2   # Brave free tier: 1 req/sec — add small buffer


def _get_api_key() -> Optional[str]:
    return os.environ.get("BRAVE_API_KEY", "").strip() or None


def _detect_platform(url: str) -> str:
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
        return "reddit"
    else:
        return "web"


def _extract_author(title: str, url: str, platform: str) -> str:
    if platform == "linkedin" and " on LinkedIn" in title:
        return title.split(" on LinkedIn")[0].strip()
    if platform == "quora" and "'s answer to" in title:
        return title.split("'s answer")[0].strip()
    if platform == "twitter" and " on X:" in title:
        return title.split(" on X:")[0].strip()
    return "unknown"


def _parse_date(result: dict) -> Optional[datetime]:
    """Parse page_age from Brave result. Returns UTC datetime or None."""
    raw = result.get("page_age", "") or result.get("age", "") or ""
    if not raw:
        return None
    try:
        # Brave returns ISO format: "2024-01-15T12:00:00"
        return datetime.fromisoformat(raw.split("T")[0]).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _search(query: str, api_key: str, count: int = 10) -> list[dict]:
    """Run a single Brave Search query. Returns list of result dicts."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": min(count, 20),   # Brave max is 20 per request
        "freshness": "pd",          # past day — server-side date filter
        "text_decorations": "false",
        "search_lang": "en",
    }
    try:
        resp = requests.get(_BASE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("web", {}).get("results", [])
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            print(f"[brave] Rate limit hit — backing off 5s")
            time.sleep(5)
        else:
            print(f"[brave] HTTP error for query '{query[:50]}': {e}")
        return []
    except Exception as e:
        print(f"[brave] Error for query '{query[:50]}': {e}")
        return []


def _parse_result(result: dict) -> Optional[RawPost]:
    """Convert a Brave result dict into a RawPost."""
    try:
        url = result.get("url", "")
        title = result.get("title", "")
        body = result.get("description", "") or result.get("extra_snippets", [""])[0]

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
            body=body[:1000],
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[brave] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Runs all WEB_SEARCH_QUERIES through Brave Search and yields unique RawPosts.
    Falls back to DuckDuckGo monitor if BRAVE_API_KEY is not set.
    """
    api_key = _get_api_key()
    if not api_key:
        print("[brave] BRAVE_API_KEY not set — falling back to DuckDuckGo")
        import web_monitor
        yield from web_monitor.poll()
        return

    print(f"[brave] Starting poll — {len(WEB_SEARCH_QUERIES)} queries with freshness=pd...")
    seen_in_this_cycle: set[str] = set()
    counts: dict[str, int] = {}
    no_result_count = 0

    for query in WEB_SEARCH_QUERIES:
        results = _search(query, api_key, count=WEB_RESULTS_PER_QUERY)

        if not results:
            no_result_count += 1
        else:
            for result in results:
                post = _parse_result(result)
                if post and post.id not in seen_in_this_cycle:
                    seen_in_this_cycle.add(post.id)
                    counts[post.platform] = counts.get(post.platform, 0) + 1
                    yield post

        time.sleep(_REQUEST_DELAY)

    summary = ", ".join(f"{p}: {n}" for p, n in sorted(counts.items()))
    print(
        f"[brave] Poll complete — {len(seen_in_this_cycle)} posts found "
        f"({summary}) | {no_result_count} queries returned 0 results"
    )
