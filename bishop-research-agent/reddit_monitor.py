"""
Reddit monitor using public RSS feeds — no API key or approval required.

Two strategies per cycle:
  1. Subreddit .new feed  — catches all new posts in each subreddit, filtered by keyword
  2. Reddit search RSS    — searches across all monitored subreddits by keyword
"""

import calendar
import html
import re
import time
from datetime import datetime, timezone
from typing import Generator, Optional

import feedparser
import requests

from analyzer import RawPost
from config import REDDIT_KEYWORDS, REDDIT_SUBREDDITS

# Pre-compile keyword patterns for fast matching
_KEYWORD_PATTERNS = [
    re.compile(re.escape(kw), re.IGNORECASE) for kw in REDDIT_KEYWORDS
]

_HEADERS = {
    "User-Agent": "BishopAI-ResearchAgent/1.0 RSS Reader (non-commercial research)"
}

# Seconds to wait between subreddit fetches — be polite to Reddit's servers
_REQUEST_DELAY = 2


def _matches(text: str) -> bool:
    return any(p.search(text) for p in _KEYWORD_PATTERNS)


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities from RSS summary fields."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _post_id_from_url(url: str) -> str:
    """Extract Reddit post ID from a permalink URL."""
    # URLs look like: https://www.reddit.com/r/sub/comments/POST_ID/title/
    match = re.search(r"/comments/([a-z0-9]+)/", url)
    return match.group(1) if match else url


def _parse_published(entry) -> Optional[datetime]:
    """Parse publish timestamp from a feedparser entry. Returns UTC datetime or None."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime.fromtimestamp(calendar.timegm(entry.published_parsed), tz=timezone.utc)
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime.fromtimestamp(calendar.timegm(entry.updated_parsed), tz=timezone.utc)
    except Exception:
        pass
    return None


def _parse_entry(entry, subreddit: str | None = None) -> RawPost | None:
    """Convert a feedparser entry into a RawPost."""
    try:
        url = entry.get("link", "")
        post_id = f"reddit_post_{_post_id_from_url(url)}"
        title = _strip_html(entry.get("title", ""))
        # RSS summary contains the post body (wrapped in HTML)
        summary = _strip_html(entry.get("summary", ""))
        author = entry.get("author", "unknown").lstrip("/u/").lstrip("u/")

        # Infer subreddit from URL if not provided
        if not subreddit:
            m = re.search(r"/r/([^/]+)/", url)
            subreddit = m.group(1) if m else "unknown"

        return RawPost(
            id=post_id,
            platform="reddit",
            url=url,
            author=author,
            title=title,
            body=summary,
            subreddit=subreddit,
            published_at=_parse_published(entry),
        )
    except Exception as e:
        print(f"[reddit] Failed to parse entry: {e}")
        return None


def _fetch_feed(url: str) -> feedparser.FeedParserDict | None:
    """Fetch and parse an RSS feed URL. Returns None on failure."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return feedparser.parse(resp.text)
    except requests.RequestException as e:
        print(f"[reddit] Fetch error for {url}: {e}")
        return None


def _subreddit_new_feed(subreddit: str) -> Generator[RawPost, None, None]:
    """Fetch new posts from a single subreddit RSS feed and filter by keyword."""
    url = f"https://www.reddit.com/r/{subreddit}/new/.rss?limit=25"
    feed = _fetch_feed(url)
    if not feed:
        return

    for entry in feed.entries:
        title = _strip_html(entry.get("title", ""))
        body = _strip_html(entry.get("summary", ""))
        if _matches(f"{title} {body}"):
            post = _parse_entry(entry, subreddit)
            if post:
                yield post


def _keyword_search_feed(keyword: str) -> Generator[RawPost, None, None]:
    """Use Reddit's search RSS to find posts matching a keyword across monitored subreddits."""
    subreddit_scope = "+".join(REDDIT_SUBREDDITS)
    encoded = requests.utils.quote(keyword)
    url = (
        f"https://www.reddit.com/r/{subreddit_scope}/search.rss"
        f"?q={encoded}&restrict_sr=1&sort=new&t=week&limit=25"
    )
    feed = _fetch_feed(url)
    if not feed:
        return

    for entry in feed.entries:
        post = _parse_entry(entry)
        if post:
            yield post


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Runs subreddit .new feeds + keyword search feeds and yields unique RawPosts.
    """
    print("[reddit] Starting poll cycle...")
    seen_in_this_cycle: set[str] = set()

    # Strategy 1: scan .new feed for each subreddit, filter locally
    for subreddit in REDDIT_SUBREDDITS:
        for post in _subreddit_new_feed(subreddit):
            if post.id not in seen_in_this_cycle:
                seen_in_this_cycle.add(post.id)
                yield post
        time.sleep(_REQUEST_DELAY)

    # Strategy 2: Reddit search RSS per keyword (catches cross-sub posts)
    for keyword in REDDIT_KEYWORDS:
        for post in _keyword_search_feed(keyword):
            if post.id not in seen_in_this_cycle:
                seen_in_this_cycle.add(post.id)
                yield post
        time.sleep(_REQUEST_DELAY)

    print(f"[reddit] Poll complete — {len(seen_in_this_cycle)} candidate posts found")
