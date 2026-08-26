from seed_jobs import parse_ats_result

GREENHOUSE = {
    "title": "Bookkeeper at Rivera Mechanical",
    "url": "https://boards.greenhouse.io/riveramechanical/jobs/4212",
    "description": "Rivera Mechanical is hiring a full-time Bookkeeper in Austin, TX.",
}
LEVER = {
    "title": "Controller - Summit Roofing Group",
    "url": "https://jobs.lever.co/summitroofing/8a2c",
    "description": "Summit Roofing Group seeks a Controller.",
}
NOISE = {
    "title": "Bookkeeper jobs in Texas | Indeed.com",
    "url": "https://www.indeed.com/q-bookkeeper-l-texas-jobs.html",
    "description": "Browse 1,204 bookkeeper jobs.",
}


def test_greenhouse_result_yields_company_slug():
    out = parse_ats_result(GREENHOUSE)
    assert out["name"] == "Riveramechanical"
    assert out["signals"]["open_finance_req"] is True
    assert out["signals"]["job_title"] == "Bookkeeper at Rivera Mechanical"
    assert out["signals"]["job_url"].startswith("https://boards.greenhouse.io/")
    assert out["sources"] == ["jobs"]


def test_lever_result_yields_company_slug():
    out = parse_ats_result(LEVER)
    assert out["name"] == "Summitroofing"


def test_aggregator_result_rejected():
    assert parse_ats_result(NOISE) is None


def test_result_without_company_path_rejected():
    bare = dict(GREENHOUSE, url="https://boards.greenhouse.io/")
    assert parse_ats_result(bare) is None


def test_hyphenated_slug_keeps_word_boundary():
    hyphenated = dict(GREENHOUSE, url="https://boards.greenhouse.io/rivera-mechanical/jobs/1")
    out = parse_ats_result(hyphenated)
    assert out["name"] == "Rivera Mechanical"


def test_underscore_slug_keeps_word_boundary():
    underscored = dict(GREENHOUSE, url="https://boards.greenhouse.io/rivera_mechanical/jobs/1")
    out = parse_ats_result(underscored)
    assert out["name"] == "Rivera Mechanical"


def test_greenhouse_result_records_ats_provenance():
    out = parse_ats_result(GREENHOUSE)
    assert out["signals"]["ats_host"] == "boards.greenhouse.io"
    assert out["signals"]["ats_slug"] == "riveramechanical"


def test_lever_result_records_ats_provenance():
    out = parse_ats_result(LEVER)
    assert out["signals"]["ats_host"] == "jobs.lever.co"
    assert out["signals"]["ats_slug"] == "summitroofing"
