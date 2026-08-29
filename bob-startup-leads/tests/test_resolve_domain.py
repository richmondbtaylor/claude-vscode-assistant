import json
import sys

import config
import resolve_domain
from lib.records import read_jsonl, write_jsonl
from resolve_domain import main, pick_domain

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
#
# --- RULING C18: state detection is postal-context-only, not an enumerated
# --- list of "ambiguous" codes ---
#
# C16's first cut enumerated codes that double as ordinary words (IN, OR, OK,
# ME, HI, DE) and only trusted those in all-caps. Review found two holes: CO
# ("Company") was missing from the list and isn't caps-gated at all, so a
# true match titled "Beacon Roofing Co" against a "TX" company was rejected;
# and the caps gate itself is not proven against a stylized all-caps title.
# C18 replaces the whole enumeration: a two-letter code only counts as a
# state reference in postal form (", TX" or "TX 78701"), in either letter
# case. Full state names still match as whole words/phrases anywhere,
# case-insensitively.


def test_rejects_collaer_collier_false_positive_by_state_conflict():
    """The real regression from the live batch.

    collierenterprises.com is the real Collier Enterprises, a Naples,
    Florida land/agriculture company -- unrelated to the Wisconsin SBA
    borrower "Collaer Enterprises, Inc." The snippet below is a
    RECONSTRUCTION (not a captured live Brave result) built to carry the
    Florida location that a real snippet for that company would plausibly
    show. It must not match the WI borrower.

    Under C18 the full state name "Florida" in the description is what
    fires _conflicting_state (full names match anywhere, unconditionally).
    The comma-form "Naples, FL" in the title independently also satisfies
    the postal-comma rule, so either signal alone would reject this
    candidate; both happen to be present here because that is how a real
    business snippet reads.
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
    """ratio >= 90 with no location information anywhere is still accepted.

    Note: state here is "CO", same as the bare "Co" in the title, so this
    test alone would not catch the CO/"Company" bug the reviewer found --
    see test_reviewer_scenario_bare_co_title_not_treated_as_colorado below
    for the version with a genuinely different state.
    """
    results = [{
        "title": "Beacon Roofing Co",
        "url": "https://beaconroofingco.com/",
        "description": "Trusted roofers.",
    }]
    # "Beacon Roofing Company" vs stem "beaconroofingco" ratio ~93 (>= 90).
    assert pick_domain("Beacon Roofing Company", "Denver", "CO", results) == "beaconroofingco.com"


def test_reviewer_scenario_bare_co_title_not_treated_as_colorado():
    """The reviewer's exact C18 scenario: a true high-ratio match must not be
    rejected because its title ends in "Co" (short for "Company").

    Company state is "TX", genuinely different from "CO" -- if bare "Co" in
    the title were still misread as Colorado, this would wrongly reject.
    Under C18, "Co" here is preceded by a space, not a comma, and is not
    followed by a ZIP, so it is never treated as a state at all.
    """
    results = [{
        "title": "Beacon Roofing Co",
        "url": "https://beaconroofingco.com/",
        "description": "Trusted roofers.",
    }]
    assert pick_domain("Beacon Roofing Company", "Austin", "TX", results) == "beaconroofingco.com"


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
    ("HVAC in Austin TX"). Under C18 this bare "in" is never a state marker
    at all -- it is preceded by a space, not a comma, and is not followed by
    a ZIP -- which is what keeps that fixture passing unmodified.
    """
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "Baked fresh in the morning, delivered daily.",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"


