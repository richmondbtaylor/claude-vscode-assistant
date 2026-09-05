"""SQLite job store.

One row per generated clip, holding the full prompt/seed/params it came from,
so anything in the gallery can be reproduced exactly.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import Job

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,
    batch_id        TEXT NOT NULL,
    status          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    backend         TEXT NOT NULL,
    prompt          TEXT NOT NULL,
    negative_prompt TEXT NOT NULL DEFAULT '',
    seed            INTEGER NOT NULL,
    params          TEXT NOT NULL DEFAULT '{}',
    label           TEXT NOT NULL DEFAULT '',
    progress        REAL NOT NULL DEFAULT 0,
    output_path     TEXT,
    thumb_path      TEXT,
    error           TEXT,
    created_at      TEXT NOT NULL,
    started_at      TEXT,
    finished_at     TEXT
);
CREATE INDEX IF NOT EXISTS jobs_status_idx  ON jobs(status, created_at);
CREATE INDEX IF NOT EXISTS jobs_batch_idx   ON jobs(batch_id);
CREATE INDEX IF NOT EXISTS jobs_created_idx ON jobs(created_at DESC);
"""

_MUTABLE = (
    "status",
    "progress",
    "output_path",
    "thumb_path",
    "error",
    "started_at",
    "finished_at",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    # --- reads ------------------------------------------------------------
    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        data = dict(row)
        data["params"] = json.loads(data.get("params") or "{}")
        return Job(**data)

    def get(self, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def list(
        self,
        *,
        status: str | None = None,
        batch_id: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        sql = "SELECT * FROM jobs"
        where, args = [], []
        if status:
            where.append("status = ?")
            args.append(status)
        if batch_id:
            where.append("batch_id = ?")
            args.append(batch_id)
        if search:
            where.append("(prompt LIKE ? OR label LIKE ?)")
            args += [f"%{search}%", f"%{search}%"]
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?"
        args += [limit, offset]
        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._row_to_job(r) for r in rows]

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}

    # --- writes -----------------------------------------------------------
    def add_jobs(self, jobs: list[Job]) -> None:
        if not jobs:
            return
        rows = [
            (
                j.id, j.batch_id, j.status, j.model_id, j.backend, j.prompt,
                j.negative_prompt, j.seed, json.dumps(j.params), j.label, j.progress,
                j.output_path, j.thumb_path, j.error,
                j.created_at or utcnow(), j.started_at, j.finished_at,
            )
            for j in jobs
        ]
        columns = (
            "id, batch_id, status, model_id, backend, prompt, negative_prompt, seed, "
            "params, label, progress, output_path, thumb_path, error, created_at, "
            "started_at, finished_at"
        )
        placeholders = ", ".join("?" * len(columns.split(",")))
        with self._lock, self._connect() as conn:
            conn.executemany(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", rows)

    def update(self, job_id: str, **fields: Any) -> None:
        fields = {k: v for k, v in fields.items() if k in _MUTABLE}
        if not fields:
            return
        assignments = ", ".join(f"{k} = ?" for k in fields)
        with self._lock, self._connect() as conn:
            conn.execute(
                f"UPDATE jobs SET {assignments} WHERE id = ?", [*fields.values(), job_id]
            )

    def claim_next(self) -> Job | None:
        """Atomically move the oldest queued job to ``running`` and return it."""
        with self._lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE status = 'queued' "
                    "ORDER BY created_at, rowid LIMIT 1"
                ).fetchone()
                if row is None:
                    conn.execute("COMMIT")
                    return None
                started = utcnow()
                conn.execute(
                    "UPDATE jobs SET status='running', started_at=? WHERE id=?",
                    (started, row["id"]),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        job = self._row_to_job(row)
        job.status = "running"
        job.started_at = started
        return job

    def cancel(self, job_id: str) -> bool:
        """Cancel a *queued* job outright. Running jobs are stopped by the worker."""
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='cancelled', finished_at=? "
                "WHERE id=? AND status='queued'",
                (utcnow(), job_id),
            )
        return cur.rowcount > 0

    def cancel_all_queued(self) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='cancelled', finished_at=? WHERE status='queued'",
                (utcnow(),),
            )
        return cur.rowcount

    def delete(self, job_id: str) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cur.rowcount > 0

    def reset_orphans(self) -> int:
        """Jobs left ``running`` by a killed process can never finish - fail them."""
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='failed', error=?, finished_at=? WHERE status='running'",
                ("interrupted: vidforge restarted while this job was running", utcnow()),
            )
        return cur.rowcount
