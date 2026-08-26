from lib.records import append_jsonl, company_id, read_jsonl, write_jsonl


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


def test_read_jsonl_skips_truncated_trailing_line(tmp_path, capsys):
    # A process killed mid-append can leave a partial final line. The
    # well-formed rows before it must still come back, and the skip must
    # be visible rather than silent.
    path = tmp_path / "out.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n{"a":3, "b"', encoding="utf-8")
    assert list(read_jsonl(path)) == [{"a": 1}, {"a": 2}]
    assert "skipped malformed line" in capsys.readouterr().out


def test_append_jsonl_creates_a_nonexistent_file(tmp_path):
    path = tmp_path / "nested" / "out.jsonl"
    assert append_jsonl(path, [{"a": 1}]) == 1
    assert list(read_jsonl(path)) == [{"a": 1}]


def test_append_jsonl_accumulates_rather_than_replaces(tmp_path):
    path = tmp_path / "out.jsonl"
    append_jsonl(path, [{"a": 1}])
    append_jsonl(path, [{"a": 2}])
    assert list(read_jsonl(path)) == [{"a": 1}, {"a": 2}]


def test_append_jsonl_return_count_is_per_call_not_cumulative(tmp_path):
    path = tmp_path / "out.jsonl"
    assert append_jsonl(path, [{"a": 1}, {"a": 2}, {"a": 3}]) == 3
    assert append_jsonl(path, [{"a": 4}]) == 1
