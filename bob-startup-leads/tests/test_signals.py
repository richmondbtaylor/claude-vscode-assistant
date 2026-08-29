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


# RULING C36: a live diagnostic against real Brave results for two small
# roofing contractors showed the dominant false-positive pattern was
# directory/certification-badge listings (buildzoom, thebluebook,
# fivestarrated, bestpickreports, angi, nextdoor, facebook) naming the
# company and carrying "award" on a badge, not press coverage. These are
# excluded via the shared NON_COMPANY_HOSTS set. Also anchors the company
# name match on word boundaries so "Roof X" cannot match "Roof Xpress".

def test_is_directory_or_social_host_true_for_known_directory():
    assert signals._is_directory_or_social_host(
        "https://www.buildzoom.com/contractor/acme-roofing-llc") is True


def test_is_directory_or_social_host_true_for_angi_badge_page():
    assert signals._is_directory_or_social_host(
        "https://www.angi.com/companylist/us/fl/tampa/roofing.htm") is True


def test_is_directory_or_social_host_false_for_companys_own_site():
    assert signals._is_directory_or_social_host("https://acmeroofing.com/about") is False


def test_is_directory_or_social_host_false_for_blank_url():
    assert signals._is_directory_or_social_host("") is False


def test_score_press_results_excludes_directory_and_social_hosts():
    results = [
        {"url": "https://www.angi.com/companylist/us/fl/tampa/roofing.htm",
         "title": "Top 10 Best Roofers", "description": "Acme Roofing named a top pick, award winner."},
        {"url": "https://www.buildzoom.com/contractor/acme-roofing-llc",
         "title": "Acme Roofing | BuildZoom", "description": "Acme Roofing named a certified GAF contractor, award."},
        {"url": "https://acmeroofing.com/blog/press",
         "title": "Acme Roofing raises $2M", "description": "funding announced"},
    ]
    assert score_press_results(results, "Acme Roofing LLC") == 1


def test_mentions_company_word_boundary_true_for_exact_name():
    assert signals._mentions_company("Acme Roofing raised funding", "acme roofing") is True


def test_mentions_company_word_boundary_false_for_partial_word_overlap():
    # "roof x" must not match inside "roof xpress" -- no boundary between
    # the "x" in the target and the "press" that immediately follows it.
    assert signals._mentions_company("Roof Xpress named best contractor", "roof x") is False


def test_score_press_results_word_boundary_rejects_similarly_named_company():
    results = [{"url": "https://roofxpress.com",
                "title": "Roof Xpress named best contractor in Tampa", "description": ""}]
    assert score_press_results(results, "Roof X") == 0


# RULING C37: press coverage is third-party by definition. A company's own
# site self-reporting an award is not evidence of anything; left unfiltered
# any business could inflate this signal by writing "award-winning" on its
# own homepage. registrable_domain is reused for the comparison so this
# stays consistent with the rest of the pipeline's domain handling.

def test_score_press_results_excludes_companys_own_domain():
    results = [
        {"url": "https://acmeroofing.com/blog/best-of-florida",
         "title": "Acme Roofing named Best of Florida award winner",
         "description": "self-reported on our own site"},
        {"url": "https://tampabaytimes.com/business/acme-roofing-wins-award",
         "title": "Acme Roofing named a top contractor", "description": "local news coverage"},
    ]
    assert score_press_results(results, "Acme Roofing LLC", domain="acmeroofing.com") == 1


def test_score_press_results_own_domain_check_is_case_insensitive():
    results = [{"url": "https://www.AcmeRoofing.com/press",
                "title": "Acme Roofing named award winner", "description": ""}]
    assert score_press_results(results, "Acme Roofing LLC", domain="acmeroofing.com") == 0


def test_score_press_results_no_domain_does_not_crash_and_applies_no_own_domain_filter():
    results = [{"url": "https://acmeroofing.com/blog/best-of-florida",
                "title": "Acme Roofing named Best of Florida award winner", "description": ""}]
    assert score_press_results(results, "Acme Roofing LLC", domain=None) == 1
    assert score_press_results(results, "Acme Roofing LLC", domain="") == 1


def test_press_hits_threads_domain_through_to_exclude_own_site(monkeypatch):
    raw = [
        {"url": "https://acmeroofing.com/blog/best-of-florida",
         "title": "Acme Roofing named Best of Florida award winner", "description": ""},
        {"url": "https://tampabaytimes.com/business/acme-roofing-wins-award",
         "title": "Acme Roofing named a top contractor", "description": "local news coverage"},
    ]
    monkeypatch.setattr(signals, "brave_search", lambda *a, **k: raw)
    assert signals.press_hits("Acme Roofing", "Tampa", "acmeroofing.com") == 1


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

