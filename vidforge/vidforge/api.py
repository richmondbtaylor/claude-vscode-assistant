"""HTTP API + web UI."""

from __future__ import annotations

import mimetypes
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .backends import BackendUnavailable, get_backend
from .guardrails import GuardrailError
from .prompts import build_batch
from .schemas import ConsentRequest, PromptPreviewRequest, SubmitRequest, SubmitResponse
from .service import get_context

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = get_context()
    ctx.start()
    try:
        yield
    finally:
        ctx.shutdown()


app = FastAPI(title="vidforge", version="0.1.0", lifespan=lifespan)


@app.exception_handler(GuardrailError)
async def _guardrail_handler(_request, exc: GuardrailError):
    verdict = exc.verdict
    return JSONResponse(
        status_code=422,
        content={"error": verdict.message, "code": verdict.code, "matched": verdict.matched},
    )


# --- registry / status -----------------------------------------------------
@app.get("/api/models")
def list_models() -> list[dict]:
    ctx = get_context()
    return [
        {
            "id": spec.id,
            "label": spec.label,
            "backend": spec.backend,
            "kind": spec.kind,
            "repo": spec.repo,
            "defaults": spec.defaults,
        }
        for spec in sorted(ctx.settings.models.values(), key=lambda s: s.label.lower())
    ]


@app.get("/api/status")
def status() -> dict:
    ctx = get_context()
    backends = {}
    for name in {spec.backend for spec in ctx.settings.models.values()}:
        try:
            get_backend(name, ctx.settings).preflight()
            backends[name] = {"ready": True, "detail": ""}
        except BackendUnavailable as exc:
            backends[name] = {"ready": False, "detail": str(exc)}
    return {
        "worker": ctx.worker.status(),
        "counts": ctx.db.counts(),
        "backends": backends,
        "home": str(ctx.settings.home),
    }


@app.get("/api/wildcards")
def wildcards() -> dict[str, int]:
    return {name: len(values) for name, values in sorted(get_context().wildcards().items())}


# --- prompts ---------------------------------------------------------------
@app.post("/api/prompts/preview")
def preview_prompts(req: PromptPreviewRequest) -> dict:
    ctx = get_context()
    templates = [p.strip() for p in ([req.prompt] + req.prompts) if p and p.strip()]
    if not templates:
        raise HTTPException(400, "nothing to preview")
    items = build_batch(
        templates,
        variants=req.variants,
        seeds=req.seeds,
        expand_wildcards=req.expand_wildcards,
        wildcards=ctx.wildcards(),
    )
    return {
        "total": len(items),
        "items": [{"prompt": p, "seed": s} for p, s in items[: req.limit]],
    }


# --- generation ------------------------------------------------------------
@app.post("/api/generate", response_model=SubmitResponse)
def generate(req: SubmitRequest) -> SubmitResponse:
    ctx = get_context()
    try:
        batch_id, jobs = ctx.submit(req)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return SubmitResponse(batch_id=batch_id, jobs=jobs)


# --- jobs ------------------------------------------------------------------
@app.get("/api/jobs")
def list_jobs(
    status: str | None = None,
    batch_id: str | None = None,
    search: str | None = None,
    limit: int = 60,
    offset: int = 0,
) -> dict:
    ctx = get_context()
    jobs = ctx.db.list(
        status=status, batch_id=batch_id, search=search,
        limit=max(1, min(limit, 500)), offset=max(0, offset),
    )
    return {"jobs": [j.model_dump() for j in jobs], "counts": ctx.db.counts()}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = get_context().db.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    return job.model_dump()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    ctx = get_context()
    if ctx.db.get(job_id) is None:
        raise HTTPException(404, "no such job")
    return {"cancelled": ctx.worker.cancel(job_id)}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, files: bool = True) -> dict:
    ctx = get_context()
    job = ctx.db.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    if files:
        for candidate in (job.output_path, job.thumb_path):
            if candidate:
                path = Path(candidate)
                path.unlink(missing_ok=True)
                path.with_suffix(".json").unlink(missing_ok=True)
    return {"deleted": ctx.db.delete(job_id)}


@app.post("/api/queue/clear")
def clear_queue() -> dict:
    return {"cancelled": get_context().db.cancel_all_queued()}


# --- media -----------------------------------------------------------------
def _serve(path_str: str | None) -> FileResponse:
    ctx = get_context()
    if not path_str:
        raise HTTPException(404, "no file for this job yet")
    path = Path(path_str).resolve()
    # Only ever serve from inside VIDFORGE_HOME, whatever the database says.
    if not path.is_relative_to(ctx.settings.home.resolve()) or not path.exists():
        raise HTTPException(404, "file missing")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type)


@app.get("/media/{job_id}")
def media(job_id: str) -> FileResponse:
    job = get_context().db.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    return _serve(job.output_path)


@app.get("/media/{job_id}/thumb")
def media_thumb(job_id: str) -> FileResponse:
    job = get_context().db.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    return _serve(job.thumb_path or job.output_path)


@app.post("/api/uploads")
async def upload(file: UploadFile = File(...)) -> dict:
    ctx = get_context()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        raise HTTPException(400, "init images must be png, jpg, webp or bmp")
    name = f"{uuid.uuid4().hex[:12]}{suffix}"
    target = ctx.settings.uploads_dir / name
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"filename": name}


# --- consent register ------------------------------------------------------
@app.get("/api/consent")
def list_consent() -> list[dict]:
    return get_context().consent.list()


@app.post("/api/consent")
def add_consent(req: ConsentRequest) -> dict:
    try:
        return get_context().consent.add(req.subject, req.attested_by, req.note)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.delete("/api/consent/{consent_id}")
def delete_consent(consent_id: str) -> dict:
    if not get_context().consent.remove(consent_id):
        raise HTTPException(404, "no such consent record")
    return {"deleted": True}


# --- UI --------------------------------------------------------------------
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
