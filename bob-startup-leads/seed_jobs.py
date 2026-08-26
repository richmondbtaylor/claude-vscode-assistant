"""Lane 1: companies with an open finance or admin requisition.

Primary source is Brave Search against public ATS boards. Those pages are
static and unauthenticated and they name the employer in the URL path.
"""
import argparse
import os
import pathlib
import time
from urllib.parse import urlparse

import httpx

import config
from lib.records import company_id, write_jsonl

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
ENV_PATH = pathlib.Path.home() / ".claude" / "security" / "bishop-research-agent.env"

# The employer slug is the first path segment on each ATS host.
ATS_SLUG_INDEX = {
    "boards.greenhouse.io": 0,
    "jobs.lever.co": 0,
    "apply.workable.com": 0,
    "jobs.ashbyhq.com": 0,
    "jobs.smartrecruiters.com": 0,
}


def _brave_key() -> str:
    key = os.environ.get("BRAVE_API_KEY")
    if key:
        return key
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("BRAVE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("BRAVE_API_KEY not found in env or security env file")


def brave_search(query: str, count: int = 20) -> list[dict]:
    """Return Brave web results as dicts with title, url and description."""
    resp = httpx.get(
        BRAVE_ENDPOINT,
        params={"q": query, "count": count, "country": "us"},
        headers={"X-Subscription-Token": _brave_key(), "Accept": "application/json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""),
         "description": r.get("description", "")}
        for r in resp.json().get("web", {}).get("results", [])
    ]


def parse_ats_result(result: dict) -> dict | None:
    """Turn one ATS search result into a seed record, or None if it is noise."""
    url = result.get("url") or ""
    host = urlparse(url).netloc.lower()
    if host not in ATS_SLUG_INDEX:
        return None
    parts = [p for p in urlparse(url).path.split("/") if p]
    idx = ATS_SLUG_INDEX[host]
    if len(parts) <= idx:
        return None
    slug = parts[idx]
    name = slug.replace("-", " ").replace("_", " ").strip().title().replace(" ", "")
    if not name or len(name) < 3:
        return None

    return {
        "company_id": company_id(name, "", None),
        "name": name,
        "domain": None,
        "website": None,
        "phone": None,
        "email": None,
        "email_status": "none",
        "address": "", "city": "", "state": "", "zip": "",
        "naics": "", "category": "",
        "sources": ["jobs"],
        "signals": {
            "open_finance_req": True,
            "job_title": result.get("title", ""),
            "job_url": url,
            "job_blurb": result.get("description", ""),
            "needs_liveness_check": False,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=20)
    args = ap.parse_args()

    rows, seen = [], set()
    for title in config.JOB_TITLES:
        for host in config.ATS_HOSTS:
            query = f'site:{host} "{title}"'
            try:
                results = brave_search(query, args.per_query)
            except httpx.HTTPError as exc:
                print(f"skip {query}: {exc}")
                continue
            for r in results:
                row = parse_ats_result(r)
                if row and row["company_id"] not in seen:
                    seen.add(row["company_id"])
                    rows.append(row)
            print(f"{query}: {len(rows)} total")
            time.sleep(1.1)  # Brave free tier is rate limited to about 1 qps

    n = write_jsonl(config.DATA / "seed_jobs.jsonl", rows)
    print(f"wrote {n} rows to data/seed_jobs.jsonl")


if __name__ == "__main__":
    main()
