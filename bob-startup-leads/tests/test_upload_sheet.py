import pytest
from upload_sheet import MASTER_HEADERS, TIER1_HEADERS, build_tabs

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
