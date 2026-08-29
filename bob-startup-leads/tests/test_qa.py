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


# RULING C46: contactability is the one absolute requirement on a Master
# row, so it must not depend on an upstream invariant (clean_emails,
# norm_phone) holding forever. It has to stand on its own as the backstop.
def test_whitespace_only_phone_and_email_fails_contactability():
    bad = dict(GOOD, phone="   ", email="   ")
    assert any("contactable" in v for v in check_row(bad))


def test_malformed_email_without_at_sign_fails_contactability():
    bad = dict(GOOD, phone=None, email="not-an-email")
    assert any("contactable" in v for v in check_row(bad))


def test_email_missing_local_or_domain_part_fails_contactability():
    assert any("contactable" in v for v in check_row(dict(GOOD, phone=None, email="@rivera.com")))
    assert any("contactable" in v for v in check_row(dict(GOOD, phone=None, email="info@")))


def test_whitespace_padded_valid_email_still_passes_contactability():
    ok = dict(GOOD, phone=None, email="  info@rivera.com  ")
    assert check_row(ok) == []


def test_verified_status_with_whitespace_only_contact_email_fails():
    bad = dict(GOOD_T1, contact_email_status="verified", contact_email="   ")
    assert any("email" in v for v in check_row(bad))


def test_null_signals_does_not_raise_and_row_is_not_flagged_for_liveness():
    row = dict(GOOD, signals=None)
    problems = check_row(row)
    assert not any("liveness" in v for v in problems)


# RULING C50: a contactability-only violation is now a rejection, not a
# hard failure -- this expectation was recomputed by hand against the new
# run_gates contract. See test_run_gates_rejects_contactless_row_instead_
# of_failing_it below for the dedicated C50 coverage.
def test_run_gates_counts_by_reason():
    out = run_gates([GOOD, dict(GOOD, phone=None, email=None)])
    assert out["passed"] == 1
    assert out["failed"] == 0
    assert out["rejected"] == 1
    assert out["rejected_by_reason"]


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


# RULING C50 recomputation: the original row here (missing contact_name,
# missing phone/email) only ever carried a contactability problem -- an
# empty contact_name is not itself a hard-gate violation (RULING C7), it
# just means demotion_reason() would have found "no contact name" to
# report. Under C50 that row is now REJECTED, not failed (see the
# dedicated test below), so this test is recomputed to use a row that
# still fails a genuine hard gate (an invalid, non-empty contact name)
# to preserve its original intent: demotion must never rescue a row that
# fails one of the two gates that still hard-fail (RULING C56 moved
# liveness from hard-fail to reject, alongside contactability; see below).
def test_run_gates_does_not_demote_a_row_that_still_fails_a_hard_gate():
    row = dict(GOOD_T1, contact_name="Get Ah")
    out = run_gates([row])
    assert out["failed"] == 1
    assert out["rejected"] == 0
    assert out["demoted"] == 0
    assert row["tier"] == "tier1"


# --- RULING C50 / C56: contactability and liveness reject instead of
# blocking ------------------------------------------------------------------
#
# qa.py:72 counted a contactless row as a hard failure and upload_sheet.py
# hard-exited while failed > 0, with nothing anywhere moving the row to
# Rejects. Spec 11.1 already requires the row move to Rejects with a
# reason instead. RULING C56 corrected the original C50/C7 framing of the
# liveness gate: an unconfirmed needs_liveness_check flag means only that
# no CURRENT evidence of trading was found for a PPP row carrying
# 2020-2021 data, which is a fact about the ROW, not proof the pipeline
# misbehaved -- exactly the same shape as contactability. Only the
# remaining two gates (invalid contact name, verified without an
# address) still hard-fail: each of those really does signal a pipeline
# defect, so they must keep surfacing rather than being silently binned.

