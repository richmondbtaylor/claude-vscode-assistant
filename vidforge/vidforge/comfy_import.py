"""Turn a working ComfyUI graph into a vidforge workflow.

Hand-writing a video workflow from scratch is how you spend an evening
debugging node wiring. So vidforge does not ship one: you build the graph in
ComfyUI until it renders what you want, export it with **Save (API Format)**,
and this module rewrites the handful of fields vidforge needs to drive -
prompt, seed, size, length, steps, cfg, fps - into ``%token%`` placeholders.

Everything it changes is reported back, because a silent substitution in the
wrong node is worse than none at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Sampler-ish nodes carry the seed and the denoise settings.
_SEED_KEYS = ("seed", "noise_seed")
_SAMPLER_KEYS = {"steps": "%steps%", "cfg": "%cfg%"}
# Latent generators carry the frame size and the clip length.
_SIZE_KEYS = {"width": "%width%", "height": "%height%"}
_LENGTH_KEYS = {"length": "%num_frames%", "num_frames": "%num_frames%",
                "video_frames": "%num_frames%"}
_FPS_KEYS = {"frame_rate": "%fps%", "fps": "%fps%"}

_TEXT_FIELDS = ("text", "prompt", "positive", "string")


class ImportError_(ValueError):
    """The file is not something vidforge can drive."""


@dataclass(slots=True)
class ImportReport:
    graph: dict
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def note(self, node_id: str, class_type: str, key: str, token: str) -> None:
        self.changes.append(f"  {token:<18} node {node_id} ({class_type}).{key}")

    @property
    def tokens(self) -> set[str]:
        return {line.split()[0] for line in self.changes}


def _is_link(value: Any) -> bool:
    """A wired input looks like ``["6", 0]`` and must never be overwritten."""
    return isinstance(value, list) and len(value) == 2 and isinstance(value[1], int)


def _looks_like_latent(class_type: str, inputs: dict) -> bool:
    lowered = class_type.lower()
    if "latent" in lowered or lowered.startswith("empty"):
        return True
    # A node carrying width, height and a length is a video latent whatever
    # the custom pack decided to call it.
    return "width" in inputs and "height" in inputs and any(k in inputs for k in _LENGTH_KEYS)


def _looks_like_sampler(class_type: str, inputs: dict) -> bool:
    lowered = class_type.lower()
    if "sampler" in lowered:
        return True
    return any(k in inputs for k in _SEED_KEYS) and "steps" in inputs


def _text_key(inputs: dict) -> str | None:
    return next((k for k in _TEXT_FIELDS if isinstance(inputs.get(k), str)), None)


def _prompt_nodes(graph: dict) -> tuple[set[str], set[str]]:
    """Which text nodes feed a sampler's positive input, and which its negative.

    Following the wiring beats guessing from node order: a graph with the
    negative prompt authored first would otherwise come out inverted.
    """
    positive: set[str] = set()
    negative: set[str] = set()
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs") or {}
        for role, bucket in (("positive", positive), ("negative", negative)):
            link = inputs.get(role)
            if _is_link(link):
                bucket.add(str(link[0]))
    return positive, negative


def tokenize(graph: dict) -> ImportReport:
    """Rewrite the drivable fields of an API-format graph into placeholders."""
    if not isinstance(graph, dict) or not graph:
        raise ImportError_("this is not a ComfyUI API-format graph (expected an object of nodes)")
    if "nodes" in graph and "links" in graph:
        raise ImportError_(
            "this is a UI-format workflow. In ComfyUI use the menu's "
            "'Save (API Format)' export instead, which writes a different file."
        )

    report = ImportReport(graph=graph)
    positive, negative = _prompt_nodes(graph)

    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type", "?")
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue

        # text encoders
        key = _text_key(inputs)
        if key is not None:
            if node_id in positive:
                inputs[key] = "%prompt%"
                report.note(node_id, class_type, key, "%prompt%")
            elif node_id in negative:
                inputs[key] = "%negative_prompt%"
                report.note(node_id, class_type, key, "%negative_prompt%")

        if _looks_like_sampler(class_type, inputs):
            for seed_key in _SEED_KEYS:
                if seed_key in inputs and not _is_link(inputs[seed_key]):
                    inputs[seed_key] = "%seed%"
                    report.note(node_id, class_type, seed_key, "%seed%")
            for field_name, token in _SAMPLER_KEYS.items():
                if field_name in inputs and not _is_link(inputs[field_name]):
                    inputs[field_name] = token
                    report.note(node_id, class_type, field_name, token)

        if _looks_like_latent(class_type, inputs):
            for field_name, token in {**_SIZE_KEYS, **_LENGTH_KEYS}.items():
                if field_name in inputs and not _is_link(inputs[field_name]):
                    inputs[field_name] = token
                    report.note(node_id, class_type, field_name, token)

        for field_name, token in _FPS_KEYS.items():
            if field_name in inputs and not _is_link(inputs[field_name]):
                inputs[field_name] = token
                report.note(node_id, class_type, field_name, token)

    _warn(report)
    return report


def _warn(report: ImportReport) -> None:
    found = report.tokens
    if "%prompt%" not in found:
        report.warnings.append(
            "no positive prompt node found - vidforge will not be able to set the prompt. "
            "Check the graph really wires a text encoder into the sampler's positive input."
        )
    if "%seed%" not in found:
        report.warnings.append(
            "no seed found - every render in a batch would come out identical."
        )
    saver = any(
        isinstance(n, dict) and "save" in str(n.get("class_type", "")).lower()
        or isinstance(n, dict) and "videocombine" in str(n.get("class_type", "")).lower()
        for n in report.graph.values()
    )
    if not saver:
        report.warnings.append(
            "no saving node found (VHS_VideoCombine, SaveAnimatedWEBP, SaveImage). "
            "Without one the workflow runs and produces no file for vidforge to collect."
        )


def import_workflow(source: Path, destination: Path) -> ImportReport:
    try:
        graph = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImportError_(f"{source.name} is not valid JSON: {exc}") from exc
    if isinstance(graph, dict) and "prompt" in graph and "class_type" not in str(graph)[:200]:
        graph = graph.get("prompt", graph)  # some exports wrap the graph

    report = tokenize(graph)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.graph, indent=2), encoding="utf-8")
    return report
