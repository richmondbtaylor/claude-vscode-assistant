"""Cover the diffusers backend's own logic without pretrained weights.

Whether diffusers can denoise is diffusers' problem. What is vidforge's
problem is everything wrapped around the pipeline call: detaching the content
filter, filtering kwargs down to what a given pipeline accepts, reporting
progress, honouring cancellation, and turning whatever comes back into a file.
Those are all testable against a stub pipeline.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from vidforge.backends.base import Cancelled, GenRequest
from vidforge.backends.diffusers_backend import DiffusersBackend, _extract_frames, _unfilter
from vidforge.config import ModelSpec

torch = pytest.importorskip("torch", reason="diffusers backend needs torch")


# --- filter removal --------------------------------------------------------
def test_unfilter_detaches_the_checker_and_the_watermarker():
    pipe = SimpleNamespace(
        safety_checker=object(), watermarker=object(), feature_extractor=object(),
        requires_safety_checker=True,
    )
    removed = _unfilter(pipe)

    assert pipe.safety_checker is None
    assert pipe.watermarker is None
    assert pipe.requires_safety_checker is False
    assert {"safety_checker", "watermarker"} <= set(removed)


def test_unfilter_keeps_feature_extractor_when_there_is_no_checker():
    # Image-conditioned pipelines use feature_extractor for the conditioning
    # image; only strip it when it belongs to a safety checker.
    encoder = object()
    pipe = SimpleNamespace(safety_checker=None, feature_extractor=encoder)
    _unfilter(pipe)
    assert pipe.feature_extractor is encoder


def test_unfilter_is_a_noop_on_a_pipeline_that_never_had_one():
    pipe = SimpleNamespace(vae=object())
    assert _unfilter(pipe) == []


# --- result shapes ---------------------------------------------------------
def test_extract_frames_unwraps_a_batched_clip():
    assert _extract_frames(SimpleNamespace(frames=[["a", "b", "c"]])) == ["a", "b", "c"]


def test_extract_frames_accepts_a_flat_list():
    assert _extract_frames(SimpleNamespace(frames=["a", "b"])) == ["a", "b"]


def test_extract_frames_falls_back_to_images():
    assert _extract_frames(SimpleNamespace(frames=None, images=["a"])) == ["a"]


def test_extract_frames_complains_when_there_is_nothing():
    with pytest.raises(RuntimeError, match="no frames"):
        _extract_frames(SimpleNamespace())


# --- the call surface ------------------------------------------------------
class StubPipeline:
    """Stands in for a diffusers video pipeline with a narrow signature."""

    def __init__(self, frames=8, steps_to_run=3):
        self.frames = frames
        self.steps_to_run = steps_to_run
        self.seen: dict = {}

    def __call__(self, prompt, num_inference_steps=1, generator=None, width=64,
                 height=64, num_frames=4, callback_on_step_end=None):
        from PIL import Image

        self.seen = dict(
            prompt=prompt, num_inference_steps=num_inference_steps,
            width=width, height=height, num_frames=num_frames,
        )
        for step in range(self.steps_to_run):
            if callback_on_step_end:
                callback_on_step_end(self, step, 0, {})
        clip = [Image.new("RGB", (width, height), (step * 8, 40, 80))
                for step in range(num_frames)]
        return SimpleNamespace(frames=[clip])


@pytest.fixture
def backend(ctx, monkeypatch):
    be = DiffusersBackend(ctx.settings)
    stub = StubPipeline()
    monkeypatch.setattr(be, "_load", lambda spec: stub)
    monkeypatch.setattr(be, "preflight", lambda: None)
    return be, stub


def _request(tmp_path, **params):
    base = {"width": 96, "height": 64, "num_frames": 4, "fps": 8, "steps": 3}
    base.update(params)
    return GenRequest(
        job_id="t", model=ModelSpec(id="stub", backend="diffusers"),
        prompt="a quiet street", negative_prompt="blurry", seed=7,
        out_path=tmp_path / "out.mp4", params=base,
    )


def test_generate_writes_a_video_and_a_thumbnail(backend, tmp_path):
    be, _stub = backend
    seen = []
    result = be.generate(_request(tmp_path), seen.append, threading.Event())

    assert result.video_path.exists() and result.video_path.stat().st_size > 0
    assert result.thumb_path and result.thumb_path.exists()
    assert seen and seen[-1] == 1.0
    assert seen == sorted(seen)  # progress only ever moves forward


def test_unsupported_kwargs_are_dropped_before_the_call(backend, tmp_path):
    # The stub takes no negative_prompt or guidance_scale. One registry has to
    # drive pipelines with very different signatures, so extras must be culled
    # rather than raising TypeError.
    be, stub = backend
    be.generate(_request(tmp_path, guidance_scale=7.5), lambda _f: None, threading.Event())
    assert stub.seen["prompt"] == "a quiet street"
    assert stub.seen["num_frames"] == 4


def test_cancellation_stops_the_pipeline(backend, tmp_path):
    be, _stub = backend
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        be.generate(_request(tmp_path), lambda _f: None, cancel)
    assert not (tmp_path / "out.mp4").exists()


def test_i2v_without_an_init_image_is_a_clear_error(ctx, monkeypatch, tmp_path):
    be = DiffusersBackend(ctx.settings)
    monkeypatch.setattr(be, "_load", lambda spec: StubPipeline())
    monkeypatch.setattr(be, "preflight", lambda: None)
    request = _request(tmp_path)
    request.model = ModelSpec(id="stub-i2v", backend="diffusers", kind="i2v")
    with pytest.raises(ValueError, match="init image is required"):
        be.generate(request, lambda _f: None, threading.Event())
