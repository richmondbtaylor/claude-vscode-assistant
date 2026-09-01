import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import extract
import library


def make_skillui_output(root: Path, name: str = "linear-design", ultra: bool = True) -> Path:
    """Build a folder shaped like real skillui output."""
    folder = root / name
    (folder / "tokens").mkdir(parents=True)
    (folder / "references").mkdir(parents=True)
    (folder / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
    (folder / "tokens" / "colors.json").write_text(
        json.dumps({"primary": "#5E6AD2", "bg": "#0D0E10", "fg": "#F7F8F8"}), encoding="utf-8"
    )
    (folder / "tokens" / "typography.json").write_text(
        json.dumps({"families": ["Inter Variable", "SF Mono"]}), encoding="utf-8"
    )
    if ultra:
        (folder / "screens" / "scroll").mkdir(parents=True)
        (folder / "screens" / "scroll" / "01.png").write_bytes(b"\x89PNG")
        (folder / "references" / "ANIMATIONS.md").write_text("# Motion\n", encoding="utf-8")
        (folder / "references" / "INTERACTIONS.md").write_text("# States\n", encoding="utf-8")
    return folder


# Real DEFAULT-mode skillui output (measured live against stripe.com and
# example.com): DESIGN.md / CLAUDE.md / SKILL.md / <name>.skill at the root,
# references/DESIGN.md, screenshots/, fonts/ -- and crucially NO tokens/ at
# all. DESIGN.md carries a markdown colour table (Section 2) and a fenced
# `font-family: "Name";` block under a numbered Typography Rules heading
# (Section 3) -- confirmed by an actual live extraction of stripe.com; there
# is no single "font pairing:" line anywhere in the real output.
DEFAULT_DESIGN_MD = """# stripe DESIGN.md

> Colors: 3 - Fonts: 2 - Components: 10

## 2. Color Palette & Roles

| Token | Hex | Role | Use |
|---|---|---|---|
| cardBackground | `#FFFFFF` | background | Page background |
| accent | `#635BFF` | accent | CTAs, links |
| textColor | `#0A2540` | text-primary | Headings and body text |

## 3. Typography Rules

**Font Stack:**
- **Sohne** -- Heading 1, Heading 2, Heading 3
- **GT America Mono** -- Body, Caption

**Font Sources:**

```css
@font-face {
  font-family: "Sohne";
  src: url("https://example.com/fonts/Sohne.woff2") format("woff2");
}
@font-face {
  font-family: "GT America Mono";
  src: url("https://example.com/fonts/GTAmericaMono.woff2") format("woff2");
}
```

## 4. Component Stylings

Nothing font-related lives past this heading; any font-family: found here
would indicate the section-scoping regressed.
"""


def make_default_only_output(root: Path, name: str = "stripe-design") -> Path:
    """Build a folder shaped like real skillui DEFAULT-mode output: no tokens/
    at all, only DESIGN.md (plus the other default-mode files)."""
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "CLAUDE.md").write_text("# Claude notes\n", encoding="utf-8")
    (folder / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    (folder / f"{name}.skill").write_text("skill-package\n", encoding="utf-8")
    (folder / "DESIGN.md").write_text(DEFAULT_DESIGN_MD, encoding="utf-8")
    (folder / "references").mkdir()
    (folder / "references" / "DESIGN.md").write_text(DEFAULT_DESIGN_MD, encoding="utf-8")
    (folder / "screenshots").mkdir()
    (folder / "screenshots" / "homepage.png").write_bytes(b"\x89PNG")
    (folder / "fonts").mkdir()
    (folder / "fonts" / "Sohne.woff2").write_bytes(b"wOFF2")
    return folder


@pytest.fixture(autouse=True)
def temp_library(tmp_path, monkeypatch):
    root = tmp_path / "design-systems"
    root.mkdir()
    monkeypatch.setattr(library, "LIBRARY_ROOT", root)
    # Redirect the index too — otherwise these tests append fake entries to the
    # real references/library.md.
    monkeypatch.setattr(extract, "INDEX_PATH", tmp_path / "library.md")
    return root


def test_index_line_goes_to_the_redirected_index(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "run_skillui",
                        lambda cmd, out: (make_skillui_output(out, ultra=False), (0, ""))[1])
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")
    extract.run_extraction("https://linear.app", "url", name=None, mode="default", screens=5)
    index = tmp_path / "library.md"
    assert index.is_file()
    assert "(`linear`)" in index.read_text(encoding="utf-8")


def test_build_command_ultra_includes_screens_and_name():
    cmd = extract.build_command(
        "https://linear.app", "url", Path("/out"), "Linear", "ultra", 10
    )
    assert cmd[:3] == ["npx", "-y", "skillui@latest"]
    assert "--url" in cmd and "https://linear.app" in cmd
    assert "--mode" in cmd and "ultra" in cmd
    assert cmd[cmd.index("--screens") + 1] == "10"
    assert cmd[cmd.index("--name") + 1] == "Linear"


def test_build_command_default_mode_omits_ultra_flags():
    cmd = extract.build_command("https://linear.app", "url", Path("/out"), None, "default", 10)
    assert "--mode" not in cmd
    assert "--screens" not in cmd
    assert "--name" not in cmd


def test_build_command_supports_dir_and_repo():
    assert "--dir" in extract.build_command("./app", "dir", Path("/o"), None, "default", 5)
    assert "--repo" in extract.build_command("https://x/y", "repo", Path("/o"), None, "default", 5)


def test_find_output_dir_picks_the_generated_folder(tmp_path):
    made = make_skillui_output(tmp_path)
    assert extract.find_output_dir(tmp_path) == made


def test_find_output_dir_empty_returns_none(tmp_path):
    assert extract.find_output_dir(tmp_path) is None


def test_validate_output_accepts_real_shape(tmp_path):
    ok, reason = extract.validate_output(make_skillui_output(tmp_path))
    assert ok is True
    assert reason == ""


def test_validate_output_rejects_empty_colors(tmp_path):
    folder = make_skillui_output(tmp_path)
    (folder / "tokens" / "colors.json").write_text("{}", encoding="utf-8")
    ok, reason = extract.validate_output(folder)
    assert ok is False
    assert "colors" in reason


def test_validate_output_accepts_default_shaped_folder_without_tokens(tmp_path):
    # DEFAULT-mode output has no tokens/ directory whatsoever -- only
    # DESIGN.md (plus CLAUDE.md/SKILL.md/screenshots/fonts). Confirmed live
    # against stripe.com and example.com. This must be accepted, not
    # refused with "no tokens/ directory in the extraction output" -- this
    # test fails against the pre-fix code that required tokens/colors.json
    # unconditionally.
    folder = make_default_only_output(tmp_path)
    ok, reason = extract.validate_output(folder)
    assert ok is True
    assert reason == ""


def test_validate_output_rejects_folder_with_neither_tokens_nor_design_md(tmp_path):
    folder = tmp_path / "empty-design"
    folder.mkdir()
    (folder / "unrelated.txt").write_text("nothing usable here\n", encoding="utf-8")
    ok, reason = extract.validate_output(folder)
    assert ok is False
    assert "tokens/colors.json" in reason
    assert "DESIGN.md" in reason


def test_summarize_reports_capabilities(tmp_path):
    summary = extract.summarize(make_skillui_output(tmp_path))
    assert summary["has"]["screens"] is True
    assert summary["has"]["animations"] is True
    assert "#5E6AD2" in summary["palette"]
    assert "Inter Variable" in summary["fonts"]


def test_summarize_default_mode_reports_no_ultra_artifacts(tmp_path):
    summary = extract.summarize(make_skillui_output(tmp_path, ultra=False))
    assert summary["has"]["screens"] is False
    assert summary["has"]["animations"] is False
    assert summary["has"]["tokens"] is True


def test_summarize_parses_palette_and_fonts_from_design_md_when_tokens_absent(tmp_path):
    # Real DEFAULT-mode output has no tokens/ at all; summarize must fall
    # back to parsing DESIGN.md's colour table and font-pairing line.
    folder = make_default_only_output(tmp_path)
    summary = extract.summarize(folder)
    assert summary["has"]["tokens"] is False
    assert summary["has"]["design_md"] is True
    assert "#FFFFFF" in summary["palette"]
    assert "#635BFF" in summary["palette"]
    assert "#0A2540" in summary["palette"]
    assert summary["fonts"] == ["Sohne", "GT America Mono"], (
        "must read real font-family declarations from the Typography Rules "
        "section, not the 'Fonts: N' summary line or unrelated CSS "
        "past the next heading"
    )


def test_summarize_font_parsing_ignores_the_metadata_summary_line(tmp_path):
    # A live run against stripe.com proved a naive "look for a line with
    # 'font' + a colon" parser matches DESIGN.md's own metadata banner
    # ("> Colors: 20 - Fonts: 2 - Components: 10") and reports the garbage
    # "2 - Components: 10" as a font name. This must never happen.
    folder = tmp_path / "metadata-trap-design"
    folder.mkdir()
    (folder / "DESIGN.md").write_text(
        "# example DESIGN.md\n\n"
        "> Colors: 20 - Fonts: 2 - Components: 10\n\n"
        "## 1. Visual Theme\n\nSome prose with no real font names.\n",
        encoding="utf-8",
    )
    summary = extract.summarize(folder)
    assert summary["fonts"] == []


def test_summarize_design_md_fallback_never_invents_values(tmp_path):
    folder = tmp_path / "sparse-design"
    folder.mkdir()
    (folder / "DESIGN.md").write_text("# Nothing parseable here\n", encoding="utf-8")
    summary = extract.summarize(folder)
    assert summary["palette"] == []
    assert summary["fonts"] == []


def test_summarize_parses_nested_w3c_design_tokens_colors(tmp_path):
    # Real ULTRA-mode tokens/colors.json is W3C design-tokens format,
    # nested several levels deep, e.g. core.background.value == "#ffffff".
    folder = tmp_path / "acme-design"
    (folder / "tokens").mkdir(parents=True)
    (folder / "tokens" / "colors.json").write_text(json.dumps({
        "$schema": "https://design-tokens.org/schema.json",
        "core": {
            "background": {
                "value": "#ffffff", "role": "background", "name": "header-border",
            },
            "accent": {
                "value": "#5921E8", "role": "accent", "name": "brand-violet",
            },
        },
    }), encoding="utf-8")
    (folder / "tokens" / "typography.json").write_text(
        json.dumps({"families": ["Figtree", "SF Mono"]}), encoding="utf-8"
    )
    (folder / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
    summary = extract.summarize(folder)
    assert "#ffffff" in summary["palette"]
    assert "#5921E8" in summary["palette"]
    assert "Figtree" in summary["fonts"]
    # Only real values from the nested tree, never the metadata strings.
    assert "background" not in summary["palette"]
    assert "header-border" not in summary["palette"]


def test_register_moves_folder_into_library(tmp_path, temp_library):
    folder = make_skillui_output(tmp_path)
    dest = extract.register(folder, "linear")
    assert dest == temp_library / "linear"
    assert (dest / "tokens" / "colors.json").is_file()
    assert not folder.exists()


def test_run_extraction_falls_back_and_records_default_mode(tmp_path, temp_library, monkeypatch):
    calls = []

    def fake_run(cmd, out):
        calls.append(cmd)
        if "ultra" in cmd:
            return 1, "playwright not found"
        make_skillui_output(out, ultra=False)
        return 0, ""

    monkeypatch.setattr(extract, "run_skillui", fake_run)
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")

    result = extract.run_extraction("https://linear.app", "url", name=None, mode="ultra", screens=10)

    assert len(calls) == 2, "should retry once in default mode"
    assert result["mode"] == "default", "must not claim ultra when ultra failed"
    assert library.read_manifest("linear")["mode"] == "default"
    assert library.read_manifest("linear")["skillui_version"] == "1.3.4"


def test_run_extraction_registers_real_default_mode_output(tmp_path, temp_library, monkeypatch):
    # This is the live-measured DEFAULT-mode shape: DESIGN.md and friends,
    # no tokens/ at all. Must now succeed end to end (defect 1).
    def fake_run(cmd, out):
        make_default_only_output(out, name="bad-design")
        return 0, ""

    monkeypatch.setattr(extract, "run_skillui", fake_run)
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")
    monkeypatch.setattr(extract, "cleanup_stray_global_skill", lambda *a, **k: None)

    manifest = extract.run_extraction("https://bad.app", "url", name=None, mode="default", screens=5)

    assert manifest["mode"] == "default"
    assert library.read_manifest("bad") is not None
    assert library.read_manifest("bad")["has"]["tokens"] is False
    assert library.read_manifest("bad")["has"]["design_md"] is True


def test_run_extraction_refuses_to_register_broken_ultra_output(tmp_path, temp_library, monkeypatch):
    def fake_run(cmd, out):
        folder = out / "bad-design"
        (folder / "tokens").mkdir(parents=True)
        (folder / "tokens" / "colors.json").write_text("{}", encoding="utf-8")
        return 0, ""

    monkeypatch.setattr(extract, "run_skillui", fake_run)
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")

    with pytest.raises(extract.ExtractionError, match="tokens"):
        extract.run_extraction("https://bad.app", "url", name=None, mode="default", screens=5)

    assert library.read_manifest("bad") is None, "no partial slot may be left behind"


def test_run_extraction_blocks_collision_without_force(temp_library, monkeypatch):
    library.write_manifest("linear", {"slug": "linear", "name": "Linear"})
    monkeypatch.setattr(extract, "run_skillui", lambda cmd, out: pytest.fail("must not run"))

    with pytest.raises(extract.ExtractionError, match="already registered"):
        extract.run_extraction("https://linear.app", "url", name=None, mode="ultra", screens=10)


# --- Windows "npx"/"npm" resolution regression tests -----------------------
#
# On Windows, subprocess.run(["npx", ...], shell=False) raises
# FileNotFoundError / WinError 2 because npx is really npx.cmd, and Windows
# CreateProcess does not do PATH extension resolution the way a shell does.
# extract.py must resolve the executable via shutil.which() before invoking
# it. These tests fail against the old bare-"npx"/"npm" code.

def test_resolve_executable_returns_which_result(monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: "C:\\fake\\npx.cmd")
    assert extract.resolve_executable("npx") == "C:\\fake\\npx.cmd"


def test_resolve_executable_falls_back_to_bare_name_when_not_found(monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: None)
    assert extract.resolve_executable("npx") == "npx"


def test_run_skillui_invokes_subprocess_with_resolved_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: "C:\\fake\\npx.cmd")

    captured = {}

    def fake_subprocess_run(argv, **kwargs):
        captured["argv"] = argv

        class FakeCompletedProcess:
            returncode = 0
            stderr = ""

        return FakeCompletedProcess()

    monkeypatch.setattr(extract.subprocess, "run", fake_subprocess_run)

    out = tmp_path / "out"
    cmd = ["npx", "-y", "skillui@latest", "--url", "https://example.com", "--out", str(out)]
    code, err = extract.run_skillui(cmd, out)

    assert code == 0
    assert captured["argv"][0] == "C:\\fake\\npx.cmd", (
        "run_skillui must invoke the resolved executable, not the bare 'npx'"
    )
    assert captured["argv"][0] != "npx"


def test_run_skillui_raises_clear_error_when_npx_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: None)

    out = tmp_path / "out"
    cmd = ["npx", "-y", "skillui@latest", "--url", "https://example.com", "--out", str(out)]

    with pytest.raises(extract.ExtractionError, match="(?i)npx"):
        extract.run_skillui(cmd, out)


