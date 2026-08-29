from lib.records import append_jsonl, company_id, ensure_signals, read_jsonl, row_key, write_jsonl


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


# --- RULING C53: the C35 resume-key fallback chain, promoted here so
# site_scrape.py and enrich_tier1.py can share it instead of each keying
# resume on a bare company_id (falsy/missing on an older or malformed
# row, silently reprocessing or, worse, silently dropping later rows).

def test_row_key_uses_company_id_when_present():
    row = {"company_id": "abc123", "name": "Acme Roofing LLC", "state": "TX",
           "domain": "acmeroofing.com"}
    assert row_key(row) == "abc123"


def test_row_key_falls_back_to_domain_identity_when_company_id_is_none():
    row = {"name": "Acme Roofing LLC", "state": "TX", "domain": "acmeroofing.com",
           "company_id": None}
    expected = company_id("Acme Roofing LLC", "TX", "acmeroofing.com")
    assert row_key(row) == expected


def test_row_key_falls_back_when_company_id_key_is_absent_entirely():
    row = {"name": "Acme Roofing LLC", "state": "TX", "domain": None}
    expected = company_id("Acme Roofing LLC", "TX", None)
    assert row_key(row) == expected


def test_row_key_never_returns_a_falsy_value():
    # The whole point of C53: unlike a bare `row.get("company_id")`,
    # row_key must never itself be a value ("" or None) that could
    # collide with another idless row's key in a resume set.
    assert row_key({}) not in (None, "")
    assert row_key({"company_id": None, "name": "", "state": ""}) not in (None, "")


# --- RULING C54: ensure_signals must handle "absent" and "present but
# explicitly null" identically, unlike row.setdefault("signals", {}),
# which is a no-op (and returns None) in the second case.

def test_ensure_signals_creates_when_key_is_absent():
    row = {"name": "Acme"}
    sig = ensure_signals(row)
    assert sig == {}
    assert row["signals"] == {}


def test_ensure_signals_replaces_an_explicit_null():
    row = {"name": "Acme", "signals": None}
    sig = ensure_signals(row)
    assert sig == {}
    assert row["signals"] == {}


def test_ensure_signals_preserves_an_existing_dict():
    row = {"name": "Acme", "signals": {"reviews": 5}}
    sig = ensure_signals(row)
    assert sig == {"reviews": 5}
    assert sig is row["signals"]


def test_ensure_signals_returned_dict_is_mutable_in_place():
    row = {"signals": None}
    sig = ensure_signals(row)
    sig["headcount"] = 40
    assert row["signals"]["headcount"] == 40
