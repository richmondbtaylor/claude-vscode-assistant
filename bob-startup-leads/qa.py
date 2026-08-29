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

    Four hard gates only, per RULING C7:
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
    """
    problems = []

    phone = (row.get("phone") or "").strip()
    email = (row.get("email") or "").strip()
    if not phone and not (email and _looks_like_email(email)):
        problems.append("not contactable: no email and no phone")

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


def run_gates(rows: list[dict]) -> dict:
    """Gate every row, demoting under-enriched tier1 rows to master in
    place (RULING C7) rather than failing them. Rows are mutated: a
    demoted row gets tier set to "master" and a demoted_from_tier1 reason
    recorded on it, so any caller holding the same list sees the effect.
    """
    passed, failed = 0, 0
    by_reason: dict[str, int] = {}
    demoted = 0
    demoted_by_reason: dict[str, int] = {}

    for row in rows:
        problems = check_row(row)
        if problems:
            failed += 1
            for problem in problems:
                key = problem.split(":")[0]
                by_reason[key] = by_reason.get(key, 0) + 1
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
        "by_reason": by_reason,
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
