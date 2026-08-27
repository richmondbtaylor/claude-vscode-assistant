import json

import signals
from lib.records import company_id
from signals import parse_headcount, score_marketplace_results, score_press_results


def test_parse_headcount_from_linkedin_copy():
    assert parse_headcount("51-200 employees") == 200
    assert parse_headcount("11-50 employees · Construction") == 50
    assert parse_headcount("2-10 employees") == 10
    assert parse_headcount("10,001+ employees") == 10001


def test_parse_headcount_returns_none_for_noise():
    assert parse_headcount("") is None
    assert parse_headcount("See jobs") is None


def test_parse_headcount_from_realistic_full_page_text():
    body = ("Acme Roofing LLC | LinkedIn\nAbout us\nAcme Roofing LLC\n"
            "Construction · Tampa, FL\n51-200 employees · Construction\n"
            "1,204 followers\nOverview\nWebsite\nacmeroofing.com\nIndustry\n"
            "Construction\nCompany size\n51-200 employees\nHeadquarters\nTampa, FL")
    assert parse_headcount(body) == 200


def test_marketplace_results_detect_known_platforms():
    results = [
        {"url": "https://www.g2.com/products/acme/reviews", "title": "Acme Reviews"},
        {"url": "https://www.bbb.org/us/tx/austin/profile/hvac/acme-123", "title": "BBB"},
        {"url": "https://randomblog.com/acme", "title": "blog"},
    ]
    assert sorted(score_marketplace_results(results)) == ["bbb", "g2"]


def test_marketplace_results_empty_when_nothing_matches():
    assert score_marketplace_results([{"url": "https://x.com/y", "title": "z"}]) == []


def test_marketplace_presence_returns_empty_list_on_brave_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("brave down")
    monkeypatch.setattr(signals, "brave_search", boom)
    assert signals.marketplace_presence("Acme Roofing", "acmeroofing.com") == []


# RULING C33: press_hits must only count a Brave result that both names
# the company AND carries a press/funding term. Raw result volume is not
# evidence of anything since Brave returns something for almost any query.

def test_score_press_results_counts_only_name_and_press_term_matches():
    results = [
        {"title": "Acme Roofing raises $2M seed round",
         "description": "Tampa-based Acme Roofing announced funding."},
        {"title": "Best roofing tips for 2026",
         "description": "General roofing advice, no company named."},
        {"title": "Acme Roofing wins local award",
         "description": "Acme Roofing named Tampa's best contractor."},
        {"title": "Random Company acquired by Big Corp",
         "description": "Unrelated acquisition news."},
    ]
    assert score_press_results(results, "Acme Roofing LLC") == 2


def test_score_press_results_empty_for_no_name_match():
    results = [{"title": "Roofing trends", "description": "Industry news, no company name."}]
    assert score_press_results(results, "Acme Roofing LLC") == 0


def test_score_press_results_empty_for_name_match_without_press_term():
    results = [{"title": "Acme Roofing careers page",
                "description": "Join the Acme Roofing team today."}]
    assert score_press_results(results, "Acme Roofing LLC") == 0


def test_score_press_results_empty_for_blank_name():
    results = [{"title": "Acme Roofing raises $2M", "description": "funding round"}]
    assert score_press_results(results, "") == 0


def test_press_hits_returns_zero_on_brave_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("brave down")
    monkeypatch.setattr(signals, "brave_search", boom)
    assert signals.press_hits("Acme Roofing", "Tampa") == 0


def test_press_hits_filters_raw_results_through_score_press_results(monkeypatch):
    raw = [
        {"title": "Acme Roofing raises $2M seed round", "description": "funding announced"},
        {"title": "Unrelated story", "description": "nothing to do with Acme"},
    ]
    monkeypatch.setattr(signals, "brave_search", lambda *a, **k: raw)
    assert signals.press_hits("Acme Roofing", "Tampa") == 1


# RULING C34: LinkedIn URL construction and page-parse logic, covered with
# fake page/response objects since the saved session does not authenticate
# and the live path cannot be exercised for real right now.

def test_linkedin_company_url_uses_domain_first_label():
    assert (signals._linkedin_company_url("acmeroofing.com")
            == "https://www.linkedin.com/company/acmeroofing/about/")


