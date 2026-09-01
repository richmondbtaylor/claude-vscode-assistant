# design-extract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one skill that extracts design systems from any website via SkillUI into a shared library, and wire nineteen existing design skills to read from that library without ever overriding Bishop AI brand.

**Architecture:** A `design-extract` skill owns extraction (`npx -y skillui@latest`) and registration into `~/.claude/design-systems/<slug>/`. A short, identical "Design Source" block is appended to nineteen `SKILL.md` files by a script, so the nineteen copies are generated rather than hand-written and can be reverted mechanically. The real precedence contract lives in one file (`references/consumption.md`) that all nineteen point at.

**Tech Stack:** Python 3.11+ run via `uv` with PEP 723 inline headers; pytest for tests; Node 18+ / `npx` for the SkillUI CLI; Playwright (already installed) for ultra mode.

**Spec:** `docs/superpowers/specs/2026-08-31-design-source-design.md`

## Global Constraints

- **Never run `git commit` without Rich's explicit go-ahead.** This is a standing rule and it overrides the usual commit-per-task convention. Every task below ends with a `git add` **stage** step. Commits are batched and authorized by Rich at the end.
- **Python runs through `uv` only.** Every script carries a PEP 723 header and is invoked as `uv run <script>`. Never `pip install`, never `python -m venv`, never `python -m pip`.
- **Tests run as** `uv run --with pytest pytest <path> -v` from `C:\Users\richm\.claude`.
- **Library root:** `~/.claude/design-systems/` (i.e. `C:\Users\richm\.claude\design-systems`).
- **Skill root:** `~/.claude/skills/design-extract/`.
- **Marker file:** `.design-system`, plain text, one line, format `<slug>  # activated YYYY-MM-DD`.
- **Connector edits are append-only.** Never modify an existing line, never touch frontmatter, never rewrite a `description`. Several target files carry a UTF-8 BOM; all connector file I/O is **binary** so BOMs and existing line endings survive untouched.
- **Precedence:** extracted systems are reference; Bishop AI brand is authority. Layers: (1) explicit instruction, (2) `branding-agent` colors/fonts/logo, (3) active design system layout/spacing/type-scale/components/motion, (4) style preset character, (5) `design-intel` generic recommendations, (6) skill defaults. The **only** escape hatch is the phrase `full <name> system`.
- **Skill name is `design-extract`, not `design-source`** (Ruling R8). A pre-existing skill named `design-sources` already occupies the adjacent name; a one-letter difference between two skills that both bridge external design material would misfire constantly. Every path is `~/.claude/skills/design-extract/`.
- **`design-sources` is a gate, not a precedence layer.** It vendors external design-craft repos and runs `check_design.py` before delivery. It sits outside the precedence ladder entirely: whatever supplies the values, `design-sources` still gates the output. Do not add it as a numbered layer.
- **`design-intel` amendment (approved 2026-08-31, post-spec):** `design-intel` bridges the same design skills to a generic recommendation database. Measured beats recommended, so it sits at layer 5 — below an active design system and below style presets, above skill defaults. It fills in whatever the extraction was silent on. This layer is **not** in the spec; it was added after `design-intel` surfaced during planning.
- **SkillUI version floor:** `skillui@latest`, Node 18+. Record the resolved version in every manifest.
- **Never report ultra output that was not produced.** If ultra fails and default mode runs, the manifest and the user-facing report must both say `default`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `skills/design-extract/scripts/library.py` | Slug rules, library paths, manifest read/write, system listing and fuzzy resolution. No I/O beyond the library. |
| `skills/design-extract/scripts/activate.py` | The `.design-system` marker: write, read, clear. Nothing else. |
| `skills/design-extract/scripts/extract.py` | Build the SkillUI command, run it, validate output, move into the library, write the manifest, append to the index. |
| `skills/design-extract/scripts/apply_connector.py` | Generate the connector block per skill group and append/revert it across the nineteen targets. Idempotent. |
| `skills/design-extract/references/consumption.md` | The precedence contract. Single source of truth referenced by all nineteen blocks. |
| `skills/design-extract/references/library.md` | Human-readable index of registered systems. |
| `skills/design-extract/SKILL.md` | Triggering, workflow, command reference. |
| `design-systems/README.md` | What the library is and how entries get there. |
| `skills/design-extract/tests/test_library.py` | Slug derivation, manifest round-trip, resolution. |
| `skills/design-extract/tests/test_activate.py` | Marker lifecycle and malformed-marker handling. |
| `skills/design-extract/tests/test_extract.py` | Command construction, ultra fallback, output validation, registration. Subprocess mocked — no network in tests. |
| `skills/design-extract/tests/test_apply_connector.py` | Block rendering, idempotency, BOM/line-ending preservation, revert fidelity. |

`library.py` is imported by `extract.py`, `activate.py`, and the tests. It is the only module with knowledge of the on-disk layout, so a layout change touches one file.

---

## Task 1: Library core — slugs, paths, manifests

**Files:**
- Create: `skills/design-extract/scripts/library.py`
- Test: `skills/design-extract/tests/test_library.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `LIBRARY_ROOT: Path`
  - `BORING_TLDS: frozenset[str]`
  - `slugify(text: str) -> str`
  - `slug_from_source(source: str, name: str | None = None) -> str`
  - `system_dir(slug: str) -> Path`
  - `read_manifest(slug: str) -> dict | None`
  - `write_manifest(slug: str, data: dict) -> Path`
  - `list_systems() -> list[dict]`
  - `resolve(query: str) -> str | None`

The slug rule from the spec, made deterministic: drop the scheme, drop a leading `www.`, split the host on dots, and drop the final label **only if** it is a "boring" TLD. `linear.app` -> `linear` (`app` is boring). `nothing.tech` -> `nothing-tech` (`tech` is not). `--name` always wins over derivation.

- [ ] **Step 1: Write the failing tests**

Create `skills/design-extract/tests/test_library.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_library.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'library'`

- [ ] **Step 3: Write the implementation**

Create `skills/design-extract/scripts/library.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""On-disk layout for the design-system library.

The only module that knows where systems live. Everything else goes through it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

LIBRARY_ROOT = Path.home() / ".claude" / "design-systems"

