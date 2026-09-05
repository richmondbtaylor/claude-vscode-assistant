"""Importing a real ComfyUI export, and proving it round-trips.

The valuable test here is the last one: tokenize a graph, then run it back
through the ComfyUI backend's substitution. If the importer and the backend
ever disagree about the token vocabulary, that test fails and nothing else
would have caught it.
"""

from __future__ import annotations

import json

import pytest

from vidforge.comfy_import import ImportError_, import_workflow, tokenize


def wan_graph() -> dict:
    """A Wan text-to-video graph in API format, shaped like a real export."""
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "seed": 745829, "steps": 20, "cfg": 6.0, "sampler_name": "euler",
            "scheduler": "normal", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]}},
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "wan2.1_t2v_1.3B.safetensors"}},
        "5": {"class_type": "EmptyHunyuanLatentVideo", "inputs": {
            "width": 832, "height": 480, "length": 81, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "a cat on a roof", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "blurry, watermark", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["8", 0], "frame_rate": 16, "filename_prefix": "wan"}},
    }


def test_prompts_are_tokenized_by_wiring_not_by_order():
    graph = wan_graph()
    tokenize(graph)
    assert graph["6"]["inputs"]["text"] == "%prompt%"
    assert graph["7"]["inputs"]["text"] == "%negative_prompt%"


def test_wiring_wins_even_when_the_negative_node_comes_first():
    # Authoring order is arbitrary; only the sampler's inputs say which is which.
    graph = wan_graph()
    graph["3"]["inputs"]["positive"] = ["7", 0]
    graph["3"]["inputs"]["negative"] = ["6", 0]
    tokenize(graph)
    assert graph["7"]["inputs"]["text"] == "%prompt%"
    assert graph["6"]["inputs"]["text"] == "%negative_prompt%"


def test_sampler_settings_are_tokenized():
    graph = wan_graph()
    tokenize(graph)
    inputs = graph["3"]["inputs"]
    assert inputs["seed"] == "%seed%"
    assert inputs["steps"] == "%steps%"
    assert inputs["cfg"] == "%cfg%"
    assert inputs["sampler_name"] == "euler"  # not ours to drive


def test_frame_size_and_length_are_tokenized_but_batch_size_is_left_alone():
    graph = wan_graph()
    tokenize(graph)
    inputs = graph["5"]["inputs"]
    assert (inputs["width"], inputs["height"], inputs["length"]) == \
        ("%width%", "%height%", "%num_frames%")
    assert inputs["batch_size"] == 1


def test_frame_rate_is_tokenized():
    graph = wan_graph()
    tokenize(graph)
    assert graph["9"]["inputs"]["frame_rate"] == "%fps%"


def test_wired_inputs_are_never_overwritten():
    # Overwriting a ["4", 0] link would silently disconnect the graph.
    graph = wan_graph()
    tokenize(graph)
    assert graph["3"]["inputs"]["model"] == ["4", 0]
    assert graph["8"]["inputs"]["samples"] == ["3", 0]


def test_a_seed_driven_by_another_node_is_respected():
    graph = wan_graph()
    graph["3"]["inputs"]["seed"] = ["99", 0]
    tokenize(graph)
    assert graph["3"]["inputs"]["seed"] == ["99", 0]


def test_advanced_sampler_noise_seed_is_found():
    graph = wan_graph()
    graph["3"] = {"class_type": "KSamplerAdvanced", "inputs": {
        "noise_seed": 5, "steps": 20, "cfg": 6.0,
        "positive": ["6", 0], "negative": ["7", 0]}}
    tokenize(graph)
    assert graph["3"]["inputs"]["noise_seed"] == "%seed%"


# --- rejections and warnings ----------------------------------------------
def test_a_ui_format_export_is_rejected_with_the_fix():
    with pytest.raises(ImportError_, match="Save \\(API Format\\)"):
        tokenize({"nodes": [], "links": []})


def test_an_empty_file_is_rejected():
    with pytest.raises(ImportError_, match="API-format"):
        tokenize({})


def test_a_graph_with_no_saving_node_warns():
    graph = wan_graph()
    del graph["9"]
    assert any("saving node" in w for w in tokenize(graph).warnings)


def test_a_graph_with_no_prompt_warns():
    graph = wan_graph()
    graph["3"]["inputs"].pop("positive")
    assert any("positive prompt" in w for w in tokenize(graph).warnings)


def test_a_clean_graph_warns_about_nothing():
    assert tokenize(wan_graph()).warnings == []


# --- the round trip --------------------------------------------------------
def test_import_then_substitute_yields_a_runnable_graph(tmp_path):
    """The importer's tokens and the backend's substitution must agree."""
    from vidforge.backends.comfyui import substitute

    source = tmp_path / "export.json"
    source.write_text(json.dumps(wan_graph()))
    destination = tmp_path / "wan.json"
    report = import_workflow(source, destination)
    assert report.warnings == []

    stored = json.loads(destination.read_text())
    live = substitute(stored, {
        "prompt": "a rain-slicked alley", "negative_prompt": "blurry",
        "seed": 4242, "steps": 30, "cfg": 5.5,
        "width": 1280, "height": 720, "num_frames": 121, "fps": 24,
    })

    assert live["6"]["inputs"]["text"] == "a rain-slicked alley"
    assert live["7"]["inputs"]["text"] == "blurry"
    assert live["3"]["inputs"]["seed"] == 4242          # int, not "4242"
    assert live["3"]["inputs"]["cfg"] == 5.5
    assert live["5"]["inputs"]["length"] == 121
    assert live["9"]["inputs"]["frame_rate"] == 24
    assert live["3"]["inputs"]["model"] == ["4", 0]     # wiring survived
    assert "%" not in json.dumps(live)                  # nothing left unresolved
