"""
Twitter / X signal monitor. Uses DuckDuckGo site:x.com searches.
Returns RawSignal objects for deal flow keywords.
"""

from datetime import datetime, timezone
from typing import Generator

from ddgs import DDGS

from analyzer import RawSignal
from config import TWITTER_KEYWORDS, TWITTER_RESULTS_PER_KEYWORD
from storage import is_seen, make_id, mark_seen


def fetch_signals() -> Generator[RawSignal, None, None]:
    with DDGS() as ddg:
        for keyword in TWITTER_KEYWORDS:
            for site in ("site:x.com", "site:twitter.com"):
                query = f'{site} "{keyword}"'
                try:
                    results = list(ddg.text(query, max_results=TWITTER_RESULTS_PER_KEYWORD))
                except Exception as e:
                    print(f"[twitter] Search error for '{keyword}': {e}")
                    continue

                for r in results:
                    url = r.get("href", "") or r.get("url", "")
                    if not url:
                        continue

                    sig_id = make_id(url)
                    if is_seen(sig_id):
                        continue

                    mark_seen(sig_id, url, "twitter")
                    yield RawSignal(
                        id=sig_id,
                        platform="twitter",
                        url=url,
                        author=_extract_handle(url),
                        title=r.get("title", "")[:200],
                        body=r.get("body", "")[:800],
                        published_at=datetime.now(timezone.utc),
                    )


def _extract_handle(url: str) -> str:
    parts = url.replace("https://", "").split("/")
    if len(parts) >= 2:
        return f"@{parts[1]}"
    return ""
