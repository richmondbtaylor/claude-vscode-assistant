"""Merge every seed lane into one record per company."""
import argparse

import config
from lib.normalize import norm_name
from lib.records import read_jsonl, write_jsonl

SEED_FILES = ("seed_sba.jsonl", "seed_jobs.jsonl", "seed_maps.jsonl")
SCALAR_FIELDS = ("name", "domain", "website", "phone", "email", "address",
                 "city", "state", "zip", "naics", "category")


def merge_pair(a: dict, b: dict) -> dict:
    """Merge b into a. Existing populated values win; blanks get filled."""
    out = dict(a)
    for field in SCALAR_FIELDS:
        if not out.get(field) and b.get(field):
            out[field] = b[field]
    out["signals"] = {**b.get("signals", {}), **a.get("signals", {})}
    out["sources"] = sorted(set(a.get("sources", [])) | set(b.get("sources", [])))
    if b.get("signals", {}).get("needs_liveness_check") is False:
        out["signals"]["needs_liveness_check"] = False
    return out


def _keys(row: dict) -> list[str]:
    """Identity keys in precedence order."""
    keys = []
    if row.get("domain"):
        keys.append("d:" + row["domain"].lower())
    if row.get("phone"):
        keys.append("p:" + row["phone"])
    name = norm_name(row.get("name", ""))
    if name:
        keys.append(f"n:{name}|{(row.get('state') or '').upper()}")
    return keys


def dedupe(rows: list[dict]) -> list[dict]:
    """Collapse rows that share any identity key. Order independent."""
    index: dict[str, int] = {}
    merged: list[dict | None] = []

    for row in rows:
        hits = sorted({index[k] for k in _keys(row) if k in index})
        if not hits:
            slot = len(merged)
            merged.append(dict(row))
        else:
            slot = hits[0]
            base = merged[slot]
            for other in hits[1:]:
                base = merge_pair(base, merged[other])
                merged[other] = None
            merged[slot] = merge_pair(base, row)

        for key in _keys(merged[slot]):
            index[key] = slot
        for key in _keys(row):
            index[key] = slot

    return [m for m in merged if m is not None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="companies.jsonl")
    args = ap.parse_args()

    rows = []
    for name in SEED_FILES:
        batch = list(read_jsonl(config.DATA / name))
        print(f"{name}: {len(batch)} rows")
        rows.extend(batch)

    out = dedupe(rows)
    print(f"{len(rows)} seed rows collapsed to {len(out)} companies")
    write_jsonl(config.DATA / args.out, out)


if __name__ == "__main__":
    main()
