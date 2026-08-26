from lib.records import company_id, read_jsonl, write_jsonl


def test_company_id_is_stable_for_same_domain():
    a = company_id("Acme Plumbing LLC", "FL", "acmeplumbing.com")
    b = company_id("ACME PLUMBING, INC.", "FL", "acmeplumbing.com")
    assert a == b


def test_company_id_differs_across_states_without_domain():
    a = company_id("Acme Plumbing", "FL", None)
    b = company_id("Acme Plumbing", "TX", None)
    assert a != b


def test_jsonl_roundtrip(tmp_path):
    path = tmp_path / "out.jsonl"
    rows = [{"name": "A", "n": 1}, {"name": "B", "n": 2}]
    assert write_jsonl(path, rows) == 2
    assert list(read_jsonl(path)) == rows


def test_read_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "out.jsonl"
    path.write_text('{"a":1}\n\n{"a":2}\n', encoding="utf-8")
    assert list(read_jsonl(path)) == [{"a": 1}, {"a": 2}]
