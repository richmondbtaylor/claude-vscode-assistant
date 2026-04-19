"""
LinkedIn signal monitor. Uses DuckDuckGo to find LinkedIn posts matching deal flow keywords.
Returns RawSignal objects for each result.
"""

from datetime import datetime, timezone
from typing import Generator

from ddgs import DDGS

from analyzer import RawSignal
from config import LINKEDIN_KEYWORDS, LINKEDIN_RESULTS_PER_KEYWORD
from storage import is_seen, make_id, mark_seen


def fetch_signals() -> Generator[RawSignal, None, None]:
    with DDGS() as ddg:
        for keyword in LINKEDIN_KEYWORDS:
            query = f'site:linkedin.com/posts "{keyword}"'
            try:
                results = list(ddg.text(query, max_results=LINKEDIN_RESULTS_PER_KEYWORD))
            except Exception as e:
                print(f"[linkedin] Search error for '{keyword}': {e}")
                continue

            for r in results:
                url = r.get("href", "") or r.get("url", "")
                if not url or "linkedin.com" not in url:
                    continue

                sig_id = make_id(url)
                if is_seen(sig_id):
                    continue

                mark_seen(sig_id, url, "linkedin")
                yield RawSignal(
                    id=sig_id,
                    platform="linkedin",
                    url=url,
                    author=r.get("source", "") or _extract_author(url),
                    title=r.get("title", "")[:200],
                    body=r.get("body", "")[:800],
                    published_at=_parse_date(r.get("published", "")),
                )


def _extract_author(url: str) -> str:
    parts = url.split("/")
    try:
        idx = parts.index("in")
        return parts[idx + 1].replace("-", " ").title()
    except (ValueError, IndexError):
        return ""


def _parse_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        from dateutil import parser
        return parser.parse(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
