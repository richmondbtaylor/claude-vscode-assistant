import json

import config
import qa as qa_module
from lib.records import write_jsonl
from qa import check_row, demotion_reason, run_gates, sample

GOOD = {"name": "Rivera Mechanical", "phone": "+15125550111", "email": "info@rivera.com",
        "email_status": "generic", "tier": "master", "contact_name": "",
        "signals": {"needs_liveness_check": False}}
GOOD_T1 = {"name": "Summit Roofing", "phone": "+13035550111",
           "email": "maria@summit.com", "email_status": "personal", "tier": "tier1",
           "contact_name": "Maria Gonzalez", "contact_email": "maria@summit.com",
           "contact_email_status": "verified", "hook": "Summit Roofing is hiring.",
           "signals": {"needs_liveness_check": False}}


def test_good_rows_pass():
    assert check_row(GOOD) == []
    assert check_row(GOOD_T1) == []


def test_row_without_email_or_phone_fails():
    bad = dict(GOOD, phone=None, email=None)
    assert any("contactable" in v for v in check_row(bad))


def test_junk_contact_name_fails():
    bad = dict(GOOD_T1, contact_name="Get Ah")
    assert any("name" in v for v in check_row(bad))


def test_unchecked_liveness_flag_fails():
    bad = dict(GOOD, signals={"needs_liveness_check": True})
    assert any("liveness" in v for v in check_row(bad))


def test_guessed_email_labelled_verified_fails():
    bad = dict(GOOD_T1, contact_email_status="verified", contact_email="")
    assert any("email" in v for v in check_row(bad))


def test_run_gates_counts_by_reason():
    out = run_gates([GOOD, dict(GOOD, phone=None, email=None)])
    assert out["passed"] == 1
    assert out["failed"] == 1
    assert out["by_reason"]


def test_sample_is_deterministic():
    rows = [dict(GOOD, name=f"co{i}") for i in range(100)]
    assert [r["name"] for r in sample(rows, 25)] == [r["name"] for r in sample(rows, 25)]


def test_sample_returns_all_when_fewer_than_n():
    rows = [dict(GOOD, name=f"co{i}") for i in range(5)]
    assert len(sample(rows, 25)) == 5


# RULING C7: a tier1 row missing contact_name or hook must not be a
# blocking violation. The waterfall cannot guarantee a contact for every
# row (no Hunter key, dead LinkedIn session) and hook_for() deliberately
# returns "" for a company with no financial signal, so under-enrichment is
# the normal case now, not the exception. Failing it would deadlock the
# whole deliverable on the first under-enriched row.
def test_tier1_missing_contact_name_is_not_a_blocking_violation():
    bad_t1 = dict(GOOD_T1, contact_name="")
    assert check_row(bad_t1) == []


def test_tier1_missing_hook_is_not_a_blocking_violation():
    bad_t1 = dict(GOOD_T1, hook="")
    assert check_row(bad_t1) == []


def test_tier1_missing_both_contact_name_and_hook_is_not_a_blocking_violation():
    bad_t1 = dict(GOOD_T1, contact_name="", hook="")
    assert check_row(bad_t1) == []


def test_tier1_missing_contact_name_is_demoted():
    reason = demotion_reason(dict(GOOD_T1, contact_name=""))
    assert reason is not None
    assert "name" in reason


def test_tier1_missing_hook_is_demoted():
    reason = demotion_reason(dict(GOOD_T1, hook=""))
    assert reason is not None
    assert "hook" in reason


def test_tier1_fully_enriched_is_not_demoted():
    assert demotion_reason(GOOD_T1) is None


def test_master_row_is_never_demoted_even_without_contact_or_hook():
    # demotion only applies to tier1 rows; a master row has no tier to
    # demote FROM, so a missing contact/hook there is simply normal.
    assert demotion_reason(GOOD) is None


def test_run_gates_demotes_under_enriched_tier1_row_to_master():
    row = dict(GOOD_T1, contact_name="")
    out = run_gates([row])
    assert out["passed"] == 1
    assert out["failed"] == 0
    assert out["demoted"] == 1
    assert out["demoted_by_reason"]
    assert row["tier"] == "master"
    assert "demoted_from_tier1" in row


def test_run_gates_does_not_demote_a_row_that_still_fails_a_hard_gate():
    # an under-enriched tier1 row that is ALSO not contactable is a real
    # failure, not a rescue -- demotion only covers the specific deadlock
    # C7 names, never the four hard gates.
    row = dict(GOOD_T1, contact_name="", phone=None, email=None)
    out = run_gates([row])
    assert out["failed"] == 1
    assert out["demoted"] == 0
    assert row["tier"] == "tier1"


def test_run_gates_reports_demoted_count_on_a_mixed_batch():
    rows = [GOOD, GOOD_T1, dict(GOOD_T1, name="Under Co", contact_name="")]
    out = run_gates(rows)
    assert out["passed"] == 3
    assert out["failed"] == 0
    assert out["demoted"] == 1


def test_main_writes_qa_report_with_contract_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    write_jsonl(tmp_path / "hooks.jsonl", [GOOD, GOOD_T1])

    qa_module.main()

    report = json.loads((tmp_path / "qa_report.json").read_text(encoding="utf-8"))
    for field in ("passed", "failed", "by_reason", "total", "sample"):
        assert field in report
    assert report["total"] == 2
    assert report["passed"] == 2
    assert report["failed"] == 0


# The hand-review sample is the backstop for defects no automated gate can
# catch: a domain resolved at high similarity with no location
# corroboration, a Sunbiz officer attributed to the wrong entity, or a hook
# that is accurate and lint-clean yet reads as filler. All three need
# location and identity fields on the sampled row, not just pass/fail.
def test_sample_includes_fields_needed_for_hand_review(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    row = dict(GOOD_T1, company_id="abc123", domain="summit.com",
               address="1 Main St", city="Denver", state="CO", sources=["maps"])
    write_jsonl(tmp_path / "hooks.jsonl", [row])

    qa_module.main()

    report = json.loads((tmp_path / "qa_report.json").read_text(encoding="utf-8"))
    sampled = report["sample"][0]
    for field in ("company_id", "domain", "city", "state", "hook",
                  "contact_name", "sources"):
        assert field in sampled


def test_main_excludes_reject_tier_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    reject_row = dict(GOOD, tier="reject")
    write_jsonl(tmp_path / "hooks.jsonl", [GOOD, reject_row])

    qa_module.main()

    report = json.loads((tmp_path / "qa_report.json").read_text(encoding="utf-8"))
    assert report["total"] == 1
