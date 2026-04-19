"""
Web monitor — searches across LinkedIn, Quora, Twitter, Facebook,
and the general web using DuckDuckGo. Fallback when Brave API key not set.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import WEB_SEARCH_QUERIES, WEB_RESULTS_PER_QUERY

_REQUEST_DELAY = 4


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


def _parse_web_date(result: dict) -> Optional[datetime]:
    raw = result.get("published", "") or ""
    if not raw:
        return None
    try:
        date_part = raw.strip().split("T")[0]
        return datetime.fromisoformat(date_part).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_result(result: dict) -> RawPost | None:
    try:
        url = result.get("href", "")
        title = result.get("title", "")
        body = result.get("body", "")

        if not url or not body:
            return None

        platform = _detect_platform(url)
        if platform == "reddit":
            return None

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
    print(f"[web] Starting poll — {len(WEB_SEARCH_QUERIES)} queries...")
    seen_in_this_cycle: set[str] = set()
    counts: dict[str, int] = {}

    with DDGS() as ddgs:
        for query in WEB_SEARCH_QUERIES:
            try:
                results = ddgs.text(query, max_results=WEB_RESULTS_PER_QUERY, timelimit='d')
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
