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


def _glued_name(row: dict) -> str:
    """Normalized name with all whitespace stripped, so a glued ATS slug
    ("riveramechanical") equals the spaced legal name it was derived from
    ("Rivera Mechanical"). RULING C21 point 2."""
    return norm_name(row.get("name", "")).replace(" ", "")


def _state(row: dict) -> str:
    return (row.get("state") or "").upper()


def _states_compatible(state_a: str, state_b: str) -> bool:
    """A state-less row (job lane) matches any state; two rows that both
    carry a state must agree. RULING C21 point 1."""
    return state_a == "" or state_b == "" or state_a == state_b


def _conflicts(a: dict, b: dict) -> bool:
    """True when a and b carry a strong identifier each and those identifiers
    disagree. RULING C20: this gates the name+state fallback only. Domain and
    phone matches themselves stay unconditional and are never passed through
    this check to reject a merge."""
    da, db = a.get("domain"), b.get("domain")
    if da and db and da.lower() != db.lower():
        return True
    pa, pb = a.get("phone"), b.get("phone")
    if pa and pb and pa != pb:
        return True
    return False


def dedupe(rows: list[dict]) -> list[dict]:
    """Collapse rows that share a domain, an E.164 phone, or a normalized
    name plus state. Order independent.

    Domain and phone are unconditional identity keys: sharing either is
    strong evidence of sameness, full stop. The name+state key is a weak
    fallback: RULING C20 vetoes it whenever both rows carry a domain (or
    both carry a phone) and those values disagree, so two distinct
    companies that merely share a name and a state never collapse into one
    just because a third row links them through that weak key. RULING C21
    loosens the weak key itself: a state-less row (job lane) matches any
    state, and names are compared with whitespace stripped so a glued ATS
    slug matches the spaced legal name it came from.
    """
    domain_index: dict[str, int] = {}
    phone_index: dict[str, int] = {}
    name_index: dict[str, set[int]] = {}
    merged: list[dict | None] = []

    def strong_hits(row: dict) -> set[int]:
        """Unconditional hits: exact domain or exact phone match."""
        hits = set()
        if row.get("domain"):
            idx = domain_index.get(row["domain"].lower())
            if idx is not None and merged[idx] is not None:
                hits.add(idx)
        if row.get("phone"):
            idx = phone_index.get(row["phone"])
            if idx is not None and merged[idx] is not None:
                hits.add(idx)
        return hits

    def weak_hits(row: dict) -> set[int]:
        """Name+state hits, filtered by state compatibility and the C20
        veto against the row itself."""
        glued = _glued_name(row)
        if not glued:
            return set()
        row_state = _state(row)
        hits = set()
        for idx in name_index.get(glued, ()):
            rec = merged[idx]
            if rec is None:
                continue
            if not _states_compatible(row_state, _state(rec)):
                continue
            if _conflicts(row, rec):
                continue
            hits.add(idx)
        return hits

    def index_row(slot: int, row: dict) -> None:
        if row.get("domain"):
            domain_index[row["domain"].lower()] = slot
        if row.get("phone"):
            phone_index[row["phone"]] = slot
        glued = _glued_name(row)
        if glued:
            name_index.setdefault(glued, set()).add(slot)

    for row in rows:
        candidates = sorted(strong_hits(row) | weak_hits(row))

        if not candidates:
            slot = len(merged)
            merged.append(dict(row))
        else:
            slot = candidates[0]
            base = merged[slot]
            for other in candidates[1:]:
                other_rec = merged[other]
                if other_rec is None:
                    continue
                if _conflicts(base, other_rec):
                    # These two slots were both pulled in by this row's weak
                    # key, but they conflict on a strong identifier with
                    # each other. Leave the other slot standalone rather
                    # than let this row bridge two distinct companies
                    # together (RULING C20's transitive case).
                    continue
                base = merge_pair(base, other_rec)
                merged[other] = None
            merged[slot] = merge_pair(base, row)

        index_row(slot, merged[slot])
        index_row(slot, row)

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