def test_linkedin_company_url_ignores_subdomain_and_tld_segments():
    assert (signals._linkedin_company_url("www.acme-roofing.co.uk")
            == "https://www.linkedin.com/company/www/about/")


def test_looks_like_not_found_detects_http_404():
    assert signals._looks_like_not_found("anything at all", 404) is True


def test_looks_like_not_found_detects_soft_404_text():
    body = "LinkedIn\nPage not found\nGo back to LinkedIn.com"
    assert signals._looks_like_not_found(body, 200) is True


def test_looks_like_not_found_false_for_real_company_page():
    body = "Acme Roofing LLC\n51-200 employees · Construction\nOverview"
    assert signals._looks_like_not_found(body, 200) is False


class _FakeResponse:
    def __init__(self, status):
        self.status = status


class _FakePage:
    def __init__(self, body, status=200, raise_on_goto=False):
        self._body = body
        self._status = status
        self._raise = raise_on_goto

    def goto(self, url, **kwargs):
        if self._raise:
            raise RuntimeError("navigation boom")
        return _FakeResponse(self._status)

    def wait_for_timeout(self, ms):
        pass

    def inner_text(self, selector):
        return self._body


def test_linkedin_headcount_parses_a_real_looking_page():
    page = _FakePage("Acme Roofing LLC\n51-200 employees · Construction\nOverview", status=200)
    assert signals.linkedin_headcount(page, "acmeroofing.com") == 200


def test_linkedin_headcount_none_for_http_404():
    page = _FakePage("anything", status=404)
    assert signals.linkedin_headcount(page, "ghostcompany.com") is None


def test_linkedin_headcount_none_for_soft_404_text():
    page = _FakePage("Page not found. Go back to LinkedIn.com", status=200)
    assert signals.linkedin_headcount(page, "ghostcompany.com") is None


def test_linkedin_headcount_none_when_page_found_but_no_headcount_text():
    page = _FakePage("Acme Roofing LLC\nOverview\nPosts\nJobs", status=200)
    assert signals.linkedin_headcount(page, "acmeroofing.com") is None


def test_linkedin_headcount_none_on_navigation_exception():
    page = _FakePage("", raise_on_goto=True)
    assert signals.linkedin_headcount(page, "acmeroofing.com") is None


# Minor reviewer finding: the auth probe had no coverage either.

class _FakeAuthPage:
    def __init__(self, url, raise_on_goto=False):
        self._url = url
        self._raise = raise_on_goto

    def goto(self, *a, **k):
        if self._raise:
            raise RuntimeError("boom")

    def wait_for_timeout(self, ms):
        pass

    @property
    def url(self):
        return self._url


def test_linkedin_authenticated_true_for_feed_url():
    assert signals._linkedin_authenticated(_FakeAuthPage("https://www.linkedin.com/feed/")) is True


def test_linkedin_authenticated_false_for_login_redirect():
    assert signals._linkedin_authenticated(_FakeAuthPage("https://www.linkedin.com/login")) is False


def test_linkedin_authenticated_false_for_checkpoint_redirect():
    url = "https://www.linkedin.com/checkpoint/challenge"
    assert signals._linkedin_authenticated(_FakeAuthPage(url)) is False


def test_linkedin_authenticated_false_on_exception():
    assert signals._linkedin_authenticated(_FakeAuthPage("", raise_on_goto=True)) is False


# RULING C35: resume key falls back from company_id to domain/name+state
# so a row with a falsy or missing company_id still gets a stable key.

def test_row_key_uses_company_id_when_present():
    row = {"company_id": "abc123", "name": "Acme Roofing LLC", "state": "TX", "domain": "acmeroofing.com"}
    assert signals._row_key(row) == "abc123"


def test_row_key_falls_back_to_canonical_identity_when_company_id_missing():
    row = {"name": "Acme Roofing LLC", "state": "TX", "domain": "acmeroofing.com", "company_id": None}
    expected = company_id("Acme Roofing LLC", "TX", "acmeroofing.com")
    assert signals._row_key(row) == expected


def test_row_key_falls_back_when_company_id_key_absent_entirely():
    row = {"name": "Acme Roofing LLC", "state": "TX", "domain": None}
    expected = company_id("Acme Roofing LLC", "TX", None)
    assert signals._row_key(row) == expected