def test_resolve_version_invokes_resolved_npm_executable(monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: "C:\\fake\\npm.cmd")

    captured = {}

    def fake_subprocess_run(argv, **kwargs):
        captured["argv"] = argv

        class FakeCompletedProcess:
            returncode = 0
            stdout = "1.2.3\n"

        return FakeCompletedProcess()

    monkeypatch.setattr(extract.subprocess, "run", fake_subprocess_run)

    version = extract.resolve_version()

    assert captured["argv"][0] == "C:\\fake\\npm.cmd"
    assert version == "1.2.3"


# --- UTF-8 decoding regression tests ----------------------------------------
#
# subprocess.run(..., text=True) without an explicit `encoding` decodes the
# child's stdout/stderr using the OS locale codec, which is cp1252 on
# Windows. skillui prints progress with emoji/box-drawing characters that
# are not representable in cp1252, so any real site's extraction output can
# crash with UnicodeDecodeError. encoding="utf-8", errors="replace" fixes
# this and guarantees we never crash on a child process's cosmetic output.

def test_run_skillui_passes_utf8_encoding_with_replace_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: "C:\\fake\\npx.cmd")

    captured = {}

    def fake_subprocess_run(argv, **kwargs):
        captured["kwargs"] = kwargs

        class FakeCompletedProcess:
            returncode = 0
            stderr = ""

        return FakeCompletedProcess()

    monkeypatch.setattr(extract.subprocess, "run", fake_subprocess_run)

    out = tmp_path / "out"
    cmd = ["npx", "-y", "skillui@latest", "--url", "https://stripe.com", "--out", str(out)]
    extract.run_skillui(cmd, out)

    assert captured["kwargs"]["encoding"] == "utf-8"
    assert captured["kwargs"]["errors"] == "replace"


