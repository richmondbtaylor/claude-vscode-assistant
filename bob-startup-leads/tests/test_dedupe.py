import random

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


# --- RULING C20: conflicting strong identifiers veto a weak-key merge -----

# Real records pulled from data/seed_maps.jsonl (rows 4 and 35 of the actual
# 2026-08-26 scrape run) — this is the exact false-positive merge that
# surfaced when dedupe.py was run against real data. Two distinct Tampa
# roofing companies, same normalized name and state, different domain,
# phone, and address.
TAMPA_ROOF_A = {
    "company_id": "0dcefe2cff69b87d", "name": "Tampa Roof Repair LLC",
    "domain": "tamparoofrepair.com", "website": "http://www.tamparoofrepair.com/",
    "phone": "+18134135115", "email": None, "email_status": "none",
    "address": "13403 Arbor Pointe Cir, Tampa, FL 33617", "city": "Tampa",
    "state": "FL", "zip": "33617", "naics": "", "category": "Roofing contractor",
    "sources": ["maps"],
    "signals": {"reviews": 179, "rating": 4.9, "maps_query": "roofing contractor",
                "maps_city": "Tampa FL", "needs_liveness_check": False},
}
TAMPA_ROOF_B = {
    "company_id": "8b65396535a8a68f", "name": "Tampa Roof Repair, Inc.",
    "domain": "roofdocinc.com", "website": "https://roofdocinc.com/",
    "phone": "+18138020112", "email": None, "email_status": "none",
    "address": "5700 Memorial Hwy Ste 122, Tampa, FL 33615", "city": "Tampa",
    "state": "FL", "zip": "33615", "naics": "", "category": "Roofing contractor",
    "sources": ["maps"],
    "signals": {"reviews": 44, "rating": 4.6, "maps_query": "roofing contractor",
                "maps_city": "Tampa FL", "needs_liveness_check": False},
}


def test_dedupe_vetoes_name_state_match_on_conflicting_domains():
    out = dedupe([TAMPA_ROOF_A, TAMPA_ROOF_B])
    assert len(out) == 2
    domains = sorted(r["domain"] for r in out)
    assert domains == ["roofdocinc.com", "tamparoofrepair.com"]


def test_dedupe_vetoes_name_state_match_on_conflicting_phones_no_domain():
    a = dict(TAMPA_ROOF_A, domain=None, phone="+18134135115")
    b = dict(TAMPA_ROOF_B, domain=None, phone="+18138020112")
    out = dedupe([a, b])
    assert len(out) == 2


def test_dedupe_merges_name_state_when_only_one_side_has_domain():
    a = dict(TAMPA_ROOF_A)
    b = dict(TAMPA_ROOF_B, domain=None, phone=None)
    out = dedupe([a, b])
    assert len(out) == 1
    assert out[0]["domain"] == "tamparoofrepair.com"


def test_dedupe_shared_domain_still_merges_despite_differing_phone():
    a = dict(SBA, domain="riveramechanical.com", phone="+15125550111")
    b = dict(MAPS, domain="riveramechanical.com", phone="+15125559999")
    out = dedupe([a, b])
    assert len(out) == 1
    assert sorted(out[0]["sources"]) == ["maps", "sba_7a"]


# --- RULING C21: state-less rows and glued names widen the weak key ------

def test_dedupe_job_lane_merges_with_sba_lane_same_company():
    sba = dict(SBA, domain=None, phone=None)  # SBA lane never has domain/phone
    out = dedupe([JOBS, sba])
    assert len(out) == 1
    assert sorted(out[0]["sources"]) == ["jobs", "sba_7a"]


def test_dedupe_job_lane_does_not_merge_different_company_same_state():
    other = dict(SBA, domain=None, phone=None, name="Acme Plumbing LLC", state="TX")
    out = dedupe([JOBS, other])
    assert len(out) == 2


def test_dedupe_transitive_veto_does_not_bridge_through_shared_weak_key():
    a = {"company_id": "a1", "name": "Foo Bar Plumbing", "domain": "foo.com",
         "website": None, "phone": None, "email": None, "email_status": "none",
         "address": "", "city": "", "state": "TX", "zip": "", "naics": "",
         "category": "", "sources": ["maps"], "signals": {}}
    c = {"company_id": "c1", "name": "Foo Bar Plumbing", "domain": "bar.com",
         "website": None, "phone": None, "email": None, "email_status": "none",
         "address": "", "city": "", "state": "TX", "zip": "", "naics": "",
         "category": "", "sources": ["maps"], "signals": {}}
    b = {"company_id": "b1", "name": "Foo Bar Plumbing", "domain": None,
         "website": None, "phone": None, "email": None, "email_status": "none",
         "address": "", "city": "", "state": "TX", "zip": "", "naics": "",
         "category": "", "sources": ["jobs"], "signals": {}}

    for ordering in ([a, b, c], [b, a, c], [c, b, a], [a, c, b]):
        out = dedupe(ordering)
        # a and c must never land in the same output record, in any order.
        assert len(out) == 2
        rec_with_foo = next(r for r in out if r.get("domain") == "foo.com")
        rec_with_bar = next(r for r in out if r.get("domain") == "bar.com")
        assert rec_with_foo is not rec_with_bar
        # b (the bridge, source "jobs") joined exactly one of them rather
        # than creating a third record of its own.
        total_sources = sorted(s for r in out for s in r["sources"])
        assert total_sources == ["jobs", "maps", "maps"]


def test_dedupe_is_order_independent_compares_records_not_just_count():
    # Engineered so no field has an ambiguous winner: within each company,
    # domain/phone appear on at most one contributing row and every row's
    # name string is identical, so the grouping (which is what order
    # independence actually guarantees) fully determines the output.
    acme_sba = {"company_id": "s1", "name": "Acme Plumbing LLC", "domain": None,
                "website": None, "phone": None, "email": None, "email_status": "none",
                "address": "1 Main St", "city": "Austin", "state": "TX", "zip": "78701",
                "naics": "238220", "category": "", "sources": ["sba_7a"],
                "signals": {"jobs_supported": 9}}
    acme_maps = {"company_id": "m1", "name": "Acme Plumbing LLC", "domain": "acmeplumbing.com",
                 "website": "https://acmeplumbing.com", "phone": "+15125550100",
                 "email": None, "email_status": "none", "address": "1 Main St",
                 "city": "Austin", "state": "TX", "zip": "78701", "naics": "",
                 "category": "Plumber", "sources": ["maps"], "signals": {"reviews": 50}}
    acme_jobs = {"company_id": "j1", "name": "acmeplumbing", "domain": None,
                 "website": None, "phone": None, "email": None, "email_status": "none",
                 "address": "", "city": "", "state": "", "zip": "", "naics": "",
                 "category": "", "sources": ["jobs"], "signals": {"open_finance_req": True}}

    rows = [acme_sba, acme_maps, acme_jobs, TAMPA_ROOF_A, TAMPA_ROOF_B]

    def fingerprint(out):
        return sorted(
            (r["domain"], r["phone"], r["state"], tuple(sorted(r["sources"])))
            for r in out
        )

    baseline = dedupe(rows)
    assert len(baseline) == 3  # acme trio merged, the two Tampa roofers stay apart

    rng = random.Random(42)
    for _ in range(5):
        shuffled = rows[:]
        rng.shuffle(shuffled)
        out = dedupe(shuffled)
        assert len(out) == len(baseline)
        assert fingerprint(out) == fingerprint(baseline)