# main() integration coverage: resume, no-domain passthrough, signal
# preservation. Network and browser calls are monkeypatched so these stay
# hermetic and fast.

DONE_ROW = {
    "company_id": "abc123", "name": "Done Co", "domain": "done.com", "website": None,
    "phone": None, "email": None, "email_status": "none", "address": "", "city": "Austin",
    "state": "TX", "zip": "", "naics": "", "category": "", "sources": ["maps"],
    "signals": {"reviews": 10, "rating": 4.5, "headcount": 50, "marketplaces": ["bbb"], "press_hits": 2},
}

NEW_ROW_NO_DOMAIN = {
    "company_id": "ghi789", "name": "No Domain Co", "domain": None, "website": None,
    "phone": None, "email": None, "email_status": "none", "address": "", "city": "Austin",
    "state": "TX", "zip": "", "naics": "", "category": "", "sources": ["jobs"],
    "signals": {"open_finance_req": True, "job_title": "Bookkeeper"},
}

NEW_ROW_WITH_DOMAIN = {
    "company_id": "def456", "name": "New Co", "domain": "new.com", "website": None,
    "phone": None, "email": None, "email_status": "none", "address": "", "city": "Austin",
    "state": "TX", "zip": "", "naics": "", "category": "", "sources": ["maps"],
    "signals": {"reviews": 20, "rating": 4.2, "maps_query": "marketing agency",
                "maps_city": "Austin TX", "needs_liveness_check": False,
                "tech": ["stripe"], "has_pricing_page": True, "has_careers_page": False},
}


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _read_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_main_resume_skips_rows_already_in_output(tmp_path, monkeypatch):
    monkeypatch.setattr(signals.config, "DATA", tmp_path)
    _write_jsonl(tmp_path / "sites.jsonl", [DONE_ROW, NEW_ROW_NO_DOMAIN])
    _write_jsonl(tmp_path / "signals.jsonl", [DONE_ROW])

    signals.main(limit=None)

    out = _read_jsonl(tmp_path / "signals.jsonl")
    ids = [r["company_id"] for r in out]
    assert ids.count("abc123") == 1
    assert "ghi789" in ids
    assert len(out) == 2


def test_main_no_domain_row_passes_through_and_consumes_no_query(tmp_path, monkeypatch):
    monkeypatch.setattr(signals.config, "DATA", tmp_path)
    _write_jsonl(tmp_path / "sites.jsonl", [NEW_ROW_NO_DOMAIN])

    calls = []
    monkeypatch.setattr(signals, "marketplace_presence", lambda *a, **k: calls.append("m") or [])
    monkeypatch.setattr(signals, "press_hits", lambda *a, **k: calls.append("p") or 0)

    signals.main(limit=None)

    assert calls == []
    out = _read_jsonl(tmp_path / "signals.jsonl")
    assert out == [NEW_ROW_NO_DOMAIN]


class _FakePW:
    def start(self):
        return self

    def stop(self):
        pass


def test_main_preserves_earlier_stage_signals_on_domain_row(tmp_path, monkeypatch):
    monkeypatch.setattr(signals.config, "DATA", tmp_path)
    _write_jsonl(tmp_path / "sites.jsonl", [NEW_ROW_WITH_DOMAIN])

    monkeypatch.setattr(signals, "marketplace_presence", lambda *a, **k: ["bbb"])
    monkeypatch.setattr(signals, "press_hits", lambda *a, **k: 3)
    monkeypatch.setattr(signals, "sync_playwright", lambda: _FakePW())
    monkeypatch.setattr(signals, "_open_linkedin_page", lambda pw: (None, None))

    signals.main(limit=None)

    out = _read_jsonl(tmp_path / "signals.jsonl")
    assert len(out) == 1
    sig = out[0]["signals"]
    # every earlier-stage key survives
    assert sig["reviews"] == 20
    assert sig["rating"] == 4.2
    assert sig["maps_query"] == "marketing agency"
    assert sig["maps_city"] == "Austin TX"
    assert sig["needs_liveness_check"] is False
    assert sig["tech"] == ["stripe"]
    assert sig["has_pricing_page"] is True
    assert sig["has_careers_page"] is False
    # new keys land inside signals too
    assert sig["headcount"] is None
    assert sig["marketplaces"] == ["bbb"]
    assert sig["press_hits"] == 3