def test_run_gates_rejects_contactless_row_instead_of_failing_it():
    contactless = dict(GOOD, phone=None, email=None)
    out = run_gates([contactless])
    assert out["failed"] == 0
    assert out["rejected"] == 1
    assert out["rejected_by_reason"]
    assert contactless["tier"] == "reject"
    assert "contactable" in contactless["reject_reason"]


def test_run_gates_still_hard_fails_invalid_contact_name_not_rejects_it():
    bad = dict(GOOD_T1, contact_name="Get Ah")
    out = run_gates([bad])
    assert out["failed"] == 1
    assert out["rejected"] == 0
    assert bad["tier"] == "tier1"  # unchanged: a hard failure is not rejected


def test_run_gates_still_hard_fails_verified_without_address_not_rejects_it():
    bad = dict(GOOD_T1, contact_email_status="verified", contact_email="")
    out = run_gates([bad])
    assert out["failed"] == 1
    assert out["rejected"] == 0
    assert bad["tier"] == "tier1"  # unchanged: a hard failure is not rejected


def test_run_gates_hard_gate_problem_takes_priority_over_contactability_rejection():
    # A row failing BOTH a hard gate and contactability must fail, not be
    # rejected -- the hard-gate defect has to surface, not get quietly
    # routed to Rejects alongside genuinely unfixable rows.
    row = dict(GOOD_T1, contact_name="Get Ah", phone=None, email=None)
    out = run_gates([row])
    assert out["failed"] == 1
    assert out["rejected"] == 0
    assert row["tier"] == "tier1"


# --- RULING C56: liveness rejects instead of failing -----------------------

def test_run_gates_rejects_unconfirmed_liveness_row_instead_of_failing_it():
    bad = dict(GOOD, signals={"needs_liveness_check": True})
    out = run_gates([bad])
    assert out["failed"] == 0
    assert out["rejected"] == 1
    assert out["rejected_by_reason"]
    assert bad["tier"] == "reject"
    assert "liveness" in bad["reject_reason"]


def test_run_gates_combines_contactability_and_liveness_reasons_on_one_row():
    # A row can be both contactless and liveness-unconfirmed at once --
    # both are rejectable, so both reasons must be recorded, not just one.
    both = dict(GOOD, phone=None, email=None, signals={"needs_liveness_check": True})
    out = run_gates([both])
    assert out["failed"] == 0
    assert out["rejected"] == 1
    assert "contactable" in both["reject_reason"]
    assert "liveness" in both["reject_reason"]


def test_run_gates_hard_gate_problem_takes_priority_over_liveness_rejection():
    # Same priority rule as contactability: a genuine hard-gate defect
    # must surface even on a row that is also liveness-unconfirmed.
    row = dict(GOOD_T1, contact_name="Get Ah", signals={"needs_liveness_check": True})
    out = run_gates([row])
    assert out["failed"] == 1
    assert out["rejected"] == 0
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
    # RULING C50: the report distinguishes rejected from failed from
    # demoted, so a reader (and upload_sheet.py's gate) never has to
    # infer one from another.
    for field in ("passed", "failed", "rejected", "by_reason",
                  "rejected_by_reason", "demoted", "demoted_by_reason",
                  "total", "sample"):
        assert field in report
    assert report["total"] == 2
    assert report["passed"] == 2
    assert report["failed"] == 0
    assert report["rejected"] == 0


# RULING C50 integration: a master row that reaches qa.py with no phone
# and no email must be REJECTED (not failed), so `uv run qa.py` never
# writes a qa_report.json with failed > 0 for a reason no one can fix.
def test_main_rejects_contactless_master_row_and_reports_zero_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    contactless = dict(GOOD, name="No Contact Co", phone=None, email=None)
    write_jsonl(tmp_path / "hooks.jsonl", [contactless])

    qa_module.main()

    report = json.loads((tmp_path / "qa_report.json").read_text(encoding="utf-8"))
    assert report["failed"] == 0
    assert report["rejected"] == 1


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
