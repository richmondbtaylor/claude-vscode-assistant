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


def test_dedupe_shared_domain_still_merges_despite_differing_states():
    # Structurally the state veto only ever gates the weak name+state key
    # (it is folded into _identity_conflicts, used only in Phase 2). Domain
    # equality is Phase 1, unconditional, and never consults state at all.
    # This proves it, rather than leaving it airtight-by-inspection only.
    a = dict(SBA, domain="riveramechanical.com", state="TX")
    b = dict(MAPS, domain="riveramechanical.com", state="FL")
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


# --- RULING C25: signals merge by an explicit per-key policy -------------

def test_merge_signals_takes_max_of_loan_amount_and_jobs_supported():
    a = dict(SBA, signals={"loan_amount": 200000.0, "jobs_supported": 5})
    b = dict(MAPS, signals={"loan_amount": 500000.0, "jobs_supported": 20})
    out = merge_pair(a, b)
    assert out["signals"]["loan_amount"] == 500000.0
    assert out["signals"]["jobs_supported"] == 20

    # The larger value wins regardless of which side is "a".
    out2 = merge_pair(b, a)
    assert out2["signals"]["loan_amount"] == 500000.0
    assert out2["signals"]["jobs_supported"] == 20


def test_merge_signals_present_value_beats_missing_key_both_orders():
    a = dict(SBA, signals={"loan_amount": 300000.0})
    b = dict(MAPS, signals={"reviews": 40})  # no loan_amount key at all

    out = merge_pair(a, b)
    assert out["signals"]["loan_amount"] == 300000.0
    assert out["signals"]["reviews"] == 40

    out2 = merge_pair(b, a)
    assert out2["signals"]["loan_amount"] == 300000.0
    assert out2["signals"]["reviews"] == 40


def test_merge_signals_open_finance_req_true_wins_when_absent_on_other_side():
    a = dict(SBA, signals={"open_finance_req": True})
    b = dict(MAPS, signals={"reviews": 10})  # no open_finance_req key at all

    out = merge_pair(a, b)
    assert out["signals"]["open_finance_req"] is True

    out2 = merge_pair(b, a)
    assert out2["signals"]["open_finance_req"] is True


def test_merge_signals_three_way_max_loan_amount_is_association_independent():
    r1 = dict(SBA, company_id="r1", signals={"loan_amount": 150000.0})
    r2 = dict(SBA, company_id="r2", signals={"loan_amount": 900000.0})
    r3 = dict(SBA, company_id="r3", signals={"loan_amount": 500000.0})

    left = merge_pair(merge_pair(r1, r2), r3)
    right = merge_pair(r1, merge_pair(r2, r3))
    middle = merge_pair(merge_pair(r1, r3), r2)

    for out in (left, right, middle):
        assert out["signals"]["loan_amount"] == 900000.0


def test_dedupe_three_way_merge_max_loan_amount_holds_across_permutations():
    # Same property, proven through the full dedupe() pipeline (which folds
    # in company_id order, not input order) rather than direct merge_pair
    # calls, across every possible input ordering.
    base = {"company_id": "z1", "name": "Acme Plumbing LLC", "domain": None,
            "website": None, "phone": None, "email": None, "email_status": "none",
            "address": "", "city": "", "state": "TX", "zip": "", "naics": "",
            "category": "", "sources": ["sba_7a"], "signals": {"loan_amount": 150000.0}}
    r1 = dict(base, company_id="z1", signals={"loan_amount": 150000.0})
    r2 = dict(base, company_id="z2", signals={"loan_amount": 900000.0})
    r3 = dict(base, company_id="z3", signals={"loan_amount": 500000.0})

    for perm in permutations([r1, r2, r3]):
        out = dedupe(list(perm))
        assert len(out) == 1
        assert out[0]["signals"]["loan_amount"] == 900000.0


def test_merge_signals_needs_liveness_check_false_wins_through_multi_way_merge():
    ppp_a = dict(SBA, sources=["ppp"], signals={"needs_liveness_check": True})
    ppp_b = dict(SBA, sources=["ppp"], signals={"needs_liveness_check": True})
    seven_a = dict(SBA, sources=["sba_7a"], signals={"needs_liveness_check": False})

    left = merge_pair(merge_pair(ppp_a, ppp_b), seven_a)
    right = merge_pair(ppp_a, merge_pair(ppp_b, seven_a))

    assert left["signals"]["needs_liveness_check"] is False
    assert right["signals"]["needs_liveness_check"] is False
