"""Gates that block the upload. Every rule here exists because it failed before."""
import json
import random

import config
from lib.normalize import is_valid_person_name
from lib.records import read_jsonl

SAMPLE_SEED = 20260826

# Fields a human reviewer needs to judge a sampled row. Beyond the obvious
# identity and contact fields, this carries what the hand sample exists to
# backstop:
#   - domain, address, city, state: the only way to catch a domain that
#     resolved at high similarity with no real location corroboration, or
#     a Sunbiz officer attributed to the wrong entity where corroboration
#     was unavailable.
#   - hook: so a reviewer can judge "accurate and lint-clean yet reads as
#     filler", which no automated gate checks.
#   - sources: which lane(s) the row came from, useful context for the
#     above two.
#   - demoted_from_tier1: visibility on RULING C7 demotions.
SAMPLE_FIELDS = (
    "company_id", "name", "domain", "website", "category", "address",
    "city", "state", "phone", "email", "email_status", "score", "tier",
    "contact_name", "contact_title", "contact_email", "contact_email_status",
    "hook", "demoted_from_tier1", "sources",
)


def _looks_like_email(s: str) -> bool:
    """Minimal structural check, not a full RFC validator: an at sign
    with something on both sides. RULING C46 point 2 -- contactability
    should not accept a malformed string just because it is non-empty."""
    local, sep, domain = s.partition("@")
    return bool(sep) and bool(local.strip()) and bool(domain.strip())


def check_row(row: dict) -> list[str]:
    """Return blocking violations for one row. Empty list means it can ship.

    Four gates, per RULING C7 / C50 / C56:
      1. contactability -- the one absolute requirement on a Master row.
      2. liveness -- a PPP-sourced row still flagged needs_liveness_check
         has not been confirmed as still trading.
      3. invalid contact name -- a name present but failing
         is_valid_person_name. A previous production run shipped junk like
         "Get Ah" and "Fort Lauderdale"; this gate exists because of that.
      4. verified without an address -- contact_email_status == "verified"
         with no contact_email. The "verified" label has to mean something.

    RULING C7: a tier1 row missing contact_name or hook is NOT a blocking
    violation here. Under-enrichment is now the expected case (no working
    Hunter key, dead LinkedIn session, hooks deliberately blank for
    non-financial signals), so failing on it would deadlock the entire
    deliverable on the first under-enriched row. That case is handled by
    demotion_reason() / run_gates() instead: the row ships as master.

    RULING C46: contactability is the one absolute requirement on a
    Master row, so it stands on its own rather than trusting an upstream
    invariant to hold forever. A whitespace-only phone or email counts as
    absent, and an email must have the minimal shape of an email (an at
    sign with something on both sides) to count as contactable. The same
    stripping applies to the verified-without-address gate. signals may
    be present and explicitly null rather than merely absent; a bad row
    there must fail that one row, not raise and abort the whole run.

    RULING C50 / C56: this function still reports EVERY violation on a
    row, contactability and liveness included -- check_row's contract
    does not change. What changes is what run_gates() does with those two
    violations: see its docstring. A row is only ever demoted to master
    OR rejected, never both, and never silently.
    """
    problems = []

    phone = (row.get("phone") or "").strip()
    email = (row.get("email") or "").strip()
    if not phone and not (email and _looks_like_email(email)):
        problems.append("not contactable: no email and no phone")

    # RULING C56: an unconfirmed liveness flag is a property of the ROW
    # (2020-2021 PPP data with no current evidence found), not proof the
    # pipeline misbehaved -- see run_gates() for how this is now handled.
    signals = row.get("signals") or {}
    if signals.get("needs_liveness_check"):
        problems.append("liveness not confirmed for a PPP-sourced row")

    name = row.get("contact_name") or ""
    if name and not is_valid_person_name(name):
        problems.append(f"invalid contact name: {name!r}")

    status = row.get("contact_email_status")
    contact_email = (row.get("contact_email") or "").strip()
    if status == "verified" and not contact_email:
        problems.append("email status is verified but no address is present")

    return problems


def demotion_reason(row: dict) -> str | None:
    """Why a tier1 row gets demoted to master, or None if it does not need
    to be. Only tier1 rows can be demoted; a master row has no tier above
    it to fall from, so a missing contact or hook there is just normal.

    RULING C7 (overrides the brief's check_row, which failed these rows
    outright): demote instead of fail.
    """
    if row.get("tier") != "tier1":
        return None
    missing = []
    if not row.get("contact_name"):
        missing.append("no contact name")
    if not row.get("hook"):
        missing.append("no hook")
    return "; ".join(missing) if missing else None


# RULING C50 / C56: a problem whose message starts with one of these
# prefixes is a property of the ROW (unfixable by the time it reaches
# this gate), not evidence the pipeline misbehaved, so it rejects rather
# than hard-fails. Contactability (C50): no phone or email exists to
# enrich further. Liveness (C56): a PPP row carries 2020-2021 data, and
# an unconfirmed flag means only that no CURRENT evidence was found --
# not that anything upstream is broken. Everything else check_row can
# report (an invalid contact name, "verified" with no address) still
# genuinely indicates upstream misbehaviour and keeps hard-failing.
_REJECTABLE_PREFIXES = ("not contactable", "liveness not confirmed")


