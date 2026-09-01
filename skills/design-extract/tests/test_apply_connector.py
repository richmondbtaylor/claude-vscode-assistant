import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apply_connector as ac


def write_skill(tmp_path: Path, name: str, body: bytes) -> Path:
    folder = tmp_path / name
    folder.mkdir()
    path = folder / "SKILL.md"
    path.write_bytes(body)
    return path


def test_all_nineteen_targets_have_a_group():
    all_skills = [s for group in ac.GROUPS.values() for s in group]
    assert len(all_skills) == 19
    assert len(set(all_skills)) == 19, "no skill may appear in two groups"
    for skill in all_skills:
        assert ac.group_of(skill) is not None


def test_every_group_has_a_tail_line():
    assert set(ac.GROUPS) == set(ac.TAILS)


def test_render_block_contains_the_contract_essentials():
    block = ac.render_block("visual-code")
    assert "## Extracted Design System" in block
    assert "BORROW" in block and "KEEP" in block
    assert "full <name> system" in block
    assert "design-extract/references/consumption.md" in block
    assert ".design-system" in block


def test_render_block_ranks_design_intel_below_measured_values():
    block = ac.render_block("visual-code")
    assert "design-intel" in block
    assert "Measured beats recommended" in block


def test_render_block_uses_the_group_tail():
    assert "tokens/colors.json" in ac.render_block("visual-code")
    assert "ANIMATIONS.md" in ac.render_block("gsap")
    assert "VISUAL_GUIDE.md" in ac.render_block("citadel")


def test_branding_agent_block_is_inverted():
    block = ac.render_block("branding-agent")
    assert "authority" in block.lower()
    assert "beneath" in block.lower()
    # The authority skill must never be told to defer.
    assert "KEEP from `branding-agent`" not in block


def test_apply_preserves_bom_and_crlf(tmp_path):
    original = b"\xef\xbb\xbf---\r\nname: x\r\n---\r\n\r\n# Body\r\n"
    path = write_skill(tmp_path, "visual-code", original)
    assert ac.apply_to_file(path) == "applied"
    after = path.read_bytes()
    assert after.startswith(b"\xef\xbb\xbf"), "BOM must survive"
    assert after.startswith(original), "not one original byte may change"
    assert ac.SENTINEL_START in after


def test_apply_is_idempotent(tmp_path):
    path = write_skill(tmp_path, "visual-code", b"# Body\n")
    assert ac.apply_to_file(path) == "applied"
    first = path.read_bytes()
    assert ac.apply_to_file(path) == "already"
    assert path.read_bytes() == first


def test_apply_adds_separating_newline_when_missing(tmp_path):
    path = write_skill(tmp_path, "visual-code", b"# Body no trailing newline")
    ac.apply_to_file(path)
    assert b"newline\n" in path.read_bytes()


def test_revert_restores_byte_for_byte(tmp_path):
    original = b"\xef\xbb\xbf# Body\r\n\r\nlast line\r\n"
    path = write_skill(tmp_path, "branding-agent", original)
    ac.apply_to_file(path)
    assert path.read_bytes() != original
    assert ac.revert_file(path) is True
    assert path.read_bytes() == original


def test_revert_restores_file_lacking_trailing_newline(tmp_path):
    original = b"# Body no trailing newline"
    path = write_skill(tmp_path, "gsap", original)
    ac.apply_to_file(path)
    assert ac.SENTINEL_START_NL in path.read_bytes(), "must record that a newline was added"
    assert ac.revert_file(path) is True
    assert path.read_bytes() == original


def test_revert_without_block_is_a_noop(tmp_path):
    original = b"# Body\n"
    path = write_skill(tmp_path, "visual-code", original)
    assert ac.revert_file(path) is False
    assert path.read_bytes() == original


def test_apply_skips_unknown_skill(tmp_path):
    path = write_skill(tmp_path, "not-a-design-skill", b"# Body\n")
    assert ac.apply_to_file(path) == "skipped"
    assert ac.SENTINEL_START not in path.read_bytes()


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    path = write_skill(tmp_path, "visual-code", b"# Body\n")
    monkeypatch.setattr(ac, "SKILLS_ROOT", tmp_path)
    assert ac.main(["--dry-run", "--only", "visual-code"]) == 0
    assert path.read_bytes() == b"# Body\n"
