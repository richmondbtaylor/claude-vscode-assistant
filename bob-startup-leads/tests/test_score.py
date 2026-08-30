import config
from score import assign_tiers, family_scores, total_score

RICH = {"name": "Rivera Mechanical", "domain": "riveramechanical.com",
        "phone": "+15125550111", "email": "maria@riveramechanical.com",
        "email_status": "verified", "sources": ["sba_7a", "maps", "jobs"],
        "signals": {"jobs_supported": 40, "loan_amount": 900000.0,
                    "tech": ["stripe", "quickbooks"], "has_pricing_page": True,
                    "reviews": 300, "headcount": 120, "open_finance_req": True,
                    "press_hits": 6, "marketplaces": ["bbb", "g2"]}}

THIN = {"name": "Tiny Shop", "domain": None, "phone": "+15125550112",
        "email": None, "email_status": "none", "sources": ["maps"],
        "signals": {"reviews": 12}}


def test_weights_sum_to_100():
    assert sum(config.WEIGHTS.values()) == 100


def test_family_scores_are_fractions():
    for value in family_scores(RICH).values():
        assert 0.0 <= value <= 1.0


def test_rich_company_scores_high():
    # RULING C32 note: RICH carries every sub-signal (headcount and
    # press_hits included), so renormalization is a no-op here and the
    # brief's original expectation is unchanged. Hand arithmetic:
    #   money  = (0.9*0.5 + 0.6667*0.35 + 1*0.15) = 0.8333  -> 33.33 pts
    #   scale  = (0.6*0.4 + 0.8*0.4 + 0.75*0.2)   = 0.71    -> 17.75 pts
    #   signal = (0.5 + 0.75*0.25 + 1*0.25)       = 0.9375  -> 23.44 pts
    #   reach  = (0.6 verified + 0.4 phone)       = 1.0     -> 10.00 pts
    #   total  = 33.33 + 17.75 + 23.44 + 10.00    = 84.5 -> rounds to 85 (or 84)
    assert total_score(RICH) >= 75


def test_thin_company_scores_below_floor():
    assert total_score(THIN) < config.SCORE_FLOOR


def test_score_is_bounded_0_to_100():
    assert 0 <= total_score(THIN) <= 100
    assert 0 <= total_score(RICH) <= 100


def test_open_req_alone_still_needs_a_second_family():
    only_req = {"name": "X", "domain": None, "phone": None, "email": None,
                "email_status": "none", "sources": ["jobs"],
                "signals": {"open_finance_req": True}}
    out = assign_tiers([only_req])
    assert out[0]["tier"] == "reject"
    assert "families" in out[0]["reject_reason"]


def test_assign_tiers_marks_top_fraction_as_tier1():
    rows = []
    for i in range(100):
        row = dict(RICH, name=f"co{i}")
        row["signals"] = dict(RICH["signals"], jobs_supported=100 - i, reviews=300 - i)
        rows.append(row)
    out = assign_tiers(rows)
    tier1 = [r for r in out if r["tier"] == "tier1"]
    assert len(tier1) == int(100 * config.TIER1_FRACTION)
    assert all(r["score"] >= max(x["score"] for x in out if x["tier"] == "master")
               for r in tier1)


def test_rows_below_floor_are_rejected_with_a_reason():
    out = assign_tiers([THIN])
    assert out[0]["tier"] == "reject"
    assert out[0]["reject_reason"]


# --- RULING C32: renormalization and present-zero tests -------------------
#
# These are new (not in the brief) because C32 changes behavior the brief's
# fixed-weight test suite never exercises: a family with a dark sub-signal,
# and the difference between "never measured" and "measured as zero".

def test_scale_renormalizes_when_headcount_is_dark():
    # headcount present as None (exactly what real signals.jsonl rows look
    # like today): the scale family must renormalize over jobs_supported
    # and reviews alone rather than losing 40% of its ceiling to a signal
    # nobody could collect.
    # Hand arithmetic: jobs_supported clamp(40/50)=0.8 * weight 0.4 = 0.32
    #                  reviews        clamp(300/400)=0.75 * weight 0.2 = 0.15
    #                  renormalize over remaining weight 0.6:
    #                  (0.32 + 0.15) / 0.6 = 0.4700 / 0.6 = 0.78333...
    row = {"name": "Dark Headcount Co", "domain": "x.com", "phone": None,
           "email": None, "email_status": "none", "sources": ["sba_7a"],
           "signals": {"jobs_supported": 40, "reviews": 300, "headcount": None}}
    scale = family_scores(row)["scale"]
    assert abs(scale - (0.47 / 0.6)) < 1e-9


