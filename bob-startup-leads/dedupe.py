"""Merge every seed lane into one record per company."""
import argparse
from collections import defaultdict

import config
from lib.normalize import norm_name
from lib.records import read_jsonl, write_jsonl

SEED_FILES = ("seed_sba.jsonl", "seed_jobs.jsonl", "seed_maps.jsonl")
SCALAR_FIELDS = ("name", "domain", "website", "phone", "email", "address",
                 "city", "state", "zip", "naics", "category")


def _max_present(a, b):
    """The greater of two values; a present value always beats an absent
    (None / missing) one. Associative and commutative, so it composes
    correctly through any grouping of a multi-way merge."""
    if a is None:
        return b
    if b is None:
        return a
    return a if a >= b else b


def _or_present(a, b):
    """Logical OR, but two absent values stay absent rather than becoming
    False."""
    if a is None and b is None:
        return None
    return bool(a) or bool(b)


def _needs_liveness_check_merge(a, b):
    """A present False always wins (RULING C20's original rule, unchanged):
    once any contributing row proves the company is still trading, the
    liveness flag clears for good, through any number of merges."""
    if a is False or b is False:
        return False
    if a is None:
        return b
    if b is None:
        return a
    return bool(a) or bool(b)


def _list_union(a, b):
    """Union of two list-valued signals, sorted for a deterministic order
    that does not depend on which side supplied which items or in what
    order they arrived."""
    return sorted(set(a or []) | set(b or []))


# RULING C25: explicit per-key merge policy for `signals`, kept as data
# rather than a chain of special cases. Any key not listed here keeps the
# original first-writer-wins behaviour (whichever side has it, preferring
# a). Any key whose value is a list is unioned regardless of whether its
# name appears here.
SIGNAL_MERGE_POLICY = {
    "loan_amount": _max_present,
    "jobs_supported": _max_present,
    "loan_fy": _max_present,
    "reviews": _max_present,
    "rating": _max_present,
    "open_finance_req": _or_present,
    "needs_liveness_check": _needs_liveness_check_merge,
}


def _merge_signals(a_signals: dict, b_signals: dict) -> dict:
    out = {}
    for key in set(a_signals) | set(b_signals):
        a_present, b_present = key in a_signals, key in b_signals
        a_val = a_signals.get(key)
        b_val = b_signals.get(key)
        if key in SIGNAL_MERGE_POLICY:
            out[key] = SIGNAL_MERGE_POLICY[key](
                a_val if a_present else None, b_val if b_present else None
            )
        elif isinstance(a_val, list) or isinstance(b_val, list):
            out[key] = _list_union(a_val, b_val)
        else:
            out[key] = a_val if a_present else b_val
    return out


def merge_pair(a: dict, b: dict) -> dict:
    """Merge b into a. Existing populated values win; blanks get filled.

    RULING C24: email_status travels with email. It is not an independent
    scalar field -- if email gets filled from b, b's email_status comes
    with it, so a verified label never ends up describing a different,
    unverified address.

    RULING C25: signals merge by an explicit per-key policy
    (SIGNAL_MERGE_POLICY), not a blind dict union, so a company with two
    SBA loans does not silently lose one loan's figures.
    """
    out = dict(a)
    email_filled_from_b = not out.get("email") and bool(b.get("email"))
    for field in SCALAR_FIELDS:
        if not out.get(field) and b.get(field):
            out[field] = b[field]
    if email_filled_from_b:
        out["email_status"] = b.get("email_status")
    out["signals"] = _merge_signals(a.get("signals", {}), b.get("signals", {}))
    out["sources"] = sorted(set(a.get("sources", [])) | set(b.get("sources", [])))
    return out


def _glued_name(row: dict) -> str:
    """Normalized name with all whitespace stripped, so a glued ATS slug
    ("riveramechanical") equals the spaced legal name it was derived from
    ("Rivera Mechanical"). RULING C21 point 2."""
    return norm_name(row.get("name", "")).replace(" ", "")


def _state(row: dict) -> str:
    return (row.get("state") or "").upper()


class _UnionFind:
    """Plain union-find over row indices 0..n-1."""

    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[rj] = ri


def _group_identity(rows: list[dict], idxs: list[int]) -> tuple[set, set, set]:
    """The domains, phones and states present anywhere in a group of rows."""
    domains = {rows[i]["domain"].lower() for i in idxs if rows[i].get("domain")}
    phones = {rows[i]["phone"] for i in idxs if rows[i].get("phone")}
    states = {_state(rows[i]) for i in idxs if _state(rows[i])}
    return domains, phones, states


