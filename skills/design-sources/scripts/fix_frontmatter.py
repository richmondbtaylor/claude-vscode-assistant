#!/usr/bin/env python3
"""Repair SKILL.md frontmatter whose `description:` fails strict YAML.

The usual cause is an unquoted colon-space inside the description, e.g.
`... ready for Netlify: student hub, teacher hub ...`, which YAML reads as a
nested mapping. This rewrites the scalar as a literal block (`|-`) so the text is
preserved byte for byte with no escaping, and the document parses.

    python fix_frontmatter.py --check    # list failures, change nothing
    python fix_frontmatter.py            # repair

Only the description scalar is rewritten. No description text is altered, so
skill triggering behaviour is unchanged.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SKILLS = Path.home() / ".claude" / "skills"
FM = re.compile(r"^(---\r?\n)(.*?)(\r?\n---\r?\n)", re.S)


def parses(fm: str) -> bool:
    try:
        return isinstance(yaml.safe_load(fm), dict)
    except Exception:
        return False


def repair(fm: str, eol: str) -> str | None:
    """Rewrite `description: <scalar>` as a literal block."""
    m = re.search(r"^description:[ \t]*(.+?)(?=\r?\n[A-Za-z_-]+:|\Z)",
                  fm, re.S | re.M)
    if not m:
        return None
    text = m.group(1)
    # Already a block scalar; nothing to do.
    if text.lstrip().startswith(("|", ">")):
        return None
    flat = " ".join(text.split())
    block = "description: |-" + eol + "  " + flat
    return fm[:m.start()] + block + fm[m.end():]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    failed, fixed, still = [], [], []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        raw = path.read_bytes().decode("utf-8-sig")
        m = FM.match(raw)
        if not m:
            continue
        fm = m.group(2)
        if parses(fm):
            continue
        failed.append(path.parent.name)
        if args.check:
            continue
        eol = "\r\n" if "\r\n" in m.group(1) else "\n"
        new_fm = repair(fm, eol)
        if new_fm and parses(new_fm):
            path.write_bytes(
                (raw[:m.start(2)] + new_fm + raw[m.end(2):]).encode("utf-8")
            )
            fixed.append(path.parent.name)
        else:
            still.append(path.parent.name)

    print(f"failing strict YAML: {len(failed)}")
    for n in failed:
        print(f"  {n}")
    if not args.check:
        print(f"\nrepaired: {len(fixed)}  {', '.join(fixed) or '-'}")
        if still:
            print(f"STILL BROKEN: {', '.join(still)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
