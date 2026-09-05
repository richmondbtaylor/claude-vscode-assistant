"""Background render worker.

One job at a time by design: a video model saturates the GPU, so running two
concurrently makes both slower and risks OOM. The queue is durable (SQLite),
so closing the browser - or the process - does not lose work.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from .backends import Cancelled, GenRequest, get_backend
from .config import Settings
from .db import Database, utcnow
from .schemas import Job

_IDLE_SLEEP = 0.5


class Worker:
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._cancel = threading.Event()
        self._current: str | None = None
        self._last_error: str | None = None

    # --- lifecycle --------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="vidforge-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        self._cancel.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    @property
    def current_job_id(self) -> str | None:
        return self._current

    def status(self) -> dict:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "current_job_id": self._current,
            "last_error": self._last_error,
        }

    def cancel(self, job_id: str) -> bool:
        """Cancel a queued job, or signal the running one to stop."""
        if self.db.cancel(job_id):
            return True
        if self._current == job_id:
            self._cancel.set()
            return True
        return False

    # --- loop -------------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            job = self.db.claim_next()
            if job is None:
                self._stop.wait(_IDLE_SLEEP)
                continue
            self._cancel.clear()
            self._current = job.id
            try:
                self._run(job)
            except Cancelled:
                self.db.update(job.id, status="cancelled", finished_at=utcnow())
            except Exception as exc:  # a bad model must not take the worker down
                self._last_error = f"{type(exc).__name__}: {exc}"
                self.db.update(
                    job.id,
                    status="failed",
                    error=_format_error(exc),
                    finished_at=utcnow(),
                )
            finally:
                self._current = None

    def _run(self, job: Job) -> None:
        spec = self.settings.model(job.model_id)
        backend = get_backend(spec.backend, self.settings)

        day = utcnow()[:10]
        out_dir = self.settings.outputs_dir / day
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{job.id}.mp4"

        request = GenRequest(
            job_id=job.id,
            model=spec,
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            seed=job.seed,
            out_path=out_path,
            params=job.params,
        )

        last = 0.0

        def on_progress(fraction: float) -> None:
            nonlocal last
            # Throttle writes: pipelines call back every step.
            if fraction - last >= 0.02 or fraction >= 1.0:
                last = fraction
                self.db.update(job.id, progress=round(min(1.0, max(0.0, fraction)), 4))

        result = backend.generate(request, on_progress, self._cancel)
        self._write_sidecar(job, spec, result.video_path)

        self.db.update(
            job.id,
            status="done",
            progress=1.0,
            output_path=str(result.video_path),
            thumb_path=str(result.thumb_path) if result.thumb_path else None,
            finished_at=utcnow(),
        )

    def _write_sidecar(self, job: Job, spec, video_path: Path) -> None:  # noqa: ANN001
        """Everything needed to reproduce this clip, next to the clip."""
        meta = {
            "id": job.id,
            "batch_id": job.batch_id,
            "label": job.label,
            "prompt": job.prompt,
            "negative_prompt": job.negative_prompt,
            "seed": job.seed,
            "model": {"id": spec.id, "backend": spec.backend, "kind": spec.kind,
                      "repo": spec.repo, "pipeline_class": spec.pipeline_class,
                      "loras": spec.loras, "workflow": spec.workflow},
            "params": job.params,
            "created_at": job.created_at,
            "rendered_at": utcnow(),
        }
        try:
            video_path.with_suffix(".json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
        except OSError:
            pass  # a missing sidecar must never fail an otherwise good render


def _format_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {str(exc).strip() or 'no detail'}"
