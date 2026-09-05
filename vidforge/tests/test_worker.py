import time

from vidforge.schemas import SubmitRequest


def _wait(ctx, job_id, timeout=60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = ctx.db.get(job_id)
        if job.terminal:
            return job
        time.sleep(0.1)
    raise AssertionError("job never finished")


def test_worker_renders_and_writes_a_reproducible_sidecar(ctx):
    import json
    from pathlib import Path

    _batch, jobs = ctx.submit(SubmitRequest(
        model_id="mock", prompt="a quiet street",
        params={"width": 96, "height": 64, "num_frames": 3, "fps": 8},
    ))
    ctx.start()
    job = _wait(ctx, jobs[0].id)

    assert job.status == "done", job.error
    output = Path(job.output_path)
    assert output.exists() and output.stat().st_size > 0

    sidecar = json.loads(output.with_suffix(".json").read_text())
    assert sidecar["prompt"] == "a quiet street"
    assert sidecar["seed"] == job.seed
    assert sidecar["model"]["backend"] == "mock"


def test_mock_backend_is_deterministic_for_a_fixed_seed(ctx):
    from pathlib import Path

    outputs = []
    for _ in range(2):
        _batch, jobs = ctx.submit(SubmitRequest(
            model_id="mock", prompt="same prompt", seeds=[1234],
            params={"width": 64, "height": 64, "num_frames": 3},
        ))
        ctx.start()
        job = _wait(ctx, jobs[0].id)
        assert job.status == "done", job.error
        outputs.append(Path(job.output_path).read_bytes())
    assert outputs[0] == outputs[1]


def test_cancelling_a_queued_job_keeps_it_out_of_the_render_loop(ctx):
    _batch, jobs = ctx.submit(SubmitRequest(
        model_id="mock", prompt="cancel me", variants=3,
        params={"width": 64, "height": 64, "num_frames": 2},
    ))
    # Cancel before the worker ever starts, so nothing races us.
    assert ctx.worker.cancel(jobs[-1].id) is True
    assert ctx.db.get(jobs[-1].id).status == "cancelled"

    ctx.start()
    finished = _wait(ctx, jobs[0].id)
    assert finished.status == "done", finished.error
    assert ctx.db.get(jobs[-1].id).status == "cancelled"


def test_model_defaults_are_merged_under_request_params(ctx):
    from vidforge.config import ModelSpec

    ctx.settings.models["tiny"] = ModelSpec(
        id="tiny", backend="mock",
        defaults={"width": 64, "height": 64, "num_frames": 2, "fps": 8,
                  "negative_prompt": "blurry"},
    )
    _batch, jobs = ctx.submit(SubmitRequest(model_id="tiny", prompt="x",
                                            params={"width": 128}))
    job = jobs[0]
    assert job.params["width"] == 128       # request wins
    assert job.params["height"] == 64       # default fills in
    assert job.negative_prompt == "blurry"  # default negative applied


def test_a_failing_backend_marks_the_job_failed_without_killing_the_worker(ctx):
    from vidforge.config import ModelSpec

    ctx.settings.models["broken"] = ModelSpec(id="broken", backend="comfyui",
                                              workflow="does-not-exist.json")
    _batch, bad = ctx.submit(SubmitRequest(model_id="broken", prompt="x"))
    ctx.start()
    failed = _wait(ctx, bad[0].id)
    assert failed.status == "failed"
    assert failed.error

    _batch, good = ctx.submit(SubmitRequest(
        model_id="mock", prompt="still working",
        params={"width": 64, "height": 64, "num_frames": 2},
    ))
    assert _wait(ctx, good[0].id).status == "done"
