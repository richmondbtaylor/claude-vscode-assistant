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
