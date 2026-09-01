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

# branding-agent sits in the "graphics" group for GROUPS/TAILS bookkeeping, but it is not
# an image/deck emitter — it is a reference skill — so it gets its own tail instead of
# TAILS["graphics"]. See render_block().
BRANDING_TAIL = (
    "**This skill defines brand values.** When a system is active, read `tokens/` and "
    "`DESIGN.md` only to understand what the extracted system offers — never to redefine a "
    "Bishop value."
)

STANDARD_BLOCK = """## Extracted Design System

**First, scan the request for the literal phrase "full <name> system"** (e.g. "full linear
system"). Near-miss phrasings — "use Linear's colors", "make it look like Linear", "match
Linear's branding" — do NOT count. Only the literal phrase.

- **Phrase present** -> that extracted system supersedes `branding-agent` for this one
  deliverable. Read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`, and use its
  colors and font families directly.
- **Phrase absent** -> resolve the active system the normal way:
  1. A system named in the request ("in the linear system", "build this like Stripe"), or a
     `.design-system` marker file in the working folder.
  2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
  3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
     motion, easing, interaction states.
     **KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families, logo
     treatment.
  4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Measured beats recommended: where an active system covers a decision, it outranks
`design-intel`. Where it is silent — accessibility, chart choice, breakpoints —
`design-intel` is still the answer.

{tail}

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
"""

# branding-agent is layer 2. It is told it is the authority, not told to defer —
# otherwise the two blocks contradict each other. Same lead-with-the-check shape as
# STANDARD_BLOCK: the phrase check comes first, the "brand authority" absolute is the
# consequence of the phrase being absent, not an unconditional opener.
BRANDING_BLOCK = """## Extracted Design System

**First, scan the request for the literal phrase "full <name> system"** (e.g. "full linear
system").

- **Phrase present** -> that extracted system supersedes this skill for this one
  deliverable. Use its colors and font families from `~/.claude/design-systems/<slug>/`.
  State in one line that you did so and why.
- **Phrase absent** -> this skill is the brand authority, and extracted systems sit beneath
  it. Bishop AI / Prompt Anything colors, font families, and logo treatment win over any
  extracted system. An active system may still contribute layout, spacing grid, type scale
  ratios, component patterns, motion, and interaction states — borrowing a 1.25 type scale
  while keeping the Bishop typeface is the intended outcome, not a compromise.

Near-miss phrasings do NOT trigger the override: "use Linear's colors", "make it look like
Linear", "match Linear's branding". Only the literal phrase.

{tail}

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
    if skill == "branding-agent":
        return BRANDING_BLOCK.format(tail=BRANDING_TAIL)
    return STANDARD_BLOCK.format(tail=TAILS[group])


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
