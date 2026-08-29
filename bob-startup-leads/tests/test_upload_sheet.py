import json

import pytest

import config
from upload_sheet import MASTER_HEADERS, TIER1_HEADERS, _compute_meta, build_tabs, main

MASTER_ROW = {"name": "Rivera Mechanical", "domain": "rivera.com", "city": "Austin",
              "state": "TX", "phone": "+15125550111", "email": "info@rivera.com",
              "email_status": "generic", "category": "HVAC", "score": 62,
              "tier": "master", "sources": ["maps", "sba_7a"],
              "signals": {"reviews": 212, "jobs_supported": 14}}
TIER1_ROW = dict(MASTER_ROW, name="Summit Roofing", tier="tier1",
                 contact_name="Maria Gonzalez", contact_title="Owner",
                 contact_email="maria@summit.com", contact_email_status="verified",
                 hook="Summit Roofing is hiring a bookkeeper.")
REJECT_ROW = dict(MASTER_ROW, name="Tiny Shop", tier="reject",
                  reject_reason="score 12 below floor 35")

META = {"run_date": "2026-08-26", "apify_spend": 0.0, "hunter_used": 40,
        "sources": {"sba_7a": 200, "maps": 900, "jobs": 120}}


def test_master_tab_has_header_and_both_kept_tiers():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert tabs["Master"][0] == MASTER_HEADERS
    assert len(tabs["Master"]) == 3  # header plus master plus tier1


def test_tier1_tab_only_contains_tier1_rows():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert tabs["Tier 1 Deep"][0] == TIER1_HEADERS
    assert len(tabs["Tier 1 Deep"]) == 2
    assert tabs["Tier 1 Deep"][1][0] == "Summit Roofing"


def test_rejects_tab_carries_the_reason():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert any("below floor" in str(cell) for cell in tabs["Rejects"][1])


def test_method_tab_records_spend_and_source_counts():
    tabs = build_tabs([MASTER_ROW], META)
    flat = " ".join(str(c) for row in tabs["Method and Sources"] for c in row)
    assert "2026-08-26" in flat
    assert "sba_7a" in flat


def test_every_cell_is_a_primitive():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    for rows in tabs.values():
        for row in rows:
            for cell in row:
                assert isinstance(cell, (str, int, float)), f"{cell!r} is not a primitive"


def test_master_sorted_by_score_descending():
    low = dict(MASTER_ROW, name="Low", score=40)
    high = dict(MASTER_ROW, name="High", score=90)
    tabs = build_tabs([low, high], META)
    assert tabs["Master"][1][0] == "High"


# RULING C47: the Sheet discloses its own limitations, so a reader never
# has to guess why a column or a whole tab is blank.
def test_method_tab_discloses_known_limitations():
    tabs = build_tabs([MASTER_ROW], META)
    flat = " ".join(str(c) for row in tabs["Method and Sources"] for c in row)
    assert "Hunter API key" in flat
    assert "LinkedIn" in flat
    assert "Press hits" in flat
    assert "Hooks are written only" in flat


def test_tier1_tab_empty_gets_an_explanatory_note_not_a_bare_header():
    tabs = build_tabs([MASTER_ROW, REJECT_ROW], META)
    assert tabs["Tier 1 Deep"][0] == TIER1_HEADERS
    assert len(tabs["Tier 1 Deep"]) == 2
    note = tabs["Tier 1 Deep"][1][0]
    assert isinstance(note, str) and len(note) > 0
    assert "no tier1 rows" in note.lower()


def test_tier1_empty_note_names_the_real_demotion_reason():
    demoted = dict(MASTER_ROW, tier="master", demoted_from_tier1="no contact name")
    tabs = build_tabs([demoted], META)
    note = tabs["Tier 1 Deep"][1][0]
    assert "no contact name" in note


# RULING C48: the QA guard is the reason the QA stage exists, so both
# branches that block an upload are exercised directly.
def test_main_blocks_when_qa_report_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    with pytest.raises(SystemExit):
        main()


def test_main_blocks_when_qa_report_has_failed_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    (tmp_path / "qa_report.json").write_text(
        json.dumps({"passed": 0, "failed": 2}), encoding="utf-8")
    with pytest.raises(SystemExit):
        main()


# RULING C49: a figure on the Method tab must correspond to something
# that actually happened. The Apify step never issues a real HTTP call,
# so the stub marker must never be read as real spend.
def test_compute_meta_apify_stub_marker_never_counts_as_spend(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    (tmp_path / "companies.jsonl").write_text("", encoding="utf-8")
    row = dict(MASTER_ROW, enrich_errors=["apify: stub only, not wired"])
    meta = _compute_meta([row])
    assert meta["apify_spend"] == 0.0


# A "hunter: RuntimeError" entry proves _key() raised before httpx.get()
# ever ran (enrich_tier1.py hunter_domain_search), so it proves a call
# was blocked, not made, and must not be counted as one.
def test_compute_meta_hunter_missing_key_error_is_not_counted_as_a_call(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(config, "DATA", tmp_path)
    (tmp_path / "companies.jsonl").write_text("", encoding="utf-8")
    row = dict(MASTER_ROW, enrich_errors=["hunter: RuntimeError"])
    meta = _compute_meta([row])
    assert meta["hunter_used"] == 0
    assert meta["hunter_key_missing"] is True


# Any other "hunter:"-prefixed reason can only exist after httpx.get()
# actually ran, which is proof of a real call. The counting path that
# remains must still count that real call.
def test_compute_meta_hunter_real_failure_after_a_live_call_is_counted(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(config, "DATA", tmp_path)
    (tmp_path / "companies.jsonl").write_text("", encoding="utf-8")
    row = dict(MASTER_ROW, enrich_errors=["hunter: http 429"])
    meta = _compute_meta([row])
    assert meta["hunter_used"] == 1
    assert meta["hunter_key_missing"] is False


def test_method_tab_shows_no_hunter_key_text_instead_of_a_bare_zero():
    meta = dict(META, hunter_used=0, hunter_key_missing=True)
    tabs = build_tabs([MASTER_ROW], meta)
    flat = " ".join(str(c) for row in tabs["Method and Sources"] for c in row)
    assert "No Hunter API key configured" in flat


def test_method_tab_still_shows_a_real_count_when_calls_were_made():
    meta = dict(META, hunter_used=3, hunter_key_missing=False)
    tabs = build_tabs([MASTER_ROW], meta)
    row = next(r for r in tabs["Method and Sources"] if r[0] == "Hunter requests used")
    assert row[1] == 3


def test_method_tab_discloses_apify_is_not_wired():
    tabs = build_tabs([MASTER_ROW], META)
    flat = " ".join(str(c) for row in tabs["Method and Sources"] for c in row)
    assert "Apify" in flat
    assert "not wired" in flat
