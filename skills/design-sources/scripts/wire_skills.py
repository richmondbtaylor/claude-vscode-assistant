#!/usr/bin/env python3
"""Append (or refresh) the design-bridge pointer block in each design skill.

    python wire_skills.py            # apply
    python wire_skills.py --check    # report only, change nothing
    python wire_skills.py --remove   # strip the block from every skill

Idempotent: the block is delimited by HTML comment markers, so re-running
replaces the existing block rather than stacking duplicates. Nothing else in the
target file is touched, and the frontmatter is never rewritten.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS = Path.home() / ".claude" / "skills"
START = "<!-- design-bridge:start -->"
END = "<!-- design-bridge:end -->"

CLUSTERS: dict[str, list[str]] = {
    "web-ui": [
        "visual-code", "image-to-code-skill", "imagegen-frontend-web",
        "minimalist-skill", "brutalist-skill", "website-to-hyperframes",
        "codecraft",
    ],
    "deck-doc": [
        "slideforge", "prestige", "pitch-deck-architect", "course-builder",
        "email-html-gen", "ai-audit", "ops-audit", "lead-audit-walkthrough",
        "handout-builder", "homework-builder", "certification-one-pager",
        "service-agreement", "invoice-generator",
    ],
    "brand-graphics": [
        "branding-agent", "citadel", "carousel", "infographic-generator",
        "reel-cover",
    ],
    "video-motion": [
        "reelforge", "hyperframes", "claude-design-hyperframes",
        "slide-overlay", "video-use", "vistage", "gsap",
    ],
}

GATE_LINE = {
    "web-ui": (
        "3. **Gate before delivery (blocking).** Any HTML you produce must reach "
        "exit 0:\n"
        "   ```bash\n"
        "   python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file> --mobile\n"
        "   ```\n"
        "   The gate is the standard, not your own read of the page. Never call a "
        "page clean without running it."
    ),
    "deck-doc": (
        "3. **Gate before export (blocking).** Run it on the HTML *before* the PDF "
        "or screenshot step:\n"
        "   ```bash\n"
        "   python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file>\n"
        "   ```\n"
        "   A defect baked into a PDF is far more expensive to find than one caught "
        "in the HTML."
    ),
    "brand-graphics": (
        "3. **No gate on image output.** `impeccable detect` parses HTML/CSS/URLs, "
        "so there is nothing to scan in a PNG. Do not claim a gate pass on an image. "
        "If the graphic is produced by screenshotting HTML, gate that HTML before "
        "capture."
    ),
    "video-motion": (
        "3. **No gate here**, and the adapter is deliberately narrow. Rich's overlay "
        "grammar (Saraev / Murph / Mav, safe bands, plate rules, cut pacing, no-zoom) "
        "is locked and is **not** open to revision by an external web-design source. "
        "Share correctness, never share grammar."
    ),
}


def block(cluster: str) -> str:
    return f"""{START}

## Design bridges: consult before building

Three bridge skills sit under this one. None of them produces deliverables; this
skill still owns the output.

1. **`design-extract`** — MEASURED tokens from one named site, repo, or project.
   When a design system is active it wins on layout, spacing, type scale,
   components, motion and interaction states.
2. **`design-intel`** — RECOMMENDED generic values (layout, spacing, UX,
   accessibility, chart selection, font pairing) where brand and the active
   system are silent.
3. **`design-sources`** — external craft rules plus the deterministic gate. Read
   `C:/Users/richm/.claude/skills/design-sources/references/{cluster}.md` for this medium.

**Precedence:** explicit instruction in the request > `branding-agent` (colours,
fonts, logo) > active extracted system > style preset (`brutalist-skill`,
`minimalist-skill`) > `design-intel` > skill defaults. Measured beats
recommended where both cover a decision. Borrow ratios and structure from an
extracted system; keep brand colours and typefaces from `branding-agent`.

`design-sources` is a **gate, not a precedence layer**: it runs before shipping
no matter which layer supplied the values.

{GATE_LINE[cluster]}

**Brand outranks both.** Bishop AI / Prompt Anything / BOB colours and typefaces
come from `branding-agent` and `tokens.json`, never from an external source.
Verified: Bishop AI's own palette trips two Impeccable rules (`cream-palette` on
warm-white `#F9F6F0`, `overused-font` on Open Sans); both are waived in
`C:/Users/richm/.claude/design-sources/brand-overrides/config.json` and reported as overridden
rather than failed. Do not "fix" brand to satisfy a detector.

{END}"""


def apply(path: Path, cluster: str, remove: bool) -> str:
    text = path.read_text(encoding="utf-8")
    has = START in text and END in text

    if remove:
        if not has:
            return "absent"
        pre = text.split(START)[0].rstrip() + "\n"
        post = text.split(END, 1)[1]
        path.write_text(pre + post.lstrip("\n"), encoding="utf-8")
        return "removed"

    new_block = block(cluster)
    if has:
        pre = text.split(START)[0]
        post = text.split(END, 1)[1]
        updated = pre + new_block + post
        if updated == text:
            return "unchanged"
        path.write_text(updated, encoding="utf-8")
        return "refreshed"

    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    path.write_text(text + sep + "\n" + new_block + "\n", encoding="utf-8")
    return "added"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    counts: dict[str, int] = {}
    missing: list[str] = []

    for cluster, names in CLUSTERS.items():
        for name in names:
            path = SKILLS / name / "SKILL.md"
            if not path.exists():
                missing.append(name)
                continue
            if args.check:
                state = "present" if START in path.read_text(encoding="utf-8") else "MISSING"
                print(f"{state:<10} {cluster:<15} {name}")
                counts[state] = counts.get(state, 0) + 1
                continue
            state = apply(path, cluster, args.remove)
            print(f"{state:<10} {cluster:<15} {name}")
            counts[state] = counts.get(state, 0) + 1

    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    if missing:
        print(f"NOT FOUND: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
