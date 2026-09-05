"""Prompt expansion and batch building.

This is the seam for an external prompt generator: hand vidforge a list of
prompt strings (API, ``.txt``, ``.json`` or ``.jsonl``) and it takes care of
wildcard expansion, seed sweeps and queueing.

Two template features, both familiar from A1111/ComfyUI wildcard tooling:

* ``{a|b|c}``   - pick one, nestable: ``{neon {pink|blue}|daylight}``
* ``__name__``  - pick a random line from ``$VIDFORGE_HOME/wildcards/name.txt``
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

_ALTERNATION = re.compile(r"\{([^{}]*)\}")
_WILDCARD = re.compile(r"__([A-Za-z0-9_][A-Za-z0-9_./-]*)__")
_MAX_PASSES = 20


def _split_options(body: str) -> list[str]:
    return [opt.strip() for opt in body.split("|")]


def load_wildcards(directory: Path) -> dict[str, list[str]]:
    """Read ``*.txt`` wildcard files. Blank lines and ``#`` comments are dropped."""
    table: dict[str, list[str]] = {}
    if not directory.is_dir():
        return table
    for path in sorted(directory.rglob("*.txt")):
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if lines:
            table[path.relative_to(directory).with_suffix("").as_posix()] = lines
    return table


def expand(template: str, wildcards: dict[str, list[str]] | None = None,
           rng: random.Random | None = None) -> str:
    """Resolve one template into one concrete prompt."""
    rng = rng or random.Random()
    wildcards = wildcards or {}
    text = template
    for _ in range(_MAX_PASSES):
        before = text
        # innermost alternations first, so nesting resolves bottom-up
        text = _ALTERNATION.sub(lambda m: rng.choice(_split_options(m.group(1))), text)
        text = _WILDCARD.sub(
            lambda m: rng.choice(wildcards[m.group(1)]) if m.group(1) in wildcards else m.group(0),
            text,
        )
        if text == before:
            break
    return re.sub(r"\s+", " ", text).strip(" ,")


def load_prompt_file(path: Path) -> list[str]:
    """Read prompts from ``.txt`` (one per line), ``.json`` or ``.jsonl``.

    JSON entries may be plain strings or objects carrying a ``prompt`` key,
    which is what most prompt generators emit.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()

    def _from_obj(obj: object) -> str | None:
        if isinstance(obj, str):
            return obj.strip() or None
        if isinstance(obj, dict):
            for key in ("prompt", "text", "positive", "description"):
                value = obj.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    if suffix == ".json":
        data = json.loads(text)
        items = data if isinstance(data, list) else data.get("prompts", [])
        return [p for p in (_from_obj(i) for i in items) if p]
    if suffix == ".jsonl":
        out = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            got = _from_obj(json.loads(line))
            if got:
                out.append(got)
        return out
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def build_batch(
    templates: list[str],
    *,
    variants: int = 1,
    seeds: list[int] | None = None,
    expand_wildcards: bool = True,
    wildcards: dict[str, list[str]] | None = None,
    rng: random.Random | None = None,
) -> list[tuple[str, int]]:
    """Cross prompts with seeds into concrete ``(prompt, seed)`` work items.

    Explicit ``seeds`` win over ``variants``; each variant gets a fresh random
    seed so a batch of 10 is 10 different takes, not the same frame ten times.
    """
    rng = rng or random.Random()
    seeds = [s for s in (seeds or []) if s is not None]
    out: list[tuple[str, int]] = []
    for template in templates:
        chosen = seeds if seeds else [rng.randrange(0, 2**31 - 1) for _ in range(max(1, variants))]
        for seed in chosen:
            # Re-roll wildcards per item so a batch explores the template space.
            prompt = expand(template, wildcards, rng) if expand_wildcards else template.strip()
            if prompt:
                out.append((prompt, int(seed)))
    return out
