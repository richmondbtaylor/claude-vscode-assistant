from resolve_domain import pick_domain

RESULTS = [
    {"title": "Rivera Mechanical | HVAC in Austin TX",
     "url": "https://riveramechanical.com/", "description": "Austin HVAC since 1998."},
    {"title": "Rivera Mechanical - Yelp",
     "url": "https://www.yelp.com/biz/rivera-mechanical-austin", "description": ""},
]


def test_picks_matching_company_domain():
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", RESULTS) == "riveramechanical.com"


def test_skips_directory_hosts():
    only_yelp = [RESULTS[1]]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", only_yelp) is None


def test_rejects_unrelated_domain():
    unrelated = [{"title": "Austin HVAC Pros", "url": "https://austinhvacpros.com/",
                  "description": "Best HVAC in Austin"}]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", unrelated) is None


def test_accepts_abbreviated_domain_when_tokens_match():
    abbrev = [{"title": "Rivera Mechanical", "url": "https://rivera-mechanical.net/",
               "description": "Austin, TX"}]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", abbrev) == "rivera-mechanical.net"


def test_empty_results_return_none():
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", []) is None


# --- RULING C16: location must corroborate a weak domain-stem match ---
#
# pick_domain used to match on domain-stem string similarity alone. That is
# exactly why the live batch matched "Collaer Enterprises, Inc." (a WI SBA
# borrower) to collierenterprises.com: the generic token "enterprises"
# dominates the ratio, so a one-letter surname difference still scores ~94
# and clears MATCH_THRESHOLD (82). These tests cover the fix: conflicting
# location disqualifies outright; below a 90 stem ratio, city/state must
# corroborate; at/above 90 with no conflicting location, accept.


def test_rejects_collaer_collier_false_positive_by_state_conflict():
    """The real regression from the live batch.

    collierenterprises.com is the real Collier Enterprises, a Naples,
    Florida land/agriculture company -- unrelated to the Wisconsin SBA
    borrower "Collaer Enterprises, Inc." The snippet below is a
    RECONSTRUCTION (not a captured live Brave result) built to carry the
    Florida location that a real snippet for that company would plausibly
    show. It must not match the WI borrower.
    """
    results = [{
        "title": "Collier Enterprises | Naples, FL Land & Agriculture",
        "url": "https://collierenterprises.com/",
        "description": "Collier Enterprises is a diversified land "
                        "management company based in Naples, Florida.",
    }]
    assert pick_domain("Collaer Enterprises, Inc.", "North Prairie", "WI", results) is None


def test_rejects_high_ratio_candidate_naming_different_state():
    """A candidate naming a different state is rejected even at a high stem ratio."""
    results = [{
        "title": "Sunrise Bakery - Portland, OR",
        "url": "https://sunrisebakery.com/",
        "description": "Fresh bread daily in Portland, Oregon.",
    }]
    # stem ratio here is 100 (exact stem match) -- only the state conflict
    # rule can be rejecting this candidate.
    assert pick_domain("Sunrise Bakery LLC", "Miami", "FL", results) is None


def test_mid_ratio_accepted_with_city_corroboration():
    """82 <= ratio < 90 is accepted once the company's city appears somewhere."""
    results = [{
        "title": "Beacon Roofing",
        "url": "https://beaconroof.com/",
        "description": "Roofing contractor serving Denver, CO homeowners.",
    }]
    # "Beacon Roofing Company" vs stem "beaconroof" ratio ~87 (82-89 band).
    assert pick_domain("Beacon Roofing Company", "Denver", "CO", results) == "beaconroof.com"


def test_mid_ratio_rejected_without_any_location():
    """Same 82-89 band candidate, but nothing in the snippet corroborates it."""
    results = [{
        "title": "Beacon Roofing",
        "url": "https://beaconroof.com/",
        "description": "Quality roofing contractor since 1990.",
    }]
    assert pick_domain("Beacon Roofing Company", "Denver", "CO", results) is None


def test_high_ratio_accepted_without_any_location_info():
    """ratio >= 90 with no location information anywhere is still accepted."""
    results = [{
        "title": "Beacon Roofing Co",
        "url": "https://beaconroofingco.com/",
        "description": "Trusted roofers.",
    }]
    # "Beacon Roofing Company" vs stem "beaconroofingco" ratio ~93 (>= 90).
    assert pick_domain("Beacon Roofing Company", "Denver", "CO", results) == "beaconroofingco.com"


def test_empty_state_high_ratio_still_accepted():
    """Job-lane rows carry state '' by design; empty state must not crash."""
    results = [{
        "title": "Beacon Roofing Co",
        "url": "https://beaconroofingco.com/",
        "description": "Trusted roofers.",
    }]
    assert pick_domain("Beacon Roofing Company", "", "", results) == "beaconroofingco.com"


def test_empty_state_mid_ratio_rejected_without_corroboration():
    """Empty city/state counts as neither corroboration nor conflict."""
    results = [{
        "title": "Beacon Roofing",
        "url": "https://beaconroof.com/",
        "description": "Quality roofing contractor since 1990.",
    }]
    assert pick_domain("Beacon Roofing Company", "", "", results) is None


def test_domain_word_does_not_register_as_maine():
    """A description containing 'domain' must not register as Maine (ME)."""
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "Our domain is fresh bread every morning.",
    }]
    # Company state is CA; if "domain" wrongly registered as Maine this
    # would look like a conflicting-state candidate and be rejected.
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"


def test_coordinate_word_does_not_register_as_indiana():
    """A description containing 'coordinate' must not register as Indiana (IN)."""
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "We coordinate deliveries across town.",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"


def test_standalone_ordinary_word_in_does_not_register_as_indiana():
    """"in" used as an ordinary lowercase preposition must not read as Indiana.

    This is the same shape of text as the brief's own Austin/TX fixture
    ("HVAC in Austin TX") -- proving the whole-word code match does not
    false-fire on that case is what keeps that fixture passing unmodified.
    """
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "Baked fresh in the morning, delivered daily.",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"
