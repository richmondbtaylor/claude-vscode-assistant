import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import activate
import library


@pytest.fixture(autouse=True)
def temp_library(tmp_path, monkeypatch):
    root = tmp_path / "design-systems"
    root.mkdir()
    monkeypatch.setattr(library, "LIBRARY_ROOT", root)
    library.write_manifest("linear", {"slug": "linear", "name": "Linear"})
    return root


def test_write_marker_uses_documented_format(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    path = activate.write_marker(project, "linear", "2026-08-31")
    assert path.name == ".design-system"
    assert path.read_text(encoding="utf-8") == "linear  # activated 2026-08-31\n"


def test_read_marker_round_trip(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    activate.write_marker(project, "linear", "2026-08-31")
    assert activate.read_marker(project) == "linear"


def test_read_marker_absent_returns_none(tmp_path):
    assert activate.read_marker(tmp_path) is None


def test_read_marker_ignores_comment_and_whitespace(tmp_path):
    (tmp_path / ".design-system").write_text("  linear   # whatever\n", encoding="utf-8")
    assert activate.read_marker(tmp_path) == "linear"


def test_read_marker_empty_file_returns_none(tmp_path):
    (tmp_path / ".design-system").write_text("\n  \n", encoding="utf-8")
    assert activate.read_marker(tmp_path) is None


def test_read_marker_comment_only_returns_none(tmp_path):
    (tmp_path / ".design-system").write_text("# nothing here\n", encoding="utf-8")
    assert activate.read_marker(tmp_path) is None


def test_clear_marker_removes_and_reports(tmp_path):
    activate.write_marker(tmp_path, "linear", "2026-08-31")
    assert activate.clear_marker(tmp_path) is True
    assert activate.read_marker(tmp_path) is None
    assert activate.clear_marker(tmp_path) is False


def test_cli_rejects_unregistered_system(tmp_path, capsys):
    code = activate.main(["figma", "--folder", str(tmp_path)])
    assert code == 1
    assert not (tmp_path / ".design-system").exists()
    out = capsys.readouterr().out
    assert "not in the library" in out
    assert "linear" in out  # lists what IS available


def test_cli_activates_registered_system(tmp_path):
    assert activate.main(["Linear", "--folder", str(tmp_path)]) == 0
    assert activate.read_marker(tmp_path) == "linear"
