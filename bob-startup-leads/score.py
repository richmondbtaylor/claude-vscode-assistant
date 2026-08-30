"""Score every company 0-100 across four evidence families, then tier.

RULING C32: two data sources went dark during the build. `headcount` is
null for every company (the LinkedIn session stopped authenticating) and
`press_hits` is near zero for almost every company (the relevance filter
was tightened three times). Under the brief's fixed per-family weights,
both dark signals would silently cost every company points regardless of
how good the rest of their evidence is, dragging scores under SCORE_FLOOR
and shrinking the list for a reason that has nothing to do with company
quality.

Fix: each family (money, scale, signal) computes its fraction over only
the sub-signals the company actually has data for, then renormalizes to
the family's full 0.0-1.0 range. A sub-signal counts as present when its
key exists in `signals` AND its value is not None - a present zero/False/
empty-list is a real measurement (e.g. "we checked and found 0 reviews")
and must count as evidence, not be treated the same as "we never checked".
`reach` does not need this treatment: email/phone absence already scores
as a real, correctly-weighted zero without needing a family-wide average.

`MIN_FAMILIES` still guards companies with no evidence at all, but a
family now counts as "has evidence" the moment any one of its sub-signals
is present - independent of whether that evidence happens to score above
zero.
"""
import argparse

import config
from lib.records import read_jsonl, write_jsonl


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _present(sig: dict, key: str) -> bool:
    """A sub-signal counts as present when its key exists and is not None
    or an empty string. A present zero, False, or empty list is a real
    measurement, not an absence (RULING C32) - only a missing key, an
    explicit None, or a blank string means the data source never reported
    anything for this company. The blank-string exclusion (RULING C55)
    matters for row-level string fields like email/phone reused through
    this same function: none of money/scale/signal's sub-signals are ever
    a string, so it is a no-op for them and only changes reach."""
    return key in sig and sig[key] is not None and sig[key] != ""


def _weighted_fraction(parts: list[tuple[bool, float, float]]) -> float:
    """parts is a list of (present, value_fraction, weight) triples whose
    weights sum to 1.0 when everything is present. Renormalize over only
    the present parts so a family scores 0.0-1.0 on the evidence it
    actually has, rather than being diluted by sub-signals nobody
    collected. Returns 0.0 when nothing in the family is present."""
    present_parts = [(value, weight) for present, value, weight in parts if present]
    total_weight = sum(weight for _, weight in present_parts)
    if total_weight == 0:
        return 0.0
    return sum(value * weight for value, weight in present_parts) / total_weight


def family_scores(row: dict) -> dict[str, float]:
    """Each family returns a 0.0 to 1.0 fraction of its available evidence."""
    # RULING C54: row.get("signals", {}) only substitutes the default when
    # the key is absent; a key present with an explicit None (as every
    # signals-null row round-trips through JSON) makes this return None,
    # and every sig.get(...) call below then raises AttributeError,
    # aborting the whole scoring run on one bad row instead of failing it.
    sig = row.get("signals") or {}

    # Money proof: loan evidence, payment stack, a real pricing surface.
    money = _weighted_fraction([
        (_present(sig, "loan_amount"),
         _clamp((sig.get("loan_amount") or 0) / 1_000_000), 0.5),
        (_present(sig, "tech"),
         _clamp(len(sig.get("tech") or []) / 3), 0.35),
        (_present(sig, "has_pricing_page"),
         1.0 if sig.get("has_pricing_page") else 0.0, 0.15),
    ])

    # Operating scale: headcount, payroll size, footprint. `headcount` is
    # dark for every company right now (RULING C32) - when absent this
    # family renormalizes over jobs_supported and reviews alone.
    scale = _weighted_fraction([
        (_present(sig, "headcount"),
         _clamp((sig.get("headcount") or 0) / 200), 0.4),
        (_present(sig, "jobs_supported"),
         _clamp((sig.get("jobs_supported") or 0) / 50), 0.4),
        (_present(sig, "reviews"),
         _clamp((sig.get("reviews") or 0) / 400), 0.2),
    ])

    # Buying signal: an open finance req is the strongest single trigger.
    # `press_hits` is near-zero across the board (RULING C32) - when
    # absent this family renormalizes over open_finance_req and
    # marketplaces alone.
    signal = _weighted_fraction([
        (_present(sig, "open_finance_req"),
         1.0 if sig.get("open_finance_req") else 0.0, 0.5),
        (_present(sig, "press_hits"),
         _clamp((sig.get("press_hits") or 0) / 8), 0.25),
        (_present(sig, "marketplaces"),
         _clamp(len(sig.get("marketplaces") or []) / 2), 0.25),
    ])

    # Reachability: a named verified contact beats a generic inbox. Email
    # and phone absence already scores as a correctly-weighted real zero
    # here, so this family does not need the renormalization treatment.
    reach = 0.0
    if row.get("email_status") == "verified":
        reach += 0.6
    elif row.get("email_status") in ("personal", "guessed"):
        reach += 0.4
    elif row.get("email"):
        reach += 0.2
    if row.get("phone"):
        reach += 0.4

    return {"money": _clamp(money), "scale": _clamp(scale),
            "signal": _clamp(signal), "reach": _clamp(reach)}


