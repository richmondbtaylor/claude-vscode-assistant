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
