from signals import parse_headcount, score_marketplace_results


def test_parse_headcount_from_linkedin_copy():
    assert parse_headcount("51-200 employees") == 200
    assert parse_headcount("11-50 employees · Construction") == 50
    assert parse_headcount("2-10 employees") == 10
    assert parse_headcount("10,001+ employees") == 10001


def test_parse_headcount_returns_none_for_noise():
    assert parse_headcount("") is None
    assert parse_headcount("See jobs") is None


def test_marketplace_results_detect_known_platforms():
    results = [
        {"url": "https://www.g2.com/products/acme/reviews", "title": "Acme Reviews"},
        {"url": "https://www.bbb.org/us/tx/austin/profile/hvac/acme-123", "title": "BBB"},
        {"url": "https://randomblog.com/acme", "title": "blog"},
    ]
    assert sorted(score_marketplace_results(results)) == ["bbb", "g2"]


def test_marketplace_results_empty_when_nothing_matches():
    assert score_marketplace_results([{"url": "https://x.com/y", "title": "z"}]) == []
