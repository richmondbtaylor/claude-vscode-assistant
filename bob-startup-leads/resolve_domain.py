"""Find a company website for seed rows that arrived without one.

Strict on purpose. A wrong domain poisons every downstream stage, so an
unresolved company is preferable to a mismatched one.
"""
import argparse
import time

from rapidfuzz import fuzz

import config
from lib.records import read_jsonl, write_jsonl
from seed_jobs import brave_search
from lib.normalize import norm_name, registrable_domain

MATCH_THRESHOLD = 82


def pick_domain(company_name: str, city: str, state: str,
                results: list[dict]) -> str | None:
    """Return the best matching company domain, or None if nothing matches well."""
    target = norm_name(company_name).replace(" ", "")
    if not target:
        return None

    for result in results:
        domain = registrable_domain(result.get("url"))
        if not domain:
            continue  # social and directory hosts are filtered by registrable_domain
        stem = domain.rsplit(".", 1)[0].replace("-", "").replace("_", "")
        if fuzz.ratio(target, stem) >= MATCH_THRESHOLD:
            return domain
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="companies.jsonl")
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    rows, resolved, attempted = [], 0, 0
    for row in read_jsonl(config.DATA / args.infile):
        if row.get("domain") or attempted >= args.limit:
            rows.append(row)
            continue
        attempted += 1
        query = " ".join(x for x in [row["name"], row.get("city"), row.get("state")] if x)
        try:
            results = brave_search(query, count=8)
        except Exception as exc:
            print(f"skip {row['name']}: {exc}")
            rows.append(row)
            continue
        domain = pick_domain(row["name"], row.get("city", ""), row.get("state", ""), results)
        if domain:
            row["domain"] = domain
            row["website"] = f"https://{domain}"
            resolved += 1
        rows.append(row)
        time.sleep(1.1)

    n = write_jsonl(config.DATA / "resolved.jsonl", rows)
    print(f"attempted {attempted}, resolved {resolved}, wrote {n} rows")


if __name__ == "__main__":
    main()