def total_score(row: dict) -> int:
    fams = family_scores(row)
    return round(sum(fams[name] * config.WEIGHTS[name] for name in config.WEIGHTS))


def _families_with_evidence(row: dict) -> int:
    """Count families with at least one present sub-signal, independent of
    whether that evidence happens to score above zero (RULING C32) - a
    family that is genuinely all-zero still counts, only a family nobody
    ever measured does not."""
    sig = row.get("signals") or {}  # RULING C54: see family_scores above.
    money = (_present(sig, "loan_amount") or _present(sig, "tech")
             or _present(sig, "has_pricing_page"))
    scale = (_present(sig, "headcount") or _present(sig, "jobs_supported")
             or _present(sig, "reviews"))
    signal = (_present(sig, "open_finance_req") or _present(sig, "press_hits")
              or _present(sig, "marketplaces"))
    # RULING C55: reach must use the same presence test as every other
    # family (_present), not its own `is not None` check. An empty string
    # is not None, so the old test counted a blank email/phone as present
    # evidence -- a free family on every row that has never actually been
    # contacted -- which let MIN_FAMILIES=2 behave as if it were 1.
    reach = _present(row, "email") or _present(row, "phone")
    return sum([money, scale, signal, reach])


def assign_tiers(rows: list[dict]) -> list[dict]:
    """Score, reject below the floor, then mark the top fraction as tier1."""
    scored = []
    for row in rows:
        out = dict(row)
        out["score"] = total_score(row)
        families = _families_with_evidence(row)
        if families < config.MIN_FAMILIES:
            out["tier"] = "reject"
            out["reject_reason"] = f"only {families} evidence families"
        elif out["score"] < config.SCORE_FLOOR:
            out["tier"] = "reject"
            out["reject_reason"] = f"score {out['score']} below floor {config.SCORE_FLOOR}"
        else:
            out["tier"] = "master"
            out["reject_reason"] = ""
        scored.append(out)

    # Tier 1 is drawn only from rows that can actually be contacted. Scoring
    # rewards loan evidence heavily, so SBA-sourced rows dominate the top of
    # the ranking while carrying no phone, email or domain until the domain
    # resolution stage has run. Tiering over every keeper therefore filled the
    # deep-enrichment tier with companies the QA gate then rejected as
    # unreachable, and Tier 1 came out empty. An unreachable company cannot be
    # enriched or contacted, so it has no business consuming a Tier 1 slot.
    keepers = sorted(
        [r for r in scored
         if r["tier"] == "master" and (_present(r, "phone") or _present(r, "email"))],
        key=lambda r: r["score"], reverse=True)
    cutoff = int(len(keepers) * config.TIER1_FRACTION)
    for row in keepers[:cutoff]:
        row["tier"] = "tier1"
    return scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="signals.jsonl")
    args = ap.parse_args()

    rows = assign_tiers(list(read_jsonl(config.DATA / args.infile)))
    counts = {}
    for row in rows:
        counts[row["tier"]] = counts.get(row["tier"], 0) + 1
    print(counts)
    write_jsonl(config.DATA / "scored.jsonl", rows)


if __name__ == "__main__":
    main()