# Final host labels that read as noise rather than part of the brand name.
BORING_TLDS = frozenset(
    {"com", "io", "co", "org", "net", "app", "dev", "ai", "so", "xyz"}
)


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated, punctuation collapsed."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return cleaned.strip("-")


def slug_from_source(source: str, name: str | None = None) -> str:
    """Derive a library slug. An explicit name always wins."""
    if name:
        return slugify(name)

    host = re.sub(r"^[a-z]+://", "", source.strip().lower())
    host = host.split("/")[0].split("?")[0]
    host = re.sub(r"^www\.", "", host)
    host = host.split(":")[0]

    labels = [label for label in host.split(".") if label]
    if len(labels) > 1 and labels[-1] in BORING_TLDS:
        labels = labels[:-1]
    return slugify("-".join(labels))


def system_dir(slug: str) -> Path:
    return LIBRARY_ROOT / slug


def read_manifest(slug: str) -> dict | None:
    path = system_dir(slug) / "manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_manifest(slug: str, data: dict) -> Path:
    target = system_dir(slug)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "manifest.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def list_systems() -> list[dict]:
    """Every registered system, sorted by slug. Folders without a manifest are skipped."""
    if not LIBRARY_ROOT.is_dir():
        return []
    found = []
    for child in sorted(LIBRARY_ROOT.iterdir()):
        if not child.is_dir():
            continue
        manifest = read_manifest(child.name)
        if manifest is not None:
            found.append(manifest)
    return found


def resolve(query: str) -> str | None:
    """Map a user phrase to a registered slug via slug or display name."""
    needle = slugify(query)
    if not needle:
        return None
    for manifest in list_systems():
        slug = manifest.get("slug", "")
        if needle == slug or needle == slugify(manifest.get("name", "")):
            return slug
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_library.py -v`
Expected: PASS — 14 passed

- [ ] **Step 5: Stage (do not commit)**

```bash
git add skills/design-extract/scripts/library.py skills/design-extract/tests/test_library.py
```

---

## Task 2: The activation marker

**Files:**
- Create: `skills/design-extract/scripts/activate.py`
- Test: `skills/design-extract/tests/test_activate.py`

**Interfaces:**
- Consumes: `library.resolve`, `library.list_systems` from Task 1.
- Produces:
  - `MARKER_NAME: str` (`".design-system"`)
  - `write_marker(folder: Path, slug: str, today: str) -> Path`
  - `read_marker(folder: Path) -> str | None`
  - `clear_marker(folder: Path) -> bool`
  - CLI: `uv run activate.py <name>` / `--clear` / `--show`, all with optional `--folder PATH`

- [ ] **Step 1: Write the failing tests**

Create `skills/design-extract/tests/test_activate.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_activate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'activate'`

- [ ] **Step 3: Write the implementation**

Create `skills/design-extract/scripts/activate.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read, write, and clear the .design-system activation marker."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library

MARKER_NAME = ".design-system"


def write_marker(folder: Path, slug: str, today: str) -> Path:
    path = Path(folder) / MARKER_NAME
    path.write_text(f"{slug}  # activated {today}\n", encoding="utf-8")
    return path


def read_marker(folder: Path) -> str | None:
    path = Path(folder) / MARKER_NAME
    if not path.is_file():
        return None
    try:
        first = path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return None
    slug = first.split("#", 1)[0].strip()
    return slug or None


