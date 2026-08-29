import json
from unittest.mock import MagicMock

import pytest

import config
import qa
import upload_sheet
from lib.records import write_jsonl
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


# RULING C54: build_tabs (via _signal_summary) must survive a row whose
# "signals" key is present but explicitly null, not just absent.
# row.get("signals", {}) only substitutes the default when the key is
# missing entirely; a present-null value returns None, and the very next
# sig.get(...) call raises AttributeError, aborting the whole Sheet build
# on one bad row.
def test_build_tabs_survives_a_present_but_null_signals_key():
    row = dict(MASTER_ROW, signals=None)
    tabs = build_tabs([row], META)
    assert tabs["Master"][1][0] == "Rivera Mechanical"


# RULING C50: a contactability rejection must reach the Rejects tab, not
# just stop counting as a hard failure. qa.run_gates() mutates a rejected
# row's tier to "reject" in place; this proves the same list handed to
# build_tabs afterward (the real upload_sheet.main() flow: keepers is
# passed to qa.run_gates() then to build_tabs()) routes that row into
# Rejects with a reason, and out of Master, without any separate read path.
def test_run_gates_rejected_row_flows_into_the_rejects_tab():
    contactless = dict(MASTER_ROW, name="No Contact Co", phone=None, email=None)
    keepers = [contactless]

    report = qa.run_gates(keepers)

    assert report["rejected"] == 1
    assert contactless["tier"] == "reject"

    tabs = build_tabs(keepers, META)

    master_names = [r[0] for r in tabs["Master"][1:]]
    assert "No Contact Co" not in master_names

    reject_rows = tabs["Rejects"][1:]
    assert any(r[0] == "No Contact Co" for r in reject_rows)
    reject_row = next(r for r in reject_rows if r[0] == "No Contact Co")
    assert "contactable" in reject_row[-1]


# --- Coordinator follow-up: does a qa-rejected row actually reach the
# Rejects tab through the REAL upload_sheet.main() flow, end to end, or
# does it get silently dropped from both keepers and rejects? The test
# above proves build_tabs() handles a pre-mutated row correctly; this one
# drives main() itself (with the Google API calls mocked out, since no
# network calls or real Sheets are allowed) to prove the same thing holds
# through the actual production code path, not just a hand-built list.

def _fake_sheets_and_drive():
    """A MagicMock sheets/drive pair shaped enough to survive main():
    spreadsheets().create() returns a spreadsheet id/url/sheet list,
    files().get() returns a parents list, everything else is an
    unconfigured MagicMock (main() never inspects those return values)."""
    sheets = MagicMock()
    drive = MagicMock()
    sheets.spreadsheets.return_value.create.return_value.execute.return_value = {
        "spreadsheetId": "sheet123",
        "spreadsheetUrl": "https://example.invalid/sheet123",
        "sheets": [{"properties": {"sheetId": i, "title": t}}
                   for i, t in enumerate(
                       ["Master", "Tier 1 Deep", "Method and Sources", "Rejects"])],
    }
    drive.files.return_value.get.return_value.execute.return_value = {"parents": ["folder1"]}
    return sheets, drive


def test_main_end_to_end_routes_a_contactless_master_row_to_rejects_tab(
        tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    (tmp_path / "qa_report.json").write_text(
        json.dumps({"passed": 1, "failed": 0, "rejected": 0}), encoding="utf-8")

    contactless = dict(MASTER_ROW, name="No Contact Co", phone=None, email=None)
    reachable = dict(MASTER_ROW, name="Rivera Mechanical")
    write_jsonl(tmp_path / "hooks.jsonl", [contactless, reachable])
    write_jsonl(tmp_path / "scored.jsonl", [])
    write_jsonl(tmp_path / "companies.jsonl", [])

    monkeypatch.setattr(upload_sheet, "_load_credentials", lambda: object())
    sheets, drive = _fake_sheets_and_drive()

    def fake_build_service(name, version, credentials=None):
        return sheets if name == "sheets" else drive
    monkeypatch.setattr("googleapiclient.discovery.build", fake_build_service)

    main()

    update_mock = sheets.spreadsheets.return_value.values.return_value.update
    # range is always built as f"'{name}'!A1" -- strip the fixed 1-char
    # leading quote and 4-char trailing "'!A1" wrapper to recover name.
    calls_by_tab = {c.kwargs["range"][1:-4]: c.kwargs["body"]["values"]
                    for c in update_mock.call_args_list}

    master_names = [r[0] for r in calls_by_tab["Master"][1:]]
    reject_names = [r[0] for r in calls_by_tab["Rejects"][1:]]

    # The contactless row must NOT silently vanish from both tabs -- it
    # must leave Master and land in Rejects with a reason, not disappear.
    assert "No Contact Co" not in master_names
    assert "No Contact Co" in reject_names
    assert "Rivera Mechanical" in master_names
    assert "Rivera Mechanical" not in reject_names

    reject_row = next(r for r in calls_by_tab["Rejects"][1:] if r[0] == "No Contact Co")
    assert "contactable" in reject_row[-1]
