from vidforge.db import Database, utcnow
from vidforge.schemas import Job


def make_job(db: Database, prompt: str = "hello", batch: str = "b1") -> Job:
    import uuid

    job = Job(
        id=uuid.uuid4().hex, batch_id=batch, model_id="mock", backend="mock",
        prompt=prompt, seed=1, created_at=utcnow(),
    )
    db.add_jobs([job])
    return job


def test_claim_next_is_fifo_and_marks_running(tmp_path):
    db = Database(tmp_path / "t.db")
    first = make_job(db, "first")
    make_job(db, "second")

    claimed = db.claim_next()
    assert claimed.id == first.id
    assert claimed.status == "running"
    assert db.get(first.id).status == "running"


def test_claim_next_returns_none_when_empty(tmp_path):
    assert Database(tmp_path / "t.db").claim_next() is None


def test_cancel_only_applies_to_queued(tmp_path):
    db = Database(tmp_path / "t.db")
    job = make_job(db)
    assert db.cancel(job.id) is True
    assert db.get(job.id).status == "cancelled"
    assert db.cancel(job.id) is False


def test_reset_orphans_fails_stuck_running_jobs(tmp_path):
    db = Database(tmp_path / "t.db")
    make_job(db)
    db.claim_next()
    assert db.reset_orphans() == 1
    assert db.list(status="failed")[0].error.startswith("interrupted")


def test_search_and_counts(tmp_path):
    db = Database(tmp_path / "t.db")
    make_job(db, "a neon alley")
    make_job(db, "a quiet forest")
    assert len(db.list(search="neon")) == 1
    assert db.counts() == {"queued": 2}


def test_params_roundtrip_as_json(tmp_path):
    db = Database(tmp_path / "t.db")
    import uuid

    job = Job(id=uuid.uuid4().hex, batch_id="b", model_id="mock", backend="mock",
              prompt="p", seed=3, params={"width": 512, "extra": {"a": 1}}, created_at=utcnow())
    db.add_jobs([job])
    assert db.get(job.id).params == {"width": 512, "extra": {"a": 1}}