def run_gates(rows: list[dict]) -> dict:
    """Gate every row. Rows are mutated in place, so any caller holding
    the same list sees every effect below.

    RULING C50: a contactability violation ("not contactable: ...") no
    longer counts as a hard failure. Contactability is a property of the
    ROW: by the time a row reaches this gate, no phone and no email
    exists to enrich further, so the row is unfixable, not defective.
    Spec section 11.1 already says what should happen to it: "Rows
    failing this move to Rejects with a reason." A contactability-only
    row is rejected here (tier="reject", reject_reason set) instead of
    counted under "failed", which is what let upload_sheet.py's
    `failed > 0` gate block the upload permanently with no way to clear
    it -- 260 of 555 real rows hit exactly this on the live data.

    RULING C56: an unconfirmed liveness flag joins contactability as a
    rejection, not a hard failure. The original C50/C7 framing called
    this "something wrong with the pipeline" -- that was wrong. A PPP
    row carries 2020-2021 data by construction; an unconfirmed flag
    means no CURRENT evidence of trading was found, which is a fact
    about the row (like contactability), not proof anything upstream
    misbehaved. site_scrape.py now gives standalone PPP rows an actual
    path to confirmation (a successful site fetch clears the flag, see
    site_scrape.scrape_row); a row that still carries the flag here
    genuinely could not be confirmed and rejects honestly instead of
    blocking the whole upload forever with no way to clear it.

    The remaining two gates (an invalid contact name, a "verified"
    status with no address) still hard-fail and are still counted under
    "failed". Each of those signals something wrong with the PIPELINE,
    not the row: upstream code produced a shape that should never exist
    (a name a filter should have caught, a verified label the waterfall
    never actually earned). Binning those silently into Rejects would
    hide the defect that produced them instead of surfacing it, so they
    keep blocking the run the way RULING C7 always intended for genuine
    defects.

    A row can carry both a hard-gate problem and a rejectable one; the
    hard-gate problem always takes priority, so a row that is both
    invalid-named and contactless still fails loudly rather than being
    quietly routed to Rejects. Demotion (RULING C7) is only ever
    considered once a row has neither kind of problem.

    Demoted rows get tier set to "master" and demoted_from_tier1
    recorded (unchanged from RULING C7). Rejected rows get tier set to
    "reject" and reject_reason recorded (every rejectable problem found,
    joined, in case a row is both contactless and liveness-unconfirmed),
    matching the shape score.py already uses, so upload_sheet.py's
    Rejects tab (which filters on tier=="reject") picks these up
    automatically alongside the rows scored.jsonl rejected earlier.
    """
    passed, failed, rejected = 0, 0, 0
    by_reason: dict[str, int] = {}
    rejected_by_reason: dict[str, int] = {}
    demoted = 0
    demoted_by_reason: dict[str, int] = {}

    for row in rows:
        problems = check_row(row)
        hard_problems = [p for p in problems if not p.startswith(_REJECTABLE_PREFIXES)]
        reject_problems = [p for p in problems if p.startswith(_REJECTABLE_PREFIXES)]

        if hard_problems:
            failed += 1
            for problem in hard_problems:
                key = problem.split(":")[0]
                by_reason[key] = by_reason.get(key, 0) + 1
            continue

        if reject_problems:
            reason = "; ".join(reject_problems)
            row["tier"] = "reject"
            row["reject_reason"] = reason
            rejected += 1
            for problem in reject_problems:
                key = problem.split(":")[0]
                rejected_by_reason[key] = rejected_by_reason.get(key, 0) + 1
            continue

        reason = demotion_reason(row)
        if reason:
            row["tier"] = "master"
            row["demoted_from_tier1"] = reason
            demoted += 1
            demoted_by_reason[reason] = demoted_by_reason.get(reason, 0) + 1

        passed += 1

    return {
        "passed": passed,
        "failed": failed,
        "rejected": rejected,
        "by_reason": by_reason,
        "rejected_by_reason": rejected_by_reason,
        "demoted": demoted,
        "demoted_by_reason": demoted_by_reason,
    }


def sample(rows: list[dict], n: int = 25) -> list[dict]:
    """Deterministic hand-review sample. Same seed every run, so the same
    25 rows come up for review no matter how many times this runs."""
    if len(rows) <= n:
        return list(rows)
    return random.Random(SAMPLE_SEED).sample(rows, n)


def main():
    rows = [r for r in read_jsonl(config.DATA / "hooks.jsonl")
            if r.get("tier") in ("master", "tier1")]
    report = run_gates(rows)
    report["total"] = len(rows)
    report["sample"] = [
        {**{k: r.get(k) for k in SAMPLE_FIELDS}, "violations": check_row(r)}
        for r in sample(rows, 25)
    ]
    (config.DATA / "qa_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "sample"}, indent=2))
    print("\nHand-review sample written to data/qa_report.json")


if __name__ == "__main__":
    main()