# Every earlier-stage signal key the scoring stage reads by name, all 18,
# populated with a concrete value. Exhaustive on purpose (not a
# representative subset) so a silently dropped key cannot slip past this
# test the way a partial spot-check would.
NEW_ROW_WITH_DOMAIN = {
    "company_id": "def456", "name": "New Co", "domain": "new.com", "website": None,
    "phone": None, "email": None, "email_status": "none", "address": "", "city": "Austin",
    "state": "TX", "zip": "", "naics": "", "category": "", "sources": ["maps", "jobs", "sba", "ats"],
    "signals": {
        # site_scrape.py
        "tech": ["stripe"], "has_pricing_page": True, "has_careers_page": False,
        # seed_maps.py
        "reviews": 20, "rating": 4.2, "maps_query": "marketing agency",
        "maps_city": "Austin TX", "needs_liveness_check": False,
        # seed_jobs.py
        "open_finance_req": True, "job_title": "Staff Accountant",
        "job_url": "https://boards.greenhouse.io/newco/jobs/123",
        "job_blurb": "New Co is hiring a Staff Accountant in Austin, TX.",
        "ats_host": "boards.greenhouse.io", "ats_slug": "newco",
        # seed_sba.py
        "jobs_supported": 12, "loan_amount": 250000, "loan_fy": 2023, "business_age": 7,
    },
}

# The 18 keys above, named explicitly so the assertion is exhaustive
# rather than a spot-check of whichever ones happened to get typed in.
EARLIER_STAGE_SIGNAL_KEYS = {
    "tech", "has_pricing_page", "has_careers_page",
    "reviews", "rating", "maps_query", "maps_city", "needs_liveness_check",
    "open_finance_req", "job_title", "job_url", "job_blurb", "ats_host", "ats_slug",
    "jobs_supported", "loan_amount", "loan_fy", "business_age",
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


# --- RULING C51: --limit must not silently cap a bare run. It used to
# default to 20, and the documented run order invokes this stage bare
# (`uv run signals.py`), so a full run silently scored 20 rows against a
# 1,000-row target with nothing printed to say so.

def test_limit_flag_defaults_to_no_cap():
    args = signals._parse_args([])
    assert args.limit is None


def test_limit_flag_still_available_for_a_deliberate_small_run():
    args = signals._parse_args(["--limit", "5"])
    assert args.limit == 5


def test_main_default_limit_is_none_too():
    import inspect
    assert inspect.signature(signals.main).parameters["limit"].default is None


# --- RULING C54: process_row must survive a row whose "signals" key is
# present but explicitly null (as opposed to merely absent), which is
# exactly the shape a row round-trips through JSON with once an earlier
# stage writes `"signals": null`. row.setdefault("signals", {}) is a
# no-op in that case and returns None, so sig["headcount"] = ... used to
# raise TypeError and abort the whole Brave/LinkedIn batch on one row.

def test_process_row_survives_a_present_but_null_signals_key(monkeypatch):
    monkeypatch.setattr(signals, "marketplace_presence", lambda *a, **k: ["bbb"])
    monkeypatch.setattr(signals, "press_hits", lambda *a, **k: 2)
    row = {"name": "Acme Roofing", "domain": "acmeroofing.com", "city": "Austin",
           "signals": None}
    out = signals.process_row(row, page=None)
    assert out["signals"]["marketplaces"] == ["bbb"]
    assert out["signals"]["press_hits"] == 2
    assert out["signals"]["headcount"] is None


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

    # Exhaustive: every one of the 18 earlier-stage keys the scoring
    # stage reads by name, checked against its original value, not just
    # a representative handful.
    original = NEW_ROW_WITH_DOMAIN["signals"]
    assert EARLIER_STAGE_SIGNAL_KEYS == set(original.keys())
    for key in EARLIER_STAGE_SIGNAL_KEYS:
        assert key in sig, f"earlier-stage signal key {key!r} was dropped"
        assert sig[key] == original[key], f"earlier-stage signal key {key!r} changed value"

    # new keys land inside signals too
    assert sig["headcount"] is None
    assert sig["marketplaces"] == ["bbb"]
    assert sig["press_hits"] == 3
