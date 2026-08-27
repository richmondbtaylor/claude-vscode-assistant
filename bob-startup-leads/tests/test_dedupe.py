from itertools import permutations

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


# --- RULING C20 / C22: conflicting strong identifiers veto a weak-key merge

# Real records pulled from data/seed_maps.jsonl (rows 4 and 35 of the actual
# 2026-08-26 scrape run). This is the exact false-positive merge that
# surfaced when dedupe.py was run against real data: two distinct Tampa
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


def test_dedupe_does_not_bridge_differently_stated_companies_through_state_less_row():
    # RULING C22 regression: the fold loop must veto on STATE too, not just
    # domain/phone, or a state-less bridge row silently merges two distinct
    # companies in different states. Neither TX_CO nor CA_CO carries a
    # domain or phone, so before C22 nothing stopped the bridge.
    tx_co = {"company_id": "tx1", "name": "Foo Bar Plumbing", "domain": None,
             "website": None, "phone": None, "email": None, "email_status": "none",
             "address": "", "city": "", "state": "TX", "zip": "", "naics": "",
             "category": "", "sources": ["maps"], "signals": {}}
    ca_co = {"company_id": "ca1", "name": "Foo Bar Plumbing", "domain": None,
             "website": None, "phone": None, "email": None, "email_status": "none",
             "address": "", "city": "", "state": "CA", "zip": "", "naics": "",
             "category": "", "sources": ["maps"], "signals": {}}
    bridge = {"company_id": "br1", "name": "Foo Bar Plumbing", "domain": None,
              "website": None, "phone": None, "email": None, "email_status": "none",
              "address": "", "city": "", "state": "", "zip": "", "naics": "",
              "category": "", "sources": ["jobs"], "signals": {}}

    for ordering in permutations([tx_co, ca_co, bridge]):
        out = dedupe(list(ordering))
        assert len(out) == 3
        assert sorted(r["state"] for r in out) == ["", "CA", "TX"]


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


# --- RULING C23: an ambiguous weak-key bridge merges with nothing --------

def test_dedupe_transitive_veto_does_not_bridge_through_shared_weak_key():
    # A and C share a name+state with each other and each independently
    # with B, but A and C conflict on domain with each other. Per C23, B
    # (the bridge) must join NEITHER: all three stay separate records, in
    # every one of the six possible input orderings.
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

    for ordering in permutations([a, b, c]):
        out = dedupe(list(ordering))
        assert len(out) == 3
        by_domain = {r.get("domain"): r for r in out}
        assert set(by_domain) == {"foo.com", "bar.com", None}
        # Full grouping check: each record's sources must still be exactly
        # what it started with, proving B did not get absorbed by either A
        # or C in any ordering (not just that A and C stayed apart).
        assert by_domain["foo.com"]["sources"] == ["maps"]
        assert by_domain["bar.com"]["sources"] == ["maps"]
        assert by_domain[None]["sources"] == ["jobs"]


# --- RULING C24: email_status travels with email --------------------------

def test_merge_email_status_travels_with_filled_email():
    a = dict(SBA, email=None, email_status="none")
    b = dict(MAPS, email="info@riveramechanical.com", email_status="verified")
    out = merge_pair(a, b)
    assert out["email"] == "info@riveramechanical.com"
    assert out["email_status"] == "verified"


def test_merge_email_status_not_disturbed_when_email_already_populated():
    # a already has a verified email; b offers a different, unverified one.
    # Neither the email nor its status should move.
    a = dict(SBA, email="verified@riveramechanical.com", email_status="verified")
    b = dict(MAPS, email="guessed@riveramechanical.com", email_status="guessed")
    out = merge_pair(a, b)
    assert out["email"] == "verified@riveramechanical.com"
    assert out["email_status"] == "verified"


# --- Order independence, strengthened -------------------------------------

def test_dedupe_is_order_independent_across_all_permutations():
    # Engineered so grouping fully determines the output: within each
    # company, domain/phone appear on at most one contributing row and
    # every row's name string for that company is identical, so there is
    # no field where two contributing rows disagree on a populated value.
    # dedupe() folds a group's rows in company_id order (not input order),
    # so the result should be byte-for-byte identical across every
    # possible ordering of the input list, not just permutation-blind on a
    # coarse fingerprint.
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

    def canonical(out):
        return sorted(out, key=lambda r: r.get("company_id") or "")

    baseline = canonical(dedupe(rows))
    assert len(baseline) == 3  # acme trio merged, the two Tampa roofers stay apart

    for perm in permutations(rows):
        out = canonical(dedupe(list(perm)))
        assert out == baseline
