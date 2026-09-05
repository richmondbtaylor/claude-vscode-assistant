import time

import pytest
from fastapi.testclient import TestClient

from vidforge.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def wait_for(client, job_id, timeout=60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "failed", "cancelled"):
            return job
        time.sleep(0.2)
    raise AssertionError(f"job {job_id} never finished; last status {job['status']}")


def test_models_include_the_always_available_mock(client):
    ids = {m["id"] for m in client.get("/api/models").json()}
    assert "mock" in ids


def test_status_reports_worker_and_backends(client):
    body = client.get("/api/status").json()
    assert body["backends"]["mock"]["ready"] is True
    assert "counts" in body and "worker" in body


def test_generate_renders_end_to_end(client):
    response = client.post("/api/generate", json={
        "model_id": "mock",
        "prompt": "a slow dolly through an empty arcade",
        "params": {"width": 128, "height": 96, "num_frames": 4, "fps": 8},
    })
    assert response.status_code == 200, response.text
    job_id = response.json()["jobs"][0]["id"]

    job = wait_for(client, job_id)
    assert job["status"] == "done", job.get("error")
    assert job["output_path"] and job["progress"] == 1.0

    video = client.get(f"/media/{job_id}")
    assert video.status_code == 200
    assert len(video.content) > 0
    assert client.get(f"/media/{job_id}/thumb").status_code == 200


def test_batch_expansion_queues_one_job_per_seed(client):
    response = client.post("/api/generate", json={
        "model_id": "mock",
        "prompt": "a {red|blue} car at night",
        "variants": 3,
        "params": {"width": 64, "height": 64, "num_frames": 2},
    })
    jobs = response.json()["jobs"]
    assert len(jobs) == 3
    assert len({j["seed"] for j in jobs}) == 3
    assert all(("red car" in j["prompt"]) or ("blue car" in j["prompt"]) for j in jobs)


def test_guardrail_refusal_is_a_422_with_a_reason(client):
    response = client.post("/api/generate", json={
        "model_id": "mock", "prompt": "nude schoolgirl",
    })
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "minor_sexual_content"
    assert body["error"]


def test_nothing_is_queued_when_a_prompt_is_refused(client):
    before = client.get("/api/jobs?limit=500").json()["counts"]
    client.post("/api/generate", json={"model_id": "mock", "prompt": "lolicon", "variants": 50})
    after = client.get("/api/jobs?limit=500").json()["counts"]
    assert before == after


def test_unknown_model_is_a_404(client):
    response = client.post("/api/generate", json={"model_id": "nope", "prompt": "x"})
    assert response.status_code == 404


def test_empty_prompt_is_rejected(client):
    assert client.post("/api/generate", json={"model_id": "mock", "prompt": "  "}).status_code == 422


def test_prompt_preview_does_not_queue(client):
    before = client.get("/api/jobs?limit=500").json()["counts"]
    body = client.post("/api/prompts/preview", json={
        "prompt": "a {red|blue|green} car", "variants": 4,
    }).json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    assert client.get("/api/jobs?limit=500").json()["counts"] == before


def test_consent_records_round_trip_through_the_api(client):
    created = client.post("/api/consent", json={
        "subject": "Jane Doe", "attested_by": "Jane Doe", "note": "release on file",
    }).json()
    assert created["id"]
    assert any(r["id"] == created["id"] for r in client.get("/api/consent").json())

    # identity reference is refused without a consent id, accepted with one
    payload = {"model_id": "mock", "prompt": "a portrait, slow pan",
               "identity_reference": True,
               "params": {"width": 64, "height": 64, "num_frames": 2}}
    assert client.post("/api/generate", json=payload).status_code == 422
    payload["consent_id"] = created["id"]
    assert client.post("/api/generate", json=payload).status_code == 200

    assert client.delete(f"/api/consent/{created['id']}").status_code == 200
    assert client.delete(f"/api/consent/{created['id']}").status_code == 404


def test_media_404s_for_unknown_job(client):
    assert client.get("/media/deadbeef").status_code == 404


def test_ui_is_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "vidforge" in response.text
