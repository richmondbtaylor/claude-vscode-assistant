"""Editing models.toml from the CLI.

Adding a checkpoint or a LoRA stack should not mean hand-editing TOML and
getting the quoting wrong. These helpers read the registry, add or remove an
entry, and write it back with the comments at the top preserved.
"""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path
from typing import Any

import tomli_w


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _leading_comments(path: Path) -> str:
    """Keep the explanatory header at the top of the file."""
    if not path.exists():
        return ""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            lines.append(line)
        else:
            break
    return "\n".join(lines).rstrip() + "\n\n" if lines else ""


def write(path: Path, data: dict) -> None:
    """Write the registry back, keeping a one-deep backup."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy(path, path.with_suffix(".toml.bak"))
    path.write_text(_leading_comments(path) + tomli_w.dumps(data), encoding="utf-8")


def add_model(path: Path, model_id: str, entry: dict[str, Any], *,
              overwrite: bool = False) -> None:
    data = _read(path)
    models = data.setdefault("model", {})
    if model_id in models and not overwrite:
        raise ValueError(f"model {model_id!r} already exists; pass --force to replace it")
    models[model_id] = entry
    write(path, data)


def remove_model(path: Path, model_id: str) -> bool:
    data = _read(path)
    models = data.get("model", {})
    if model_id not in models:
        return False
    del models[model_id]
    write(path, data)
    return True


def clone_with_loras(path: Path, base_id: str, new_id: str,
                     loras: list[dict], *, overwrite: bool = False) -> dict:
    """Copy a registry entry and stack LoRAs on the copy.

    The base entry is left alone, so the unmodified model stays available for
    comparison - which is the whole point of adding a LoRA at a given weight.
    """
    data = _read(path)
    models = data.get("model", {})
    if base_id not in models:
        known = ", ".join(sorted(models)) or "<none>"
        raise KeyError(f"no model {base_id!r} to build on; registry has: {known}")

    entry = dict(models[base_id])
    entry["loras"] = [*entry.get("loras", []), *loras]
    entry["label"] = entry.get("label", base_id) + " + " + ", ".join(
        str(lora.get("name") or Path(str(lora.get("repo", ""))).stem) for lora in loras
    )
    add_model(path, new_id, entry, overwrite=overwrite)
    return entry
