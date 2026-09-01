# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run SkillUI and register its output in the design-system library."""

from __future__ import annotations

import argparse
import datetime
import json
import re
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
    "visual_guide": "VISUAL_GUIDE.md",
}


class ExtractionError(RuntimeError):
    """Extraction failed in a way that must leave the library untouched."""


def resolve_executable(name: str) -> str:
    """Resolve `name` to a full path via shutil.which.

    Windows CreateProcess does not do PATH extension resolution (npx is
    really npx.cmd, npm is npm.cmd), so a bare "npx"/"npm" raises
    FileNotFoundError / WinError 2 with shell=False. shutil.which() finds
    the right executable (including the .cmd shim) on every platform.
    Falls back to the bare name if not found, so behavior under mocked
    subprocess.run in tests, and on platforms where the tool truly isn't
    installed, is unchanged.
    """
    return shutil.which(name) or name


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
    if shutil.which("npx") is None:
        raise ExtractionError(
            "could not find 'npx' on PATH. Install Node.js 18+ "
            "(https://nodejs.org) and make sure it is on PATH, then retry."
        )
    resolved_cmd = [resolve_executable("npx"), *cmd[1:]]
    proc = subprocess.run(
        resolved_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    return proc.returncode, proc.stderr


def resolve_version() -> str:
    """Ask npm which skillui version resolved. Seam for tests."""
    try:
        npm = resolve_executable("npm")
        proc = subprocess.run(
            [npm, "view", "skillui", "version"],
            capture_output=True, text=True, shell=False, timeout=60,
            encoding="utf-8", errors="replace",
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
    # No candidate looks like skillui output. Returning the first arbitrary
    # subdirectory would mislabel unrelated files as an extraction.
    return None


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def validate_output(folder: Path) -> tuple[bool, str]:
    """Two real skillui shapes exist. Ultra writes tokens/colors.json; default
    writes only DESIGN.md (no tokens/ at all). Accept either usable shape.

    When tokens/ is present, this run attempted ultra mode and colors.json
    must actually be populated -- a present-but-empty tokens/ signals a
    broken ultra extraction and is rejected even though DESIGN.md exists.
    When tokens/ is absent entirely, this is genuine default-mode output and
    a non-empty DESIGN.md is sufficient on its own.
    """
    tokens_dir = folder / "tokens"
    if tokens_dir.is_dir():
        colors = _load_json(tokens_dir / "colors.json")
        if colors:
            return True, ""
        return False, "tokens/colors.json is missing or empty"

    design_md = folder / "DESIGN.md"
    if design_md.is_file() and design_md.read_text(encoding="utf-8", errors="replace").strip():
        return True, ""

    return False, "no tokens/colors.json and no DESIGN.md — not a usable extraction"


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


_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# Real skillui DESIGN.md (measured live against stripe.com) names fonts as
# CSS `font-family: "Name";` declarations inside a fenced code block under a
# "## N. Typography Rules" heading -- never a single "font pairing:" line.
# Scanning the whole document for font-family: would also pick up unrelated
# CSS in the Component Stylings section, so we scope to the typography
# section first.
_TYPOGRAPHY_HEADING_RE = re.compile(r"(?im)^#{1,6}\s*\d*\.?\s*typography\b.*$")
_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+\S")
_FONT_FAMILY_RE = re.compile(r'font-family\s*:\s*["\']?([^"\';,\)]+)')
_GENERIC_FONT_KEYWORDS = {
    "inherit", "initial", "unset", "sans-serif", "serif", "monospace",
    "cursive", "fantasy", "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace",
}


def _read_design_md(folder: Path) -> str:
    """Prefer the top-level digest; fall back to references/DESIGN.md."""
    for candidate in (folder / "DESIGN.md", folder / "references" / "DESIGN.md"):
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return ""
    return ""


def _typography_section(text: str) -> str:
    """Slice out the "## N. Typography Rules" section, if any, so font
    parsing never wanders into unrelated CSS elsewhere in the document."""
    heading = _TYPOGRAPHY_HEADING_RE.search(text)
    if not heading:
        return text
    rest = text[heading.end():]
    next_heading = _HEADING_RE.search(rest)
    return rest[:next_heading.start()] if next_heading else rest


def _parse_design_md_colors(text: str) -> list[str]:
    """Hex codes from DESIGN.md's colour table, deduped, order preserved."""
    seen, unique = set(), []
    for match in _HEX_RE.finditer(text):
        code = match.group(0)
        key = code.lower()
        if key not in seen:
            seen.add(key)
            unique.append(code)
        if len(unique) >= 8:
            break
    return unique


def _parse_design_md_fonts(text: str) -> list[str]:
    """Font family names declared in DESIGN.md's typography section.

    Never invents values: returns [] when no font-family declaration is found.
    """
    section = _typography_section(text)
    seen, unique = set(), []
    for match in _FONT_FAMILY_RE.finditer(section):
        name = match.group(1).strip().strip("\"'").strip()
        if not name or name.lower() in _GENERIC_FONT_KEYWORDS:
            continue
        if name.lower().startswith("var("):
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            unique.append(name)
        if len(unique) >= 6:
            break
    return unique


def summarize(folder: Path) -> dict:
    tokens_dir = folder / "tokens"
    colors_path = tokens_dir / "colors.json"
    colors = _load_json(colors_path)
    has_tokens = tokens_dir.is_dir() and bool(colors)

    if has_tokens:
        typography = _load_json(tokens_dir / "typography.json")
        palette = _flatten_colors(colors)[:8]
        fonts = _flatten_fonts(typography)[:6]
    else:
        design_md_text = _read_design_md(folder)
        palette = _parse_design_md_colors(design_md_text)
        fonts = _parse_design_md_fonts(design_md_text)

    refs = folder / "references"
    screens = folder / "screens"
    screenshots = folder / "screenshots"
    fonts_dir = folder / "fonts"
    design_md = folder / "DESIGN.md"

    has = {
        "tokens": has_tokens,
        "design_md": design_md.is_file()
        and bool(design_md.read_text(encoding="utf-8", errors="replace").strip()),
        "screenshots": screenshots.is_dir() and any(screenshots.glob("*.png")),
        "screens": screens.is_dir() and any(screens.rglob("*.png")),
        "fonts": fonts_dir.is_dir() and any(fonts_dir.glob("*.woff2")),
        "skill_package": any(folder.glob("*.skill")),
    }
    for key, filename in REFERENCE_FILES.items():
        has[key] = (refs / filename).is_file()
    return {
        "palette": palette,
        "fonts": fonts,
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


# skillui always writes its own global Claude skill as a side effect, no
# matter what --out points at. The installed copy is broken anyway (it tells
# readers to "Read references/DESIGN.md" but ships no references/ beside
# it), and with ~120 skills already registered, one extra always-on
# dead-pointer skill per extracted site degrades skill triggering across all
# of them. We remove it, but only when we can positively identify it as
# skillui's own artifact.
_STRAY_SKILL_FILES = {"SKILL.md", "CLAUDE.md"}


def stray_skill_path(folder_name: str, skills_root: Path | None = None) -> Path:
    """Where skillui would have installed its global skill for this run.

    skillui derives its own name from the source and uses it for both the
    output folder (e.g. "stripe-design") and the installed skill directory
    name -- they are the same string, so the output folder's own name is
    exactly the installed directory's name.
    """
    root = skills_root if skills_root is not None else (Path.home() / ".claude" / "skills")
    return root / folder_name


def _is_git_tracked(path: Path) -> bool:
    """True if `path` (or anything under it) is tracked by git.

    Any failure to determine this (git missing, not a repo, etc.) is
    treated as "can't be sure" -> tracked, so cleanup refuses rather than
    risks deleting something real.
    """
    git = resolve_executable("git")
    try:
        proc = subprocess.run(
            [git, "-C", str(path), "ls-files", "."],
            capture_output=True, text=True, shell=False, timeout=10,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return True
    if proc.returncode != 0:
        return False
    return bool(proc.stdout.strip())


def _is_safe_stray_skill_dir(path: Path) -> bool:
    """True only if `path` looks exactly like skillui's own bare skill
    install: a SKILL.md, optionally CLAUDE.md, optionally a references/
    subfolder of markdown files, nothing else -- and it is not git-tracked.
    """
    if not path.is_dir():
        return False
    try:
        entries = list(path.iterdir())
    except OSError:
        return False
    for entry in entries:
        if entry.is_file():
            if entry.name not in _STRAY_SKILL_FILES:
                return False
        elif entry.is_dir():
            if entry.name != "references":
                return False
            for sub in entry.rglob("*"):
                if sub.is_file() and sub.suffix.lower() != ".md":
                    return False
        else:
            return False
    return not _is_git_tracked(path)


def cleanup_stray_global_skill(
    folder_name: str, keep: bool = False, skills_root: Path | None = None
) -> None:
    """Remove the stray global skill skillui installed for this run, iff it
    is safe to do so. Never raises -- a cleanup failure must not fail the
    extraction itself.
    """
    if keep:
        return
    stray = stray_skill_path(folder_name, skills_root)
    if not stray.exists():
        return
    if _is_safe_stray_skill_dir(stray):
        shutil.rmtree(stray)
        print(f"Removed stray global skill installed by skillui: {stray}")
    else:
        print(
            f"WARNING: skillui appears to have installed a global skill at "
            f"{stray}, but its contents don't match skillui's known shape "
            "(or it is git-tracked). Leaving it in place -- inspect and "
            "remove manually if it is unwanted."
        )


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
    keep_installed_skill: bool = False,
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
            raise ExtractionError(
                "skillui produced no recognizable output folder "
                "(nothing containing DESIGN.md or tokens/)"
            )

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
        cleanup_stray_global_skill(folder.name, keep=keep_installed_skill)
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
    parser.add_argument(
        "--keep-installed-skill", action="store_true",
        help="Keep the global Claude skill skillui installs as a side effect "
             "(normally removed since it ships broken -- no references/ beside it).",
    )
    args = parser.parse_args(argv)

    source_type = "url" if args.url else ("dir" if args.dir else "repo")
    source = args.url or args.dir or args.repo

    try:
        manifest = run_extraction(
            source, source_type, args.name, args.mode, args.screens, args.force,
            keep_installed_skill=args.keep_installed_skill,
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