def clear_marker(folder: Path) -> bool:
    """Remove the marker. True if one was there, False if not."""
    path = Path(folder) / MARKER_NAME
    if not path.is_file():
        return False
    path.unlink()
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Activate a design system for a folder.")
    parser.add_argument("name", nargs="?", help="System slug or display name")
    parser.add_argument("--folder", default=".", help="Project folder (default: cwd)")
    parser.add_argument("--clear", action="store_true", help="Remove the marker")
    parser.add_argument("--show", action="store_true", help="Print the active slug")
    args = parser.parse_args(argv)

    folder = Path(args.folder)

    if args.clear:
        print("Cleared." if clear_marker(folder) else "No active design system.")
        return 0

    if args.show or not args.name:
        slug = read_marker(folder)
        print(slug if slug else "No active design system.")
        return 0

    slug = library.resolve(args.name)
    if slug is None:
        available = [s["slug"] for s in library.list_systems()]
        print(f"'{args.name}' is not in the library.")
        print(f"Available: {', '.join(available) if available else '(none yet)'}")
        return 1

    today = datetime.date.today().isoformat()
    write_marker(folder, slug, today)
    print(f"Activated '{slug}' in {folder.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_activate.py -v`
Expected: PASS — 9 passed

- [ ] **Step 5: Stage (do not commit)**

```bash
git add skills/design-extract/scripts/activate.py skills/design-extract/tests/test_activate.py
```

---

## Task 3: Extraction and registration

**Files:**
- Create: `skills/design-extract/scripts/extract.py`
- Test: `skills/design-extract/tests/test_extract.py`

**Interfaces:**
- Consumes: `library.slug_from_source`, `library.system_dir`, `library.write_manifest`, `library.read_manifest` from Task 1.
- Produces:
  - `build_command(source: str, source_type: str, out: Path, name: str | None, mode: str, screens: int) -> list[str]`
  - `find_output_dir(out: Path) -> Path | None`
  - `validate_output(folder: Path) -> tuple[bool, str]`
  - `summarize(folder: Path) -> dict` — returns `{"palette": [...], "fonts": [...], "has": {...}}`
  - `build_manifest(slug, name, source, source_type, mode, screens, version, folder) -> dict`
  - `register(folder: Path, slug: str) -> Path`
  - `append_index_line(manifest: dict) -> None`
  - CLI: `uv run extract.py --url URL [--name N] [--mode ultra|default] [--screens N] [--force]`

The ultra fallback is the behavior most likely to be misreported, so it is tested directly: a failing ultra run must produce a manifest saying `default`.

- [ ] **Step 1: Write the failing tests**

Create `skills/design-extract/tests/test_extract.py`:

```python
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


def test_validate_output_rejects_missing_tokens_dir(tmp_path):
    folder = tmp_path / "bare-design"
    folder.mkdir()
    (folder / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
    ok, reason = extract.validate_output(folder)
    assert ok is False
    assert "tokens" in reason


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


def test_run_extraction_refuses_to_register_tokenless_output(tmp_path, temp_library, monkeypatch):
    def fake_run(cmd, out):
        folder = out / "bad-design"
        folder.mkdir(parents=True)
        (folder / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_extract.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extract'`

- [ ] **Step 3: Write the implementation**

Create `skills/design-extract/scripts/extract.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run SkillUI and register its output in the design-system library."""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library

# Module-level so tests can redirect it. Without this, unit tests that call
# run_extraction would append fake entries to the real library index.
INDEX_PATH = Path(__file__).resolve().parents[1] / "references" / "library.md"

REFERENCE_FILES = {
    "animations": "ANIMATIONS.md",
    "interactions": "INTERACTIONS.md",
    "layout": "LAYOUT.md",
    "components": "COMPONENTS.md",
}


class ExtractionError(RuntimeError):
    """Extraction failed in a way that must leave the library untouched."""


def build_command(
    source: str, source_type: str, out: Path, name: str | None, mode: str, screens: int
) -> list[str]:
    flag = {"url": "--url", "dir": "--dir", "repo": "--repo"}[source_type]
    cmd = ["npx", "-y", "skillui@latest", flag, source, "--out", str(out)]
    if name:
        cmd += ["--name", name]
    if mode == "ultra":
        cmd += ["--mode", "ultra", "--screens", str(screens)]
    return cmd


def run_skillui(cmd: list[str], out: Path) -> tuple[int, str]:
    """Execute skillui. Returns (returncode, stderr). Seam for tests."""
    out.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    return proc.returncode, proc.stderr


def resolve_version() -> str:
    """Ask npm which skillui version resolved. Seam for tests."""
    try:
        proc = subprocess.run(
            ["npm", "view", "skillui", "version"],
            capture_output=True, text=True, shell=False, timeout=60,
        )
        return proc.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def find_output_dir(out: Path) -> Path | None:
    """SkillUI writes a single <name>-design/ folder under --out."""
    candidates = [c for c in sorted(out.iterdir()) if c.is_dir()] if out.is_dir() else []
    if not candidates:
        return None
    for c in candidates:
        if (c / "DESIGN.md").is_file() or (c / "tokens").is_dir():
            return c
    return candidates[0]


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def validate_output(folder: Path) -> tuple[bool, str]:
    """A slot with no tokens is worse than no slot. Reject it here."""
    if not (folder / "tokens").is_dir():
        return False, "no tokens/ directory in the extraction output"
    colors = _load_json(folder / "tokens" / "colors.json")
    if not colors:
        return False, "tokens/colors.json is missing or empty"
    return True, ""


def _flatten_colors(data: dict) -> list[str]:
    found = []
    for value in data.values():
        if isinstance(value, str) and value.strip().startswith("#"):
            found.append(value.strip())
        elif isinstance(value, dict):
            found.extend(_flatten_colors(value))
        elif isinstance(value, list):
            found.extend(v.strip() for v in value if isinstance(v, str) and v.strip().startswith("#"))
    seen, unique = set(), []
    for c in found:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)
    return unique


def _flatten_fonts(data: dict) -> list[str]:
    families = data.get("families")
    if isinstance(families, list):
        return [f for f in families if isinstance(f, str)]
    return [v for v in data.values() if isinstance(v, str)]


def summarize(folder: Path) -> dict:
    colors = _load_json(folder / "tokens" / "colors.json")
    typography = _load_json(folder / "tokens" / "typography.json")
    screens = folder / "screens"
    refs = folder / "references"
    has = {
        "tokens": (folder / "tokens").is_dir() and bool(colors),
        "screens": screens.is_dir() and any(screens.rglob("*.png")),
    }
    for key, filename in REFERENCE_FILES.items():
        has[key] = (refs / filename).is_file()
    return {
        "palette": _flatten_colors(colors)[:8],
        "fonts": _flatten_fonts(typography)[:6],
        "has": has,
    }


def build_manifest(
    slug: str, name: str, source: str, source_type: str,
    mode: str, screens: int, version: str, folder: Path,
) -> dict:
    summary = summarize(folder)
    return {
        "slug": slug,
        "name": name,
        "source": source,
        "source_type": source_type,
        "mode": mode,
        "extracted": datetime.date.today().isoformat(),
        "skillui_version": version,
        "screens": screens if mode == "ultra" else 0,
        "has": summary["has"],
        "palette": summary["palette"],
        "fonts": summary["fonts"],
    }


def register(folder: Path, slug: str) -> Path:
    dest = library.system_dir(slug)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(dest))
    return dest


def append_index_line(manifest: dict) -> None:
    index = INDEX_PATH
    index.parent.mkdir(parents=True, exist_ok=True)
    if not index.is_file():
        index.write_text(
            "# Registered Design Systems\n\n"
            "One line per system. Written by `extract.py`.\n\n",
            encoding="utf-8",
        )
    palette = " ".join(manifest.get("palette", [])[:3])
    line = (
        f"- **{manifest['name']}** (`{manifest['slug']}`) — {manifest['source']} — "
        f"{manifest['mode']} mode, {manifest['extracted']} — {palette}\n"
    )
    existing = index.read_text(encoding="utf-8")
    if f"(`{manifest['slug']}`)" in existing:
        kept = [ln for ln in existing.splitlines(keepends=True)
                if f"(`{manifest['slug']}`)" not in ln]
        existing = "".join(kept)
    index.write_text(existing.rstrip("\n") + "\n" + line, encoding="utf-8")


def run_extraction(
    source: str, source_type: str, name: str | None,
    mode: str, screens: int, force: bool = False,
) -> dict:
    slug = library.slug_from_source(source, name)
    if library.read_manifest(slug) is not None and not force:
        raise ExtractionError(
            f"'{slug}' is already registered. Re-run with --force to replace it."
        )

    display_name = name or slug.replace("-", " ").title()
    version = resolve_version()

    with tempfile.TemporaryDirectory(prefix="skillui-") as tmp:
        out = Path(tmp)
        attempted = mode
        code, err = run_skillui(build_command(source, source_type, out, name, mode, screens), out)

        if code != 0 and mode == "ultra":
            print("Ultra mode failed; retrying in default mode.")
            print(f"  reason: {err.strip()[:300]}")
            attempted = "default"
            for child in list(out.iterdir()):
                shutil.rmtree(child, ignore_errors=True) if child.is_dir() else child.unlink()
            code, err = run_skillui(
                build_command(source, source_type, out, name, "default", screens), out
            )

        if code != 0:
            raise ExtractionError(f"skillui failed ({code}): {err.strip()[:500]}")

        folder = find_output_dir(out)
        if folder is None:
            raise ExtractionError("skillui produced no output folder")

        ok, reason = validate_output(folder)
        if not ok:
            raise ExtractionError(f"refusing to register: {reason}")

        # If ultra was requested and ran, but produced no screenshots, say default.
        summary = summarize(folder)
        if attempted == "ultra" and not summary["has"]["screens"]:
            print("Ultra ran but produced no screenshots; recording mode as default.")
            attempted = "default"

        manifest = build_manifest(
            slug, display_name, source, source_type, attempted, screens, version, folder
        )
        register(folder, slug)

    library.write_manifest(slug, manifest)
    append_index_line(manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a design system with SkillUI.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url")
    group.add_argument("--dir")
    group.add_argument("--repo")
    parser.add_argument("--name")
    parser.add_argument("--mode", choices=["ultra", "default"], default="ultra")
    parser.add_argument("--screens", type=int, default=10)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    source_type = "url" if args.url else ("dir" if args.dir else "repo")
    source = args.url or args.dir or args.repo

    try:
        manifest = run_extraction(
            source, source_type, args.name, args.mode, args.screens, args.force
        )
    except ExtractionError as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"\nRegistered '{manifest['slug']}' ({manifest['name']})")
    print(f"  mode:    {manifest['mode']}   skillui {manifest['skillui_version']}")
    print(f"  palette: {' '.join(manifest['palette'][:5]) or '(none)'}")
    print(f"  fonts:   {', '.join(manifest['fonts'][:4]) or '(none)'}")
    present = [k for k, v in manifest["has"].items() if v]
    absent = [k for k, v in manifest["has"].items() if not v]
    print(f"  has:     {', '.join(present) or '(nothing)'}")
    print(f"  missing: {', '.join(absent) or '(nothing)'}")
    print(f"  path:    {library.system_dir(manifest['slug'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_extract.py -v`
Expected: PASS — 15 passed

- [ ] **Step 5: Stage (do not commit)**

```bash
git add skills/design-extract/scripts/extract.py skills/design-extract/tests/test_extract.py
```

---

## Task 4: The consumption contract

**Files:**
- Create: `skills/design-extract/references/consumption.md`
- Create: `design-systems/README.md`
- Create: `skills/design-extract/references/library.md`

**Interfaces:**
- Consumes: nothing (prose).
- Produces: `references/consumption.md`, the file every connector block points at. Task 5's block text must reference this exact path.

This task is prose, so the gate is a read-through against the spec's precedence table rather than a test run.

- [ ] **Step 1: Write the contract**

Create `skills/design-extract/references/consumption.md`:

```markdown
# Design Source — Consumption Contract

The rule in one line: **extracted design systems are reference; Bishop AI brand is authority.**

## Precedence

| Layer | Source | Wins on |
|---|---|---|
| 1 (highest) | Explicit instruction in the request | everything |
| 2 | `branding-agent` | colors, fonts, logo treatment on any Bishop AI or Prompt Anything deliverable |
| 3 | Active design system | layout, spacing, type scale, components, motion, interactions |
| 4 | Style preset (`brutalist-skill`, `minimalist-skill`) | aesthetic character where 2 and 3 are silent |
| 5 | `design-intel` | generic layout, spacing, UX, accessibility, and font-pairing recommendations where 2-4 are silent |
| 6 (lowest) | Skill defaults | everything else |

Separately, `design-sources` is a **gate, not a layer**. It vendors external design-craft
repos and runs a deterministic check before delivery. It applies no matter which layer
supplied the values, so it has no row in this table — run it before shipping, as it asks.

`design-intel` and `design-extract` are siblings, not rivals. `design-extract` supplies
**measured** values from one specific site; `design-intel` supplies **recommended**
values from a general database. Measured beats recommended on any decision both cover.
Where the extraction is silent — accessibility rules, chart selection, responsive
breakpoints — `design-intel` is the answer and should be consulted normally.

## The one escape hatch

The phrase **"full \<name\> system"** promotes the active system above `branding-agent`
for that single deliverable. Nothing else does. Not "use Linear's colors", not "make it
look like Linear" — only "full linear system".

If a request seems to want brand override but does not use that phrase, follow the table
and say in one line which colors and fonts you used and why.

## Borrow / keep

**BORROW from the active system:** layout structure, spacing grid, type scale ratios,
component patterns, border radii, elevation, motion durations, easing curves,
interaction states.

**KEEP from `branding-agent`:** brand colors, font families, logo treatment.

Type scale is a ratio, not a font. Borrowing Linear's 1.25 scale while keeping the Bishop
typeface is the intended outcome, not a compromise.

## Resolving the active system

1. A system named in the request — match against `slug` or `name` in each
   `~/.claude/design-systems/*/manifest.json`.
2. Otherwise, a `.design-system` marker file in the working folder. Format:
   `<slug>  # activated YYYY-MM-DD`. Read the first token before any `#`.
3. Otherwise, none is active — proceed exactly as the skill would have before.

A named system beats the marker for that request and does not overwrite it.

## What to read, by medium

| You are producing | Read |
|---|---|
| HTML / CSS / code | `tokens/colors.json`, `tokens/typography.json`, `tokens/spacing.json`, `fonts/` |
| Images, decks, graphics | `screens/`, `references/VISUAL_GUIDE.md`, plus `tokens/` for palette bounds |
| Layout or component structure | `references/LAYOUT.md`, `references/COMPONENTS.md` |
| Motion, transitions, diagrams | `references/ANIMATIONS.md`, `references/INTERACTIONS.md` |
| Anything, for orientation | `DESIGN.md` |

Use token values exactly as written. Do not round them, re-derive them, or substitute a
"close enough" value. The entire point is that these are measured rather than guessed.

## When files are absent

`manifest.json` carries a `has` map (`tokens`, `screens`, `animations`, `interactions`,
`layout`, `components`). Check it before relying on a file. Default-mode extractions have
no screenshots, animations, or interaction diffs.

If a system is named but not registered, say so and list what is available. Do not fall
back to invented values silently.
```

- [ ] **Step 2: Write the library README**

Create `design-systems/README.md`:

```markdown
# Design Systems Library

Extracted design systems, one folder per system. Written by
`~/.claude/skills/design-extract/scripts/extract.py`, read by every design skill
carrying a "Design Source" block.

## Layout

```
<slug>/
  manifest.json    slug, name, source, mode, date, palette, fonts, has-map
  DESIGN.md        full token reference
  tokens/          colors.json, spacing.json, typography.json
  references/      ANIMATIONS, LAYOUT, COMPONENTS, INTERACTIONS, VISUAL_GUIDE
  screens/         scroll/, pages/, sections/   (ultra mode only)
  fonts/           bundled woff2
```

## Adding one

```bash
uv run ~/.claude/skills/design-extract/scripts/extract.py --url https://linear.app
```

## Rules

- A folder without a `manifest.json` is invisible to the library and is ignored.
- Extractions with no usable color tokens are refused rather than registered.
- Nothing here overrides Bishop AI brand. See
  `~/.claude/skills/design-extract/references/consumption.md`.
```

- [ ] **Step 3: Seed the index — only if it does not already exist**

`extract.py` creates this file on first extraction. If Task 3 already produced one,
leave it alone; only create it when absent. Never overwrite a populated index.

Create `skills/design-extract/references/library.md`:

```markdown
# Registered Design Systems

One line per system. Written by `extract.py`.

```

- [ ] **Step 4: Verify against the spec**

Read `docs/superpowers/specs/2026-08-31-design-source-design.md` sections "Component 4:
precedence" and "Component 3: the connector block". Confirm line by line:
- The five layers appear in the same order with the same owners.
- The escape hatch is `full <name> system` and nothing else.
- The borrow list and keep list match.
- The per-medium file map matches the four rows of the spec's medium table.

Fix any divergence in `consumption.md`, not in the spec.

- [ ] **Step 5: Stage (do not commit)**

```bash
git add skills/design-extract/references/ design-systems/README.md
```

---

## Task 5: The connector applicator

**Files:**
- Create: `skills/design-extract/scripts/apply_connector.py`
- Test: `skills/design-extract/tests/test_apply_connector.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `SENTINEL_START: bytes`, `SENTINEL_END: bytes`
  - `GROUPS: dict[str, tuple[str, ...]]` — group name -> skill folder names
  - `TAILS: dict[str, str]` — group name -> medium-specific line
  - `group_of(skill: str) -> str | None`
  - `render_block(skill: str) -> str`
  - `apply_to_file(path: Path) -> str` — returns `"applied"`, `"already"`, or `"skipped"`
  - `revert_file(path: Path) -> bool`
  - CLI: `uv run apply_connector.py [--dry-run] [--revert] [--only SKILL ...]`

All file I/O is **binary**, so the UTF-8 BOMs on `branding-agent/SKILL.md` and
`visual-code/SKILL.md` and any CRLF line endings survive byte-for-byte.

- [ ] **Step 1: Write the failing tests**

Create `skills/design-extract/tests/test_apply_connector.py`:

```python
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
    assert "## Design Source" in block
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_apply_connector.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apply_connector'`

- [ ] **Step 3: Write the implementation**

Create `skills/design-extract/scripts/apply_connector.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Append (or remove) the Design Source connector block across the design skills.

Binary I/O throughout so BOMs and CRLF endings survive untouched. Append-only:
no existing byte is ever modified.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path.home() / ".claude" / "skills"

# Two start sentinels so revert is byte-lossless. The "nl" variant records that we
# had to add a newline before the block because the file did not end with one.
SENTINEL_START = b"<!-- design-extract:connector v1 -->"
SENTINEL_START_NL = b"<!-- design-extract:connector v1 nl -->"
SENTINEL_END = b"<!-- /design-extract:connector v1 -->"

GROUPS: dict[str, tuple[str, ...]] = {
    "web": (
        "visual-code", "image-to-code-skill", "imagegen-frontend-web",
        "email-html-gen", "course-builder", "codecraft",
    ),
    "graphics": (
        "branding-agent", "citadel", "carousel",
        "infographic-generator", "slideforge", "presentation-impact-enhancer",
    ),
    "preset": ("brutalist-skill", "minimalist-skill"),
    "motion": (
        "hyperframes", "claude-design-hyperframes", "gsap",
        "excalidraw-skill", "reelforge",
    ),
}

TAILS: dict[str, str] = {
    "web": (
        "**This skill emits code.** Read `tokens/colors.json`, `tokens/typography.json`, "
        "`tokens/spacing.json`, and `fonts/`. Use those values exactly as written — do not "
        "round them or substitute a close-enough value."
    ),
    "graphics": (
        "**This skill emits images or decks.** Read `screens/` and "
        "`references/VISUAL_GUIDE.md` to describe the visual language in prompts, and "
        "`tokens/` for palette bounds."
    ),
    "preset": (
        "**This skill carries its own aesthetic.** The extracted system supplies structure "
        "— read `references/LAYOUT.md` and `references/COMPONENTS.md`. This preset supplies "
        "aesthetic character wherever the extracted system is silent."
    ),
    "motion": (
        "**This skill emits motion.** Read `references/ANIMATIONS.md` and "
        "`references/INTERACTIONS.md` for real keyframes, durations, and easing curves "
        "rather than inventing timings."
    ),
}

STANDARD_BLOCK = """## Design Extract

Before choosing colors, type, spacing, or motion, check for an active design system:

1. A system named in the request ("in the linear system", "build this like Stripe"), or a
   `.design-system` marker file in the working folder.
2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
   motion, easing, interaction states.
   **KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families, logo
   treatment.
   Override only when the request explicitly says "full <name> system".
4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Measured beats recommended: where an active system covers a decision, it outranks
`design-intel`. Where it is silent — accessibility, chart choice, breakpoints —
`design-intel` is still the answer.

{tail}

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
"""

# branding-agent is layer 2. It is told it is the authority, not told to defer —
# otherwise the two blocks contradict each other.
BRANDING_BLOCK = """## Design Extract

This skill is the **brand authority**. Extracted design systems in
`~/.claude/design-systems/` sit *beneath* it and never override it.

1. Bishop AI / Prompt Anything colors, font families, and logo treatment defined here win
   over any extracted system, on every Bishop-branded deliverable.
2. An active design system may still contribute layout, spacing grid, type scale ratios,
   component patterns, motion, and interaction states. Borrowing a 1.25 type scale while
   keeping the Bishop typeface is the intended outcome, not a compromise.
3. The single exception is the explicit phrase "full <name> system" in the request, which
   promotes that system above this skill for one deliverable. Nothing else does.
4. {tail}

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
"""


def group_of(skill: str) -> str | None:
    for name, members in GROUPS.items():
        if skill in members:
            return name
    return None


def render_block(skill: str) -> str:
    group = group_of(skill)
    if group is None:
        raise KeyError(f"{skill} is not a wired design skill")
    template = BRANDING_BLOCK if skill == "branding-agent" else STANDARD_BLOCK
    return template.format(tail=TAILS[group])


def _find_start(content: bytes) -> tuple[int, bool]:
    """Locate the block. Returns (offset, added_newline). offset -1 if absent."""
    at_nl = content.find(SENTINEL_START_NL)
    if at_nl != -1:
        return at_nl, True
    return content.find(SENTINEL_START), False


def apply_to_file(path: Path) -> str:
    """Append the block. Returns 'applied', 'already', or 'skipped'."""
    skill = path.parent.name
    if group_of(skill) is None:
        return "skipped"

    current = path.read_bytes()
    if _find_start(current)[0] != -1:
        return "already"

    # Everything we add lives at or after the sentinel, except a single newline
    # when the file lacked a trailing one — and that case uses the "nl" sentinel
    # so revert knows to drop exactly one byte.
    needs_nl = not current.endswith(b"\n")
    sentinel = SENTINEL_START_NL if needs_nl else SENTINEL_START
    addition = (
        (b"\n" if needs_nl else b"")
        + sentinel + b"\n\n---\n\n"
        + render_block(skill).encode("utf-8")
        + SENTINEL_END + b"\n"
    )
    with path.open("ab") as handle:
        handle.write(addition)
    return "applied"


def revert_file(path: Path) -> bool:
    """Remove the block byte-losslessly. True if one was removed."""
    current = path.read_bytes()
    start, added_newline = _find_start(current)
    if start == -1:
        return False
    end = current.find(SENTINEL_END, start)
    if end == -1:
        return False
    end += len(SENTINEL_END)
    if current[end:end + 1] == b"\n":
        end += 1

    head = current[:start]
    if added_newline and head.endswith(b"\n"):
        head = head[:-1]
    path.write_bytes(head + current[end:])
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply the Design Source connector block.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--revert", action="store_true")
    parser.add_argument("--only", nargs="*", default=None, help="Limit to these skills")
    args = parser.parse_args(argv)

    targets = args.only or [s for group in GROUPS.values() for s in group]
    counts: dict[str, int] = {}

    for skill in targets:
        path = SKILLS_ROOT / skill / "SKILL.md"
        if not path.is_file():
            print(f"  MISSING  {skill}/SKILL.md")
            counts["missing"] = counts.get("missing", 0) + 1
            continue

        if args.dry_run:
            has = _find_start(path.read_bytes())[0] != -1
            state = "already" if has else "would-apply"
            print(f"  {state:<12} {skill}")
            counts[state] = counts.get(state, 0) + 1
            continue

        if args.revert:
            removed = revert_file(path)
            state = "reverted" if removed else "no-block"
        else:
            state = apply_to_file(path)
        print(f"  {state:<12} {skill}")
        counts[state] = counts.get(state, 0) + 1

    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest pytest skills/design-extract/tests/test_apply_connector.py -v`
Expected: PASS — 14 passed

- [ ] **Step 5: Run the whole suite**

Run: `uv run --with pytest pytest skills/design-extract/tests/ -v`
Expected: PASS — 52 passed

- [ ] **Step 6: Stage (do not commit)**

```bash
git add skills/design-extract/scripts/apply_connector.py skills/design-extract/tests/test_apply_connector.py
```

---

## Task 6: The design-extract SKILL.md

**Files:**
- Create: `skills/design-extract/SKILL.md`

**Interfaces:**
- Consumes: the CLI surfaces of `extract.py`, `activate.py`, `apply_connector.py`.
- Produces: the skill Claude loads. Command examples here must match the real argparse
  flags from Tasks 2, 3, and 5 exactly.

- [ ] **Step 1: Write the skill file**

Create `skills/design-extract/SKILL.md`:

````markdown
---
name: design-extract
description: Extracts a real design system from any website, git repo, or local project using SkillUI, stores it in a reusable library, and makes it available to every design skill. Use this skill whenever the user wants to build something in the visual language of a specific site — "extract the design system from linear.app", "pull in Stripe's design", "build this like Notion", "use the linear system", "make it look like <site>" — or when they ask what design systems are available, want to activate one for a project, or say "skillui". Also use it before any website, branding, deck, graphic, or motion work where a reference site is named, so the build works from measured tokens rather than guessed ones.
---

# Design Extract

Extract real design systems. Store them once. Let every design skill read them.

Extraction is [SkillUI](https://github.com/amaancoderx/npxskillui) — pure static
analysis, no AI, no API keys. Ultra mode adds Playwright screenshots, animation
detection, and interaction diffs.

## The rule that governs everything

**Extracted systems are reference. Bishop AI brand is authority.**

Full precedence table, borrow/keep lists, and per-medium file map:
`references/consumption.md`. Read it before applying a system to a deliverable.

## Extract

```bash
uv run ~/.claude/skills/design-extract/scripts/extract.py --url https://linear.app
```

Ultra mode with ten pages is the default. Other sources:

```bash
# local project
uv run .../extract.py --dir ./my-app --name "MyApp"
# public git repo
uv run .../extract.py --repo https://github.com/org/repo --name "Repo"
# fast, static only — no screenshots, animations, or interaction diffs
uv run .../extract.py --url https://stripe.com --mode default
# replace an existing entry
uv run .../extract.py --url https://linear.app --force
```

If ultra fails (usually Playwright), it retries once in default mode and records
`"mode": "default"`. Report the mode that actually ran. Never describe screenshots or
animation data that was not produced.

Extractions with no usable color tokens are refused, not registered. A slot the
connector reads and finds empty is worse than no slot.

## List and activate

```bash
# what is registered
cat ~/.claude/skills/design-extract/references/library.md

# make one sticky for a project folder
uv run ~/.claude/skills/design-extract/scripts/activate.py linear --folder ./my-project
uv run ~/.claude/skills/design-extract/scripts/activate.py --show
uv run ~/.claude/skills/design-extract/scripts/activate.py --clear
```

Naming a system in a request beats the marker for that request and leaves the marker
alone.

## Wire the design skills

Nineteen skills carry a "Design Source" block. It is generated, never hand-edited:

```bash
uv run ~/.claude/skills/design-extract/scripts/apply_connector.py --dry-run
uv run ~/.claude/skills/design-extract/scripts/apply_connector.py
uv run ~/.claude/skills/design-extract/scripts/apply_connector.py --revert
```

Append-only and idempotent. Re-run it after editing the block text in
`apply_connector.py`: `--revert` then apply.

| Group | Skills |
|---|---|
| Web/code | visual-code, image-to-code-skill, imagegen-frontend-web, email-html-gen, course-builder, codecraft |
| Brand/graphics | branding-agent (inverted), citadel, carousel, infographic-generator, slideforge, presentation-impact-enhancer |
| Style presets | brutalist-skill, minimalist-skill |
| Motion/diagram | hyperframes, claude-design-hyperframes, gsap, excalidraw-skill, reelforge |

## Library layout

```
~/.claude/design-systems/<slug>/
  manifest.json    slug, name, source, mode, date, palette, fonts, has-map
  DESIGN.md  tokens/  references/  screens/  fonts/
```

Check `manifest.json`'s `has` map before relying on a file. Default-mode entries have no
`screens/`, `ANIMATIONS.md`, or `INTERACTIONS.md`.

## Tests

```bash
uv run --with pytest pytest ~/.claude/skills/design-extract/tests/ -v
```

## Notes

- `skillui` is a young single-maintainer package invoked through `npx -y`. The resolved
  version is recorded in every manifest so a bad release is traceable.
- Ultra mode needs Playwright, which is already installed on this machine.
````

- [ ] **Step 2: Verify the documented flags match the code**

Run each documented command with `--help` and confirm every flag exists:

```bash
uv run skills/design-extract/scripts/extract.py --help
uv run skills/design-extract/scripts/activate.py --help
uv run skills/design-extract/scripts/apply_connector.py --help
```

Expected: `--url/--dir/--repo/--name/--mode/--screens/--force` on extract;
`name/--folder/--clear/--show` on activate; `--dry-run/--revert/--only` on apply_connector.
Fix `SKILL.md` if anything diverges.

- [ ] **Step 3: Stage (do not commit)**

```bash
git add skills/design-extract/SKILL.md
```

---

## Task 7: Apply the connector to all nineteen skills

**Files:**
- Modify: `skills/{visual-code,image-to-code-skill,imagegen-frontend-web,email-html-gen,course-builder,codecraft}/SKILL.md`
- Modify: `skills/{branding-agent,citadel,carousel,infographic-generator,slideforge,presentation-impact-enhancer}/SKILL.md`
- Modify: `skills/{brutalist-skill,minimalist-skill}/SKILL.md`
- Modify: `skills/{hyperframes,claude-design-hyperframes,gsap,excalidraw-skill,reelforge}/SKILL.md`

**Interfaces:**
- Consumes: `apply_connector.main` from Task 5.
- Produces: nineteen wired skills. No new symbols.

- [ ] **Step 1: Record byte-exact baselines**

```bash
cd ~/.claude
uv run --with pytest python - <<'PY'
import hashlib, json
from pathlib import Path
import sys
sys.path.insert(0, "skills/design-extract/scripts")
import apply_connector as ac
sums = {}
for skill in [s for g in ac.GROUPS.values() for s in g]:
    p = Path("skills") / skill / "SKILL.md"
    sums[skill] = hashlib.sha256(p.read_bytes()).hexdigest()
Path("skills/design-extract/tests/baseline.json").write_text(json.dumps(sums, indent=2))
print(f"baselined {len(sums)} files")
PY
```

Expected: `baselined 19 files`

- [ ] **Step 2: Dry run**

Run: `uv run skills/design-extract/scripts/apply_connector.py --dry-run`
Expected: nineteen `would-apply` lines, zero `MISSING`. If any file is missing, stop and
resolve the path before writing anything.

- [ ] **Step 3: Apply**

Run: `uv run skills/design-extract/scripts/apply_connector.py`
Expected: nineteen `applied` lines.

- [ ] **Step 4: Prove the edits are append-only**

```bash
git diff --stat -- skills/
git diff -- skills/branding-agent/SKILL.md
```

Expected: every file shows insertions only, `0 deletions`. Read the `branding-agent`
diff in full and confirm it received the **inverted** block naming itself the authority,
not the standard deferring block.

- [ ] **Step 5: Prove revert is byte-exact**

```bash
cd ~/.claude
uv run skills/design-extract/scripts/apply_connector.py --revert
uv run --with pytest python - <<'PY'
import hashlib, json
from pathlib import Path
sums = json.loads(Path("skills/design-extract/tests/baseline.json").read_text())
bad = [s for s, h in sums.items()
       if hashlib.sha256((Path("skills") / s / "SKILL.md").read_bytes()).hexdigest() != h]
print("MISMATCH:", bad) if bad else print("all 19 restored byte-for-byte")
PY
uv run skills/design-extract/scripts/apply_connector.py
```

Expected: `all 19 restored byte-for-byte`, then nineteen `applied` lines again. If any
file mismatches, the revert path is wrong — fix `revert_file` and repeat from Step 1.

- [ ] **Step 6: Non-regression check on three skills**

With **no** design system active, run one skill from three different groups and confirm
output is indistinguishable from pre-edit behavior:
- `visual-code` — ask for a small landing page. Confirm it does not mention or look for a
  design system.
- `citadel` — ask for a thumbnail. Confirm normal Bishop-brand behavior.
- `excalidraw-skill` — ask for a small diagram. Confirm normal behavior.

Record the result of each in the task notes. Any behavior change here means the block is
adding default behavior it should not; fix the block text and re-apply.

- [ ] **Step 7: Stage (do not commit)**

```bash
git add skills/*/SKILL.md skills/design-extract/tests/baseline.json
```

---

## Task 8: Live end-to-end verification

**Files:**
- Modify: none. This task only observes.

**Interfaces:**
- Consumes: everything built in Tasks 1-7.
- Produces: a verification record. Nothing is reported working until seen working.

- [ ] **Step 1: Real extraction**

Run: `uv run skills/design-extract/scripts/extract.py --url https://linear.app --screens 10`
Expected: `Registered 'linear' (Linear)`, mode `ultra`, a non-empty palette and font list.

If Rich prefers a different site, use his. The site does not matter; observing a real
extraction does.

- [ ] **Step 2: Inspect the slot**

```bash
cat ~/.claude/design-systems/linear/manifest.json
ls ~/.claude/design-systems/linear/tokens/
find ~/.claude/design-systems/linear/screens -name '*.png' | wc -l
cat ~/.claude/skills/design-extract/references/library.md
```

Expected: manifest has real hex values in `palette` and real family names in `fonts`;
`tokens/colors.json` is non-empty; screenshot count > 0 for an ultra run; the index has
exactly one Linear line.

- [ ] **Step 3: Consumption**

Ask `visual-code` for a landing page **in the linear system**. Then verify by reading the
emitted HTML: every color and font-family value must trace to
`design-systems/linear/tokens/`, or to `branding-agent` for brand colors and fonts. Any
value that traces to neither is an invented value and the block is not working.

- [ ] **Step 4: Precedence**

Run the same request twice:
1. "Build a Bishop AI landing page in the linear system" — expected: Bishop colors and
   fonts survive; Linear's layout, spacing, and type scale come through.
2. "Build a Bishop AI landing page, full linear system" — expected: Linear's colors and
   fonts now win.

If run 1 ships Linear's palette on a Bishop deliverable, the precedence wiring has failed
and Task 7 must be revisited before anything is reported working.

- [ ] **Step 5: Stickiness**

```bash
mkdir -p /tmp/ds-test && cd /tmp/ds-test
uv run ~/.claude/skills/design-extract/scripts/activate.py linear
cat .design-system
uv run ~/.claude/skills/design-extract/scripts/activate.py --show
uv run ~/.claude/skills/design-extract/scripts/activate.py --clear
uv run ~/.claude/skills/design-extract/scripts/activate.py --show
```

Expected: `linear  # activated <today>`, then `linear`, then `Cleared.`, then
`No active design system.` Then make a design request inside that folder while the marker
is set and confirm the system applies without being named.

- [ ] **Step 6: Degradation**

Force ultra to fail (temporarily rename the Playwright browsers cache, or extract a site
Playwright cannot reach) and confirm: the run retries in default mode, the manifest says
`"mode": "default"`, `has.screens` is `false`, and the printed report says `default`.
Restore whatever was renamed.

- [ ] **Step 7: Full suite, then report**

Run: `uv run --with pytest pytest skills/design-extract/tests/ -v`
Expected: 52 passed.

Write the outcome of Steps 1-6 into the final report — including anything that failed or
was skipped. Do not describe any step as verified that was not run.

- [ ] **Step 8: Stage, then ask Rich about committing**

```bash
git add -A skills/design-extract design-systems docs/superpowers
git status --short
```

Then ask Rich whether to commit, and what to do about `design-systems/linear/` — the
extracted payload is large and binary-heavy, so it may belong in `.gitignore` rather than
in the repo.

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| Component 1: design-extract skill | 1, 2, 3, 5, 6 |
| Component 2: the library | 1, 4 |
| Component 3: connector block | 5, 7 |
| Component 4: precedence (incl. inverted branding-agent) | 4, 5, 7, 8 |
| Component 5: activation (named + sticky) | 2, 8 |
| Skills wired (19) | 5, 7 |
| Data flow: extraction | 3, 8 |
| Data flow: consumption | 4, 8 |
| Error handling — all 6 rows | 1 (corrupt manifest, deleted system), 2 (marker to deleted system), 3 (ultra fallback, skillui failure, collision, tokenless refusal) |
| Testing 1: extraction | 8 Step 1-2 |
| Testing 2: degradation | 3 (unit), 8 Step 6 (live) |
| Testing 3: consumption | 8 Step 3 |
| Testing 4: precedence | 8 Step 4 |
| Testing 5: non-regression | 7 Step 6 |
| Testing 6: stickiness | 8 Step 5 |
| Risk: version traceability | 3 (`resolve_version`, manifest field) |
| Risk: 19 edits perturbing triggering | 7 Steps 1, 4, 5, 6 |
| Risk: blocks drifting out of sync | 5 (generated, not hand-written) |

No gaps.

**Placeholder scan:** No TBD, TODO, "similar to Task N", or "add error handling". Every
code step carries runnable code; every verification step names its expected output.

**Type consistency:** `library.slug_from_source`, `library.read_manifest`,
`library.write_manifest`, `library.system_dir`, `library.resolve`, and
`library.list_systems` are defined in Task 1 and used with matching signatures in Tasks 2
and 3. `extract.run_skillui(cmd, out)` and `extract.resolve_version()` are the two
monkeypatch seams and both are defined with those exact signatures in Task 3.
`apply_connector.GROUPS`, `TAILS`, `SENTINEL_START`, `group_of`, `render_block`,
`apply_to_file`, `revert_file`, and `SKILLS_ROOT` are defined in Task 5 and used in Tasks
5 and 7. The marker format string appears identically in Task 2's implementation, Task
2's test, Task 4's contract, and Task 8's expected output.

**Two corrections made during review:**
- `extract.run_extraction` originally trusted a zero exit code from ultra mode. A run can
  exit 0 having produced no screenshots, which would let the manifest claim `ultra` with
  no ultra artifacts — the exact misreport the spec forbids. Added the post-run
  `has.screens` check that downgrades the recorded mode to `default`.
- Task 7's revert check originally compared file sizes. Changed to SHA-256 against a
  recorded baseline, since equal length does not prove equal bytes.