def _identity_conflicts(id_a: tuple, id_b: tuple) -> bool:
    """RULING C20 / C22: two groups conflict on a field only when BOTH carry
    a value for it and those value sets share nothing. A field neither side
    has, or a state-less row's empty state set, never conflicts -- that is
    what lets a job-lane row bridge across lanes at all."""
    da, pa, sa = id_a
    db, pb, sb = id_b
    if da and db and da.isdisjoint(db):
        return True
    if pa and pb and pa.isdisjoint(pb):
        return True
    if sa and sb and sa.isdisjoint(sb):
        return True
    return False


def dedupe(rows: list[dict]) -> list[dict]:
    """Collapse rows that share a domain, an E.164 phone, or a normalized
    name plus state, into one record per company. Fully order independent:
    the grouping is computed from set and graph operations over the whole
    input at once, never from a running, order-sensitive scan, so the
    result cannot depend on which row happened to arrive first.

    Domain and phone are unconditional identity keys (RULING C20): sharing
    either always merges two rows, even if some other field disagrees.
    Those merges form seed groups first, in a phase that never vetoes
    anything.

    The name+state key only links seed groups that don't already share a
    domain or phone. RULING C20 / C22 vetoes that link whenever the two
    groups both carry a domain, a phone, or a state, and those values
    disagree. RULING C21 loosens the key itself: a state-less row (job
    lane) is compatible with any state, and names are compared with
    whitespace stripped so a glued ATS slug matches the spaced legal name
    it came from.

    RULING C23: if a seed group's weak key would link it to two OTHER seed
    groups that conflict with each other, none of that group's weak links
    fire -- it joins neither rather than an arbitrary tiebreak pick. This
    is what keeps the result identical regardless of row order: a bridging
    row never gets to silently pick a side.
    """
    n = len(rows)
    if n == 0:
        return []

    uf = _UnionFind(n)

    # Phase 1: domain and phone equality, unconditional, no vetoes.
    domain_first: dict[str, int] = {}
    phone_first: dict[str, int] = {}
    for i, row in enumerate(rows):
        domain = row.get("domain")
        if domain:
            domain = domain.lower()
            if domain in domain_first:
                uf.union(domain_first[domain], i)
            else:
                domain_first[domain] = i
        phone = row.get("phone")
        if phone:
            if phone in phone_first:
                uf.union(phone_first[phone], i)
            else:
                phone_first[phone] = i

    # Seed groups: row indices sharing a domain or phone, post phase 1.
    seed_groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        seed_groups[uf.find(i)].append(i)

    identities = {root: _group_identity(rows, idxs) for root, idxs in seed_groups.items()}

    # Which glued names appear in each seed group.
    roots_by_name: dict[str, set[int]] = defaultdict(set)
    for root, idxs in seed_groups.items():
        for i in idxs:
            name = _glued_name(rows[i])
            if name:
                roots_by_name[name].add(root)

    # Candidate weak edges: seed-group pairs sharing a glued name that don't
    # directly conflict with each other.
    neighbors: dict[int, set[int]] = defaultdict(set)
    for roots in roots_by_name.values():
        ordered = sorted(roots)
        for x in range(len(ordered)):
            for y in range(x + 1, len(ordered)):
                ra, rb = ordered[x], ordered[y]
                if _identity_conflicts(identities[ra], identities[rb]):
                    continue
                neighbors[ra].add(rb)
                neighbors[rb].add(ra)

    # RULING C23: a group whose own weak-linked neighbors conflict with each
    # other is an ambiguous hub -- none of ITS weak edges may fire, for
    # either side of any of them.
    ambiguous_hub: set[int] = set()
    for root, nbrs in neighbors.items():
        ordered = sorted(nbrs)
        for x in range(len(ordered)):
            if root in ambiguous_hub:
                break
            for y in range(x + 1, len(ordered)):
                if _identity_conflicts(identities[ordered[x]], identities[ordered[y]]):
                    ambiguous_hub.add(root)
                    break

    for root, nbrs in neighbors.items():
        if root in ambiguous_hub:
            continue
        for other in nbrs:
            if other in ambiguous_hub:
                continue
            uf.union(root, other)

    # Fold each final group's rows into one record. Sort by company_id (a
    # data field, independent of input position) before folding, so the
    # winning value for any field two rows both populate is deterministic
    # and does not depend on the order dedupe() was called with.
    final_groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        final_groups[uf.find(i)].append(i)

    out = []
    for idxs in final_groups.values():
        idxs = sorted(idxs, key=lambda i: rows[i].get("company_id") or "")
        merged = dict(rows[idxs[0]])
        for i in idxs[1:]:
            merged = merge_pair(merged, rows[i])
        out.append(merged)

    return out


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
