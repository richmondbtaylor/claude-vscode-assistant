import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import library


@pytest.fixture(autouse=True)
def temp_library(tmp_path, monkeypatch):
    root = tmp_path / "design-systems"
    root.mkdir()
    monkeypatch.setattr(library, "LIBRARY_ROOT", root)
    return root


@pytest.mark.parametrize(
    "source,expected",
    [
        ("https://linear.app", "linear"),
        ("https://www.nothing.tech", "nothing-tech"),
        ("https://stripe.com", "stripe"),
        ("http://notion.so/", "notion"),
        ("https://design.stripe.com", "design-stripe"),
        ("https://www.linear.app/features", "linear"),
    ],
)
def test_slug_from_url(source, expected):
    assert library.slug_from_source(source) == expected


def test_explicit_name_overrides_derivation():
    assert library.slug_from_source("https://linear.app", "Acme Design Co") == "acme-design-co"


def test_slugify_collapses_punctuation_and_case():
    assert library.slugify("  Nothing.tech  UI!! ") == "nothing-tech-ui"


def test_manifest_round_trip(temp_library):
    data = {"slug": "linear", "name": "Linear", "mode": "ultra"}
    path = library.write_manifest("linear", data)
    assert path == temp_library / "linear" / "manifest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["name"] == "Linear"
    assert library.read_manifest("linear")["mode"] == "ultra"


def test_read_manifest_missing_returns_none():
    assert library.read_manifest("nope") is None


def test_read_manifest_corrupt_returns_none(temp_library):
    bad = temp_library / "broken"
    bad.mkdir()
    (bad / "manifest.json").write_text("{not json", encoding="utf-8")
    assert library.read_manifest("broken") is None


def test_list_systems_sorted_and_skips_unregistered(temp_library):
    library.write_manifest("zeta", {"slug": "zeta", "name": "Zeta"})
    library.write_manifest("alpha", {"slug": "alpha", "name": "Alpha"})
    (temp_library / "orphan").mkdir()
    assert [s["slug"] for s in library.list_systems()] == ["alpha", "zeta"]


def test_resolve_matches_slug_name_and_case(temp_library):
    library.write_manifest("linear", {"slug": "linear", "name": "Linear"})
    assert library.resolve("linear") == "linear"
    assert library.resolve("Linear") == "linear"
    assert library.resolve("  LINEAR ") == "linear"


def test_resolve_unknown_returns_none(temp_library):
    library.write_manifest("linear", {"slug": "linear", "name": "Linear"})
    assert library.resolve("figma") is None