def test_family_with_zero_evidence_present_scores_zero_not_average():
    # If literally nothing in a family is present, the family must be 0.0
    # rather than raising or defaulting to some nonzero baseline.
    row = {"name": "No Money Signals", "domain": None, "phone": None,
           "email": None, "email_status": "none", "sources": ["maps"],
           "signals": {"reviews": 50}}
    assert family_scores(row)["money"] == 0.0


def test_present_zero_reviews_counts_as_a_scale_evidence_family():
    # A company genuinely measured at 0 reviews is different from a company
    # nobody ever checked. The zero must still count toward MIN_FAMILIES so
    # it is not rejected as if scale were unmeasured, per RULING C32.
    zero_reviews = {"name": "Zero Reviews Co", "domain": None,
                     "phone": "+15125550199", "email": None,
                     "email_status": "none", "sources": ["maps"],
                     "signals": {"reviews": 0}}
    out = assign_tiers([zero_reviews])[0]
    # Two evidence families (scale via the present zero, reach via phone) -
    # so it must NOT be rejected for lack of evidence families, even though
    # its score is low enough to be rejected for the floor instead.
    assert "families" not in out["reject_reason"]


def test_missing_reviews_key_does_not_count_as_scale_evidence():
    # Contrast case: reviews never reported at all (no key), only phone
    # present elsewhere - scale contributes no evidence family, unlike the
    # present-zero case above, so only 1 evidence family total and it must
    # be rejected specifically for lack of evidence families.
    no_scale_data = {"name": "No Scale Data Co", "domain": None,
                      "phone": "+15125550199", "email": None,
                      "email_status": "none", "sources": ["maps"],
                      "signals": {}}
    out = assign_tiers([no_scale_data])[0]
    assert out["tier"] == "reject"
    assert "families" in out["reject_reason"]


def test_maps_only_company_with_dark_signals_still_clears_the_floor():
    # The real-world case C32 exists for: a solid Maps-sourced lead with no
    # SBA loan record (no jobs_supported/loan_amount/open_finance_req) and
    # no headcount or press (both dark data sources), but strong reviews,
    # a tech fingerprint, a pricing page, and a marketplace listing. Under
    # the brief's fixed weights this would silently lose 40% of scale and
    # 25% of signal to sub-signals nobody could ever collect. Under C32 it
    # should renormalize and clear SCORE_FLOOR on the evidence it has.
    # Hand arithmetic:
    #   money  = (tech 2/3=0.6667*0.35 + pricing 1*0.15)/(0.35+0.15)
    #          = (0.2333+0.15)/0.5 = 0.7667
    #   scale  = reviews clamp(350/400)=0.875 (only sub-signal) = 0.875
    #   signal = marketplaces clamp(1/2)=0.5 (only sub-signal) = 0.5
    #   reach  = phone only = 0.4
    #   total  = 0.7667*40 + 0.875*25 + 0.5*25 + 0.4*10
    #          = 30.67 + 21.875 + 12.5 + 4.0 = 69.04 -> rounds to 69
    row = {"name": "Solid Maps Lead", "domain": "solidmapslead.com",
           "phone": "+15125550188", "email": None, "email_status": "none",
           "sources": ["maps"],
           "signals": {"reviews": 350, "tech": ["stripe", "quickbooks"],
                       "has_pricing_page": True, "marketplaces": ["bbb"]}}
    assert total_score(row) >= config.SCORE_FLOOR


# --- RULING C55: reach evidence must use the same presence test as every
# other family (_present), not a bespoke `is not None` check. An empty
# string is not None, so the old check counted a blank email as present
# reach evidence -- a free family on a row nobody has ever actually
# contacted -- which let MIN_FAMILIES=2 behave as if it were 1.

