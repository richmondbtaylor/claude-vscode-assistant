from dedupe import dedupe, merge_pair

SBA = {"company_id": "a", "name": "Rivera Mechanical LLC", "domain": "riveramechanical.com",
       "website": None, "phone": None, "email": None, "email_status": "none",
       "address": "9 Elm St", "city": "Austin", "state": "TX", "zip": "78701",
       "naics": "238220", "category": "", "sources": ["sba_7a"],
       "signals": {"jobs_supported": 14, "loan_amount": 500000.0}}

MAPS = {"company_id": "b", "name": "Rivera Mechanical", "domain": "riveramechanical.com",
        "website": "https://riveramechanical.com", "phone": "+15125550111",
        "email": None, "email_status": "none", "address": "9 Elm St",
        "city": "Austin", "state": "TX", "zip": "78701", "naics": "",
        "category": "HVAC contractor", "sources": ["maps"],
        "signals": {"reviews": 212, "rating": 4.8}}

JOBS = {"company_id": "c", "name": "Riveramechanical", "domain": None, "website": None,
        "phone": None, "email": None, "email_status": "none", "address": "",
        "city": "", "state": "", "zip": "", "naics": "", "category": "",
        "sources": ["jobs"], "signals": {"open_finance_req": True, "job_url": "https://x/y"}}


def test_merge_unions_sources_and_signals():
    out = merge_pair(SBA, MAPS)
    assert sorted(out["sources"]) == ["maps", "sba_7a"]
    assert out["signals"]["jobs_supported"] == 14
    assert out["signals"]["reviews"] == 212


def test_merge_fills_empty_fields_without_overwriting():
    out = merge_pair(SBA, MAPS)
    assert out["phone"] == "+15125550111"
    assert out["naics"] == "238220"       # SBA value survives
    assert out["category"] == "HVAC contractor"  # Maps fills the blank


def test_dedupe_collapses_on_domain():
    out = dedupe([SBA, MAPS])
    assert len(out) == 1
    assert sorted(out[0]["sources"]) == ["maps", "sba_7a"]


def test_dedupe_collapses_on_phone_when_domain_missing():
    a = dict(SBA, domain=None, phone="+15125550111")
    out = dedupe([a, MAPS])
    assert len(out) == 1


def test_dedupe_collapses_on_name_and_state():
    a = dict(SBA, domain=None, phone=None)
    b = dict(MAPS, domain=None, phone=None)
    out = dedupe([a, b])
    assert len(out) == 1


def test_dedupe_keeps_same_name_in_different_states_apart():
    a = dict(SBA, domain=None, phone=None)
    b = dict(MAPS, domain=None, phone=None, state="FL")
    assert len(dedupe([a, b])) == 2


def test_dedupe_is_order_independent():
    assert len(dedupe([MAPS, SBA, JOBS])) == len(dedupe([JOBS, SBA, MAPS]))
