import json
import sys

import httpx
import pytest

import config
import enrich_tier1
from enrich_tier1 import (Budget, BudgetExceeded, _record_error, _redact,
                           is_satisfied, pick_best_contact,
                           registry_lookup_fl, seed_contact_from_row,
                           waterfall)


def test_row_with_verified_named_contact_is_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is True


def test_row_with_guessed_email_is_not_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "guessed"}
    assert is_satisfied(row) is False


def test_row_with_junk_name_is_not_satisfied():
    row = {"contact_name": "Get Ah", "contact_email": "info@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is False


def test_pick_best_contact_prefers_decision_maker_titles():
    people = [
        {"name": "Sam Reed", "title": "Marketing Intern", "email": "sam@acme.com"},
        {"name": "Maria Gonzalez", "title": "Owner", "email": "maria@acme.com"},
        {"name": "Lee Park", "title": "Technician", "email": "lee@acme.com"},
    ]
    assert pick_best_contact(people)["name"] == "Maria Gonzalez"


def test_pick_best_contact_rejects_invalid_names():
    people = [{"name": "Contact Us", "title": "Owner", "email": "info@acme.com"}]
    assert pick_best_contact(people) is None


def test_budget_blocks_spend_over_ceiling():
    budget = Budget(limit_usd=0.05)
    budget.charge(0.04)
    with pytest.raises(BudgetExceeded):
        budget.charge(0.03)


def test_budget_reports_remaining():
    budget = Budget(limit_usd=10.0)
    budget.charge(2.5)
    assert budget.remaining() == pytest.approx(7.5)


# RULING C9: steps 1-2 seed contact_* from data already on the row (free)
# before anything paid runs. These pin down that behaviour.

def test_seed_contact_from_row_uses_personal_email_as_guessed_candidate():
    row = {"email": "maria.gonzalez@acme.com", "email_status": "personal", "phone": "+15125550111"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "maria.gonzalez@acme.com"
    assert out["contact_email_status"] == "guessed"


def test_seed_contact_from_row_uses_generic_email_as_generic_status():
    row = {"email": "info@acme.com", "email_status": "generic"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "info@acme.com"
    assert out["contact_email_status"] == "generic"


def test_seed_contact_from_row_never_labels_a_seeded_email_verified():
    row = {"email": "maria.gonzalez@acme.com", "email_status": "personal"}
    out = seed_contact_from_row(row)
    assert out["contact_email_status"] != "verified"


def test_seed_contact_from_row_skips_when_no_email_on_row():
    row = {"email": None, "email_status": "none", "phone": "+15125550111"}
    out = seed_contact_from_row(row)
    assert "contact_email" not in out
    assert out["contact_phone"] == "+15125550111"


def test_seed_contact_from_row_does_not_overwrite_existing_contact():
    row = {"email": "info@acme.com", "email_status": "generic",
           "contact_email": "maria@acme.com", "contact_email_status": "verified"}
    out = seed_contact_from_row(row)
    assert out["contact_email"] == "maria@acme.com"
    assert out["contact_email_status"] == "verified"


def test_seed_contact_from_row_seeds_phone_from_maps():
    row = {"phone": "+13055550199"}
    out = seed_contact_from_row(row)
    assert out["contact_phone"] == "+13055550199"


def test_seed_contact_from_row_preserves_all_other_fields():
    row = {"company_id": "abc123", "name": "Acme LLC", "state": "FL",
           "email": "info@acme.com", "email_status": "generic"}
    out = seed_contact_from_row(row)
    assert out["company_id"] == "abc123"
    assert out["name"] == "Acme LLC"
    assert out["state"] == "FL"


# The waterfall must never crash a whole batch when a key is missing --
# money-safety demands the row comes back with an error noted, not a
# stack trace that kills every row after it.

def test_waterfall_survives_missing_hunter_and_apollo_keys(monkeypatch):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)
    monkeypatch.setattr("enrich_tier1.SECURITY", pytest.importorskip("pathlib").Path("no/such/dir"))
    row = {"company_id": "x1", "name": "Acme LLC", "domain": "acme-example-nonexistent.test",
           "state": "TX"}
    budget = Budget(limit_usd=0.0)
    out = waterfall(row, budget)
    assert out["company_id"] == "x1"
    assert not is_satisfied(out)
    assert out.get("enrich_errors")


# RULING C41: the final junk-name safety net must clear only the name and
# title. Email and its status are an independent fact and must survive.

def test_junk_name_gate_clears_name_but_keeps_valid_email_status():
    row = {"contact_name": "Contact Us", "contact_title": "Owner",
           "contact_email": "info@acme.com", "contact_email_status": "generic"}
    out = waterfall(row, Budget(limit_usd=0.0))
    assert out["contact_name"] == ""
    assert out["contact_title"] == ""
    assert out["contact_email"] == "info@acme.com"
    assert out["contact_email_status"] == "generic"


# RULING C38: a leaked API key in a written file is the worst outcome this
# stage can produce. _redact/_record_error are the two-layer fix -- a safe
# call-site summary (never str(exc)) plus a backstop that strips anything
# that looks like or matches a resolved key before it is ever appended.

def test_redact_strips_a_value_key_has_actually_resolved(monkeypatch):
    monkeypatch.setenv("SOME_TEST_KEY", "totally-secret-abc123")
    enrich_tier1._key("SOME_TEST_KEY")
    text = _redact("hunter call failed while using totally-secret-abc123 as the key")
    assert "totally-secret-abc123" not in text
    assert "REDACTED" in text


def test_redact_strips_generic_api_key_looking_patterns():
    text = _redact("request failed: ...&api_key=SUPERSECRET999&limit=10")
    assert "SUPERSECRET999" not in text
    assert "REDACTED" in text


def test_record_error_redacts_before_appending(monkeypatch):
    monkeypatch.setenv("SOME_OTHER_TEST_KEY", "another-secret-xyz789")
    enrich_tier1._key("SOME_OTHER_TEST_KEY")
    out = {}
    _record_error(out, "hunter: leaked another-secret-xyz789 in the message")
    dumped = json.dumps(out)
    assert "another-secret-xyz789" not in dumped
    assert "hunter" in dumped


def test_hunter_401_never_leaks_the_key_into_the_row_or_a_written_file(
        monkeypatch, tmp_path):
    fake_key = "sk-live-fake-key-should-never-appear-9f8e7d"
    monkeypatch.setenv("HUNTER_API_KEY", fake_key)
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)
    # An empty, real security dir so APOLLO_API_KEY resolution fails fast
    # (RuntimeError, no network call) rather than hitting the real Apollo
    # account from inside a unit test.
    monkeypatch.setattr(enrich_tier1, "SECURITY", tmp_path)

    def fake_get(url, params=None, timeout=None):
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(401, request=request,
                               json={"errors": [{"details": "invalid api key"}]})

    monkeypatch.setattr(httpx, "get", fake_get)

    row = {"company_id": "leak-check-1", "name": "Acme LLC",
           "domain": "acme-example-nonexistent.test", "state": "TX"}
    out = waterfall(row, Budget(limit_usd=0.0))

    dumped = json.dumps(out)
    assert fake_key not in dumped
    errors = " ".join(out.get("enrich_errors", []))
    assert fake_key not in errors
    assert "hunter" in errors

    from lib.records import append_jsonl
    out_path = tmp_path / "enriched.jsonl"
    append_jsonl(out_path, [out])
    on_disk = out_path.read_text(encoding="utf-8")
    assert fake_key not in on_disk


# RULING C39: a name match on Sunbiz is not enough to trust on its own --
# two different FL entities can normalize to the same name. Disambiguate
# by city; record no officer at all when that disambiguation fails.

class _FakeSunbizPage:
    """Stands in for a Playwright page: goto() records the URL, content()
    returns canned HTML keyed by a substring of that URL. No network, no
    browser."""

    def __init__(self, pages: dict[str, str]):
        self._pages = pages
        self._current = ""

    def goto(self, url, timeout=None):
        self._current = url

    def content(self):
        for key, html in self._pages.items():
            if key in self._current:
                return html
        return "<html></html>"


_SEARCH_HTML_ONE = '''<html><body><table>
<tr><td class="large-width"><a href="/Inquiry/CorporationSearch/SearchResultDetail?id=1">X ROOFING LLC</a></td></tr>
</table></body></html>'''

_SEARCH_HTML_TWO = '''<html><body><table>
<tr><td class="large-width"><a href="/Inquiry/CorporationSearch/SearchResultDetail?id=1">X ROOFING LLC</a></td></tr>
<tr><td class="large-width"><a href="/Inquiry/CorporationSearch/SearchResultDetail?id=2">X ROOFING LLC</a></td></tr>
</table></body></html>'''


def _detail_html(city: str, name: str) -> str:
    return f'''<html><body>
<div>Principal Address</div>
<div>100 MAIN ST</div>
<div>{city.upper()}, FL 33602</div>
<div>Officer/Director Detail</div>
<div>Title PRESIDENT</div>
<div>{name}</div>
<div>Annual Reports</div>
</body></html>'''


def test_registry_lookup_fl_single_candidate_returns_officer_without_city():
    page = _FakeSunbizPage({
        "SearchResults": _SEARCH_HTML_ONE,
        "id=1": _detail_html("Tampa", "SMITH, JOHN"),
    })
    best = registry_lookup_fl(page, "X Roofing LLC")
    assert best["name"] == "John Smith"


def test_registry_lookup_fl_disambiguates_by_city_when_names_collide():
    page = _FakeSunbizPage({
        "SearchResults": _SEARCH_HTML_TWO,
        "id=1": _detail_html("Tampa", "SMITH, JOHN"),
        "id=2": _detail_html("Miami", "DOE, JANE"),
    })
    tampa_best = registry_lookup_fl(page, "X Roofing LLC", city="Tampa")
    assert tampa_best["name"] == "John Smith"

    page2 = _FakeSunbizPage({
        "SearchResults": _SEARCH_HTML_TWO,
        "id=1": _detail_html("Tampa", "SMITH, JOHN"),
        "id=2": _detail_html("Miami", "DOE, JANE"),
    })
    miami_best = registry_lookup_fl(page2, "X Roofing LLC", city="Miami")
    assert miami_best["name"] == "Jane Doe"


def test_registry_lookup_fl_records_no_officer_when_ambiguous_and_uncorroborated():
    page_no_city = _FakeSunbizPage({
        "SearchResults": _SEARCH_HTML_TWO,
        "id=1": _detail_html("Tampa", "SMITH, JOHN"),
        "id=2": _detail_html("Miami", "DOE, JANE"),
    })
    assert registry_lookup_fl(page_no_city, "X Roofing LLC") is None

    page_wrong_city = _FakeSunbizPage({
        "SearchResults": _SEARCH_HTML_TWO,
        "id=1": _detail_html("Tampa", "SMITH, JOHN"),
        "id=2": _detail_html("Miami", "DOE, JANE"),
    })
    assert registry_lookup_fl(page_wrong_city, "X Roofing LLC", city="Orlando") is None


# RULING C40: the resume/dedup path in main() spends money (or would, once
# a real key exists), so a regression there means re-billing rows that
# already succeeded. Prove a row already in the output file is skipped and
# never reaches waterfall() at all.

def test_main_skips_rows_already_in_enriched_output(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)

    row = {"company_id": "dup-1", "name": "Acme LLC", "domain": "acme.test",
           "state": "TX", "tier": "tier1"}
    (tmp_path / "scored.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    already_done = dict(row, contact_name="Maria Gonzalez",
                         contact_email="maria@acme.test",
                         contact_email_status="verified")
    (tmp_path / "enriched.jsonl").write_text(
        json.dumps(already_done) + "\n", encoding="utf-8")

    calls = []

    def spy_waterfall(r, budget, page=None):
        calls.append(r)
        return r

    monkeypatch.setattr(enrich_tier1, "waterfall", spy_waterfall)
    monkeypatch.setattr(sys, "argv", ["enrich_tier1.py", "--limit", "5"])

    enrich_tier1.main()

    assert calls == []  # already-present row never reaches a paid step
    lines = (tmp_path / "enriched.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1  # untouched, not duplicated