def test_blank_email_does_not_count_as_reach_evidence():
    from score import _families_with_evidence
    row = {"name": "Blank Email Co", "domain": None, "phone": None,
           "email": "", "email_status": "none", "sources": ["sba_7a"],
           "signals": {"loan_amount": 500000}}
    # Only "money" (loan_amount) is real evidence; reach must NOT count
    # the blank email string as a second family.
    assert _families_with_evidence(row) == 1


def test_blank_email_alone_is_rejected_for_lack_of_evidence_families():
    row = {"name": "Blank Email Only Co", "domain": None, "phone": None,
           "email": "", "email_status": "none", "sources": ["sba_7a"],
           "signals": {"loan_amount": 500000}}
    out = assign_tiers([row])[0]
    assert out["tier"] == "reject"
    assert "families" in out["reject_reason"]


def test_real_phone_still_counts_as_reach_evidence():
    # Sanity check: the C55 fix must not also exclude a genuine phone.
    from score import _families_with_evidence
    row = {"name": "Real Phone Co", "domain": None, "phone": "+15125550188",
           "email": None, "email_status": "none", "sources": ["maps"],
           "signals": {"loan_amount": 500000}}
    assert _families_with_evidence(row) == 2  # money + reach


# --- RULING C54: family_scores and _families_with_evidence must survive
# a row whose "signals" key is present but explicitly null, not just
# absent. row.get("signals", {}) only substitutes the default when the
# key is missing entirely; a present-null value makes it return None,
# and every sig.get(...) call after it then raises AttributeError.

def test_family_scores_survives_a_present_but_null_signals_key():
    row = {"name": "Null Signals Co", "domain": None, "phone": "+15125550188",
           "email": None, "email_status": "none", "sources": ["maps"],
           "signals": None}
    fams = family_scores(row)
    assert fams["money"] == 0.0
    assert fams["scale"] == 0.0
    assert fams["signal"] == 0.0


def test_assign_tiers_survives_a_present_but_null_signals_key():
    row = {"name": "Null Signals Co", "domain": None, "phone": "+15125550188",
           "email": None, "email_status": "none", "sources": ["maps"],
           "signals": None}
    out = assign_tiers([row])[0]
    assert out["tier"] == "reject"  # no evidence at all, but must not raise


def test_tier1_is_drawn_only_from_contactable_rows():
    """An unreachable company must never consume a Tier 1 slot.

    Scoring rewards loan evidence heavily, so SBA-sourced rows outscore
    everything while carrying no phone, email or domain. Tiering over every
    keeper filled Tier 1 with companies the QA gate then rejected, leaving the
    tab empty.
    """
    unreachable = {
        "name": "Loan Co", "phone": None, "email": None, "email_status": "none",
        "sources": ["sba_7a"],
        "signals": {"jobs_supported": 60, "loan_amount": 5_000_000.0,
                    "reviews": 400, "tech": ["stripe"], "has_pricing_page": True},
    }
    reachable = {
        "name": "Reachable Co", "phone": "+15125550111",
        "email": "info@reachable.com", "email_status": "generic",
        "sources": ["maps"],
        "signals": {"reviews": 120, "tech": ["stripe"]},
    }
    # Ten contactable rows so the 20 percent cutoff yields two Tier 1 slots,
    # against nine unreachable rows that each outscore every one of them.
    rows = [dict(unreachable, name=f"loan{i}") for i in range(9)]
    for i in range(10):
        row = dict(reachable, name=f"reach{i}")
        row["signals"] = dict(reachable["signals"], reviews=400 - i * 10)
        rows.append(row)
    out = assign_tiers(rows)

    tier1 = [r for r in out if r["tier"] == "tier1"]
    assert len(tier1) == 2
    assert all(r.get("phone") or r.get("email") for r in tier1)
    assert {r["name"] for r in tier1} == {"reach0", "reach1"}


def test_contactless_rows_still_reach_master_when_they_clear_the_floor():
    """Excluding them from Tier 1 must not reject them outright."""
    unreachable = {
        "name": "Loan Co", "phone": None, "email": None, "email_status": "none",
        "sources": ["sba_7a"],
        "signals": {"jobs_supported": 60, "loan_amount": 5_000_000.0,
                    "reviews": 400, "tech": ["stripe"], "has_pricing_page": True},
    }
    out = assign_tiers([unreachable])
    assert out[0]["tier"] == "master"
