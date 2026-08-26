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
