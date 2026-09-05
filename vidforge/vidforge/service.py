"""Submission pipeline: screen, expand, queue.

Shared by the HTTP API and the CLI so both enforce the same rules.
"""

from __future__ import annotations

import random
import uuid
from functools import lru_cache

from .config import Settings, get_settings
from .db import Database, utcnow
from .guardrails import ConsentStore, GuardrailError, Verdict, check
from .prompts import build_batch, load_wildcards
from .schemas import Job, SubmitRequest
from .worker import Worker


class AppContext:
    """Long-lived singletons: settings, database, worker, consent register."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.db = Database(self.settings.db_path)
        self.db.reset_orphans()
        self.consent = ConsentStore(self.settings.consent_file)
        self.worker = Worker(self.settings, self.db)

    def start(self) -> None:
        self.worker.start()

    def shutdown(self) -> None:
        self.worker.stop()

    def wildcards(self) -> dict[str, list[str]]:
        # Re-read each submit so editing a wildcard file takes effect without
        # a restart; these files are small.
        return load_wildcards(self.settings.wildcards_dir)

    def screen(self, req: SubmitRequest, prompt: str) -> Verdict:
        return check(
            prompt,
            identity_reference=req.identity_reference,
            consent_id=req.consent_id,
            consent_store=self.consent,
        )

    def expand(self, req: SubmitRequest, rng: random.Random | None = None) -> list[tuple[str, int]]:
        return build_batch(
            req.all_prompts(),
            variants=req.variants,
            seeds=req.seeds,
            expand_wildcards=req.expand_wildcards,
            wildcards=self.wildcards(),
            rng=rng,
        )

    def submit(self, req: SubmitRequest) -> tuple[str, list[Job]]:
        """Screen, expand and enqueue. Raises ``GuardrailError`` on a refusal."""
        spec = self.settings.model(req.model_id)  # KeyError -> 404 at the API edge

        # Screen the raw templates first, so an abusive template is refused
        # before it multiplies into a hundred queued jobs.
        for template in req.all_prompts():
            self.screen(req, template).raise_for_status()

        items = self.expand(req)
        if not items:
            raise ValueError("prompt expansion produced nothing to render")

        # Wildcards can introduce terms the template did not contain.
        for prompt, _seed in items:
            self.screen(req, prompt).raise_for_status()

        batch_id = uuid.uuid4().hex[:12]
        defaults = dict(spec.defaults)
        params = req.params.merged_with(defaults)
        negative = params.pop("negative_prompt", "") or ""

        jobs = [
            Job(
                id=uuid.uuid4().hex,
                batch_id=batch_id,
                model_id=spec.id,
                backend=spec.backend,
                prompt=prompt,
                negative_prompt=negative,
                seed=seed,
                params=params,
                label=req.label,
                created_at=utcnow(),
            )
            for prompt, seed in items
        ]
        self.db.add_jobs(jobs)
        self.worker.start()  # no-op if already running
        return batch_id, jobs


@lru_cache(maxsize=1)
def get_context() -> AppContext:
    return AppContext()


__all__ = ["AppContext", "get_context", "GuardrailError"]