def test_resolve_version_passes_utf8_encoding_with_replace_errors(monkeypatch):
    monkeypatch.setattr(extract.shutil, "which", lambda name: "C:\\fake\\npm.cmd")

    captured = {}

    def fake_subprocess_run(argv, **kwargs):
        captured["kwargs"] = kwargs

        class FakeCompletedProcess:
            returncode = 0
            stdout = "1.2.3\n"

        return FakeCompletedProcess()

    monkeypatch.setattr(extract.subprocess, "run", fake_subprocess_run)

    extract.resolve_version()

    assert captured["kwargs"]["encoding"] == "utf-8"
    assert captured["kwargs"]["errors"] == "replace"


# --- Stray global-skill cleanup regression tests ----------------------------
#
# skillui writes ~/.claude/skills/<name>-design/SKILL.md as a side effect of
# every run -- confirmed live twice, in both modes and regardless of --out.
# The installed skill is broken (points at references/DESIGN.md which it
# never ships) and, with ~120 skills registered, one extra always-on
# dead-pointer skill per extraction degrades triggering across all of them.
# run_extraction must detect and remove it, but only when it can positively
# identify the directory as skillui's own bare artifact.

def test_cleanup_removes_a_bare_skillui_artifact_it_created(tmp_path):
    skills_root = tmp_path / "skills"
    stray = skills_root / "stripe-design"
    stray.mkdir(parents=True)
    (stray / "SKILL.md").write_text("# Stripe design\n", encoding="utf-8")
    (stray / "CLAUDE.md").write_text("# notes\n", encoding="utf-8")

    extract.cleanup_stray_global_skill("stripe-design", skills_root=skills_root)

    assert not stray.exists()