def test_all_caps_title_bare_in_does_not_register_as_indiana():
    """A stylized ALL-CAPS title must not false-fire either.

    "IN" here is bare prose (preceded by a space, not a comma; not followed
    by a ZIP), so under C18 it is never read as Indiana regardless of case --
    proving the postal-context rule, not a caps gate, is what protects this.
    """
    results = [{
        "title": "SERVING CLIENTS IN AUSTIN",
        "url": "https://sunrisebakery.com/",
        "description": "",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Austin", "TX", results) == "sunrisebakery.com"


def test_comma_form_two_letter_code_is_detected_as_a_conflict():
    """Postal comma form (", FL") IS detected as a real state reference."""
    results = [{
        "title": "Palm Properties",
        "url": "https://palmproperties.com/",
        "description": "Located in Naples, FL near the coast.",
    }]
    assert pick_domain("Palm Properties LLC", "Madison", "WI", results) is None


def test_zip_adjacent_two_letter_code_is_detected_as_a_conflict():
    """Postal ZIP-adjacent form ("TX 78701") IS detected as a real state reference."""
    results = [{
        "title": "Palm Properties",
        "url": "https://palmproperties.com/",
        "description": "Our office: Austin TX 78701.",
    }]
    assert pick_domain("Palm Properties LLC", "Miami", "FL", results) is None


def test_bare_uppercase_code_in_prose_is_not_treated_as_a_state():
    """A bare, uncommaed code in running prose is NOT a state, even in caps."""
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "Proudly serving the greater TX region.",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"


def test_bare_lowercase_code_in_prose_is_not_treated_as_a_state():
    """A bare, uncommaed code in running prose is NOT a state, lowercase either."""
    results = [{
        "title": "Sunrise Bakery",
        "url": "https://sunrisebakery.com/",
        "description": "Proudly serving the greater tx region.",
    }]
    assert pick_domain("Sunrise Bakery LLC", "Los Angeles", "CA", results) == "sunrisebakery.com"


# --- RULING C52: resolve_domain.py is a network stage (one Brave query
# per unresolved company) and gets the same resume discipline every other
# network stage has. The subtlety: a company that was queried and came
# back with no match must be recorded as attempted, or it is retried
# (and re-billed) forever, indistinguishable from a company never tried.

ROW_NO_DOMAIN = {"company_id": "c1", "name": "Rivera Mechanical", "domain": None,
                  "website": None, "city": "Austin", "state": "TX"}


def test_main_resume_skips_a_row_already_checkpointed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    already_done = dict(ROW_NO_DOMAIN, domain_resolve_attempted=True)
    write_jsonl(tmp_path / "companies.jsonl", [ROW_NO_DOMAIN])
    write_jsonl(tmp_path / "resolved.jsonl", [already_done])

    def boom(*a, **k):
        raise AssertionError("brave_search must not be called for an already-done row")
    monkeypatch.setattr(resolve_domain, "brave_search", boom)
    monkeypatch.setattr(sys, "argv", ["resolve_domain.py"])

    main()

    out = list(read_jsonl(tmp_path / "resolved.jsonl"))
    assert len(out) == 1  # not duplicated


def test_main_records_a_genuine_no_match_attempt_so_it_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    write_jsonl(tmp_path / "companies.jsonl", [ROW_NO_DOMAIN])

    calls = []
    def fake_search(query, count=8):
        calls.append(query)
        return []  # no results -> pick_domain returns None -> genuinely unresolved
    monkeypatch.setattr(resolve_domain, "brave_search", fake_search)
    monkeypatch.setattr(resolve_domain.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["resolve_domain.py"])

    main()  # first run: attempts and fails to resolve

    assert len(calls) == 1
    out = list(read_jsonl(tmp_path / "resolved.jsonl"))
    assert len(out) == 1
    assert out[0]["domain"] is None
    assert out[0]["domain_resolve_attempted"] is True

    main()  # second run: must not re-query the same unresolved row

    assert len(calls) == 1  # unchanged -- no second Brave query spent
    out = list(read_jsonl(tmp_path / "resolved.jsonl"))
    assert len(out) == 1  # not duplicated either


def test_main_checkpoints_a_row_that_already_has_a_domain_without_a_query(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    row_with_domain = dict(ROW_NO_DOMAIN, domain="riveramechanical.com",
                            website="https://riveramechanical.com")
    write_jsonl(tmp_path / "companies.jsonl", [row_with_domain])

    def boom(*a, **k):
        raise AssertionError("brave_search must not be called for a row with a domain")
    monkeypatch.setattr(resolve_domain, "brave_search", boom)
    monkeypatch.setattr(sys, "argv", ["resolve_domain.py"])

    main()

    out = list(read_jsonl(tmp_path / "resolved.jsonl"))
    assert len(out) == 1
    assert out[0]["domain"] == "riveramechanical.com"
    assert out[0]["domain_resolve_attempted"] is True


def test_main_limit_leaves_unattempted_rows_uncheckpointed_for_a_future_run(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    row_a = dict(ROW_NO_DOMAIN, company_id="c1", name="Company A")
    row_b = dict(ROW_NO_DOMAIN, company_id="c2", name="Company B")
    write_jsonl(tmp_path / "companies.jsonl", [row_a, row_b])

    monkeypatch.setattr(resolve_domain, "brave_search", lambda query, count=8: [])
    monkeypatch.setattr(resolve_domain.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["resolve_domain.py", "--limit", "1"])

    main()

    out = list(read_jsonl(tmp_path / "resolved.jsonl"))
    assert len(out) == 1  # only the one row the limit allowed is checkpointed
