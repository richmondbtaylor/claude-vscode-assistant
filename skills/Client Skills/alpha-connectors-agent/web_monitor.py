"""
Web signal monitor. Runs structured DuckDuckGo queries targeting press releases,
Crunchbase, USASpending, LinkedIn, and Twitter for deal flow signals.
"""

from datetime import datetime, timezone
from typing import Generator

from ddgs import DDGS

from analyzer import RawSignal
from config import WEB_RESULTS_PER_QUERY, WEB_SEARCH_QUERIES
from storage import is_seen, make_id, mark_seen


def fetch_signals() -> Generator[RawSignal, None, None]:
    with DDGS() as ddg:
        for query in WEB_SEARCH_QUERIES:
            try:
                results = list(ddg.text(query, max_results=WEB_RESULTS_PER_QUERY))
            except Exception as e:
                print(f"[web] Search error for query '{query[:60]}': {e}")
                continue

            for r in results:
                url = r.get("href", "") or r.get("url", "")
                if not url:
                    continue

                sig_id = make_id(url)
                if is_seen(sig_id):
                    continue

                mark_seen(sig_id, url, "web")
                platform = _detect_platform(url)
                yield RawSignal(
                    id=sig_id,
                    platform=platform,
                    url=url,
                    author=r.get("source", "")[:100],
                    title=r.get("title", "")[:200],
                    body=r.get("body", "")[:800],
                    published_at=_parse_date(r.get("published", "")),
                )


def _detect_platform(url: str) -> str:
    if "linkedin.com" in url:
        return "linkedin"
    if "x.com" in url or "twitter.com" in url:
        return "twitter"
    if "businesswire.com" in url:
        return "businesswire"
    if "prnewswire.com" in url:
        return "prnewswire"
    if "techcrunch.com" in url:
        return "techcrunch"
    if "crunchbase.com" in url:
        return "crunchbase"
    if "usaspending.gov" in url or "sam.gov" in url:
        return "gov"
    if "energy.gov" in url:
        return "doe"
    return "web"


def _parse_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        from dateutil import parser
        return parser.parse(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