def test_cleanup_refuses_a_directory_with_unexpected_content(tmp_path):
    skills_root = tmp_path / "skills"
    stray = skills_root / "linear-design"
    stray.mkdir(parents=True)
    (stray / "SKILL.md").write_text("# Linear design\n", encoding="utf-8")
    # Something skillui does not write -- e.g. a real skill someone hand-built
    # that happens to collide on name, or unexpected extra files.
    (stray / "notes.txt").write_text("do not delete me\n", encoding="utf-8")

    extract.cleanup_stray_global_skill("linear-design", skills_root=skills_root)

    assert stray.exists(), "must never delete a directory it can't positively identify"
    assert (stray / "notes.txt").is_file()


def test_cleanup_is_a_noop_when_nothing_was_installed(tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    # Should not raise even though skills_root has no matching subdirectory.
    extract.cleanup_stray_global_skill("nothing-here-design", skills_root=skills_root)


def test_cleanup_skipped_when_keep_installed_skill_is_set(tmp_path):
    skills_root = tmp_path / "skills"
    stray = skills_root / "stripe-design"
    stray.mkdir(parents=True)
    (stray / "SKILL.md").write_text("# Stripe design\n", encoding="utf-8")

    extract.cleanup_stray_global_skill("stripe-design", keep=True, skills_root=skills_root)

    assert stray.exists()


def test_run_extraction_cleans_up_stray_skill_before_registering(tmp_path, temp_library, monkeypatch):
    # Redirect stray_skill_path (not cleanup_stray_global_skill itself) so
    # run_extraction's real cleanup logic runs, just rooted at a fake
    # skills/ directory instead of the real ~/.claude/skills/.
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    monkeypatch.setattr(
        extract, "stray_skill_path",
        lambda folder_name, skills_root=None, _root=skills_root: _root / folder_name,
    )
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")

    seen = {}

    def fake_run(cmd, out):
        folder = make_skillui_output(out, name="linear-design", ultra=False)
        # Simulate skillui's side effect: it also wrote its own bare skill
        # into the global skills directory under this test's fake root.
        stray = skills_root / folder.name
        stray.mkdir(parents=True)
        (stray / "SKILL.md").write_text("# Linear design\n", encoding="utf-8")
        seen["stray"] = stray
        return 0, ""

    monkeypatch.setattr(extract, "run_skillui", fake_run)

    extract.run_extraction("https://linear.app", "url", name=None, mode="default", screens=5)

    assert not seen["stray"].exists(), "the stray skill skillui installed must be removed"


def test_run_extraction_keeps_stray_skill_when_flag_set(tmp_path, temp_library, monkeypatch):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    monkeypatch.setattr(
        extract, "stray_skill_path",
        lambda folder_name, skills_root=None, _root=skills_root: _root / folder_name,
    )
    monkeypatch.setattr(extract, "resolve_version", lambda: "1.3.4")

    seen = {}

    def fake_run(cmd, out):
        folder = make_skillui_output(out, name="linear-design", ultra=False)
        stray = skills_root / folder.name
        stray.mkdir(parents=True)
        (stray / "SKILL.md").write_text("# Linear design\n", encoding="utf-8")
        seen["stray"] = stray
        return 0, ""

    monkeypatch.setattr(extract, "run_skillui", fake_run)

    extract.run_extraction(
        "https://linear.app", "url", name=None, mode="default", screens=5,
        keep_installed_skill=True,
    )

    assert seen["stray"].exists(), "--keep-installed-skill must skip cleanup"
