"""Request/response models for the API and the queue."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

JobStatus = Literal["queued", "running", "done", "failed", "cancelled"]


class GenParams(BaseModel):
    """Generation knobs. Anything omitted falls back to the model's defaults."""

    width: int | None = Field(default=None, ge=64, le=4096)
    height: int | None = Field(default=None, ge=64, le=4096)
    num_frames: int | None = Field(default=None, ge=1, le=1024)
    fps: int | None = Field(default=None, ge=1, le=120)
    steps: int | None = Field(default=None, ge=1, le=300)
    guidance_scale: float | None = Field(default=None, ge=0, le=40)
    negative_prompt: str = ""
    init_image: str | None = None  # filename inside VIDFORGE_HOME/uploads, for i2v
    loras: list[dict[str, Any]] | None = None  # [{"repo": "...", "weight": 0.8}]
    extra: dict[str, Any] = Field(default_factory=dict)  # backend-specific passthrough

    def merged_with(self, defaults: dict[str, Any]) -> dict[str, Any]:
        out = dict(defaults)
        for key, value in self.model_dump().items():
            if key == "extra":
                out.setdefault("extra", {})
                out["extra"] = {**out.get("extra", {}), **value}
            elif value not in (None, "", []):
                out[key] = value
        return out


class PromptItem(BaseModel):
    """A concrete clip: no expansion, its own seed and setting overrides."""

    prompt: str
    seed: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class SubmitRequest(BaseModel):
    """One submission expands into N queued jobs."""

    model_id: str = "mock"
    prompt: str = ""
    prompts: list[str] = Field(default_factory=list)
    # Already-resolved clips, e.g. an export composed elsewhere. Items skip
    # wildcard expansion and keep their own seed, so a batch round-trips.
    items: list[PromptItem] = Field(default_factory=list)
    params: GenParams = Field(default_factory=GenParams)

    # batch expansion
    expand_wildcards: bool = True
    variants: int = Field(default=1, ge=1, le=200)  # random seeds per prompt
    seeds: list[int] = Field(default_factory=list)  # explicit seeds override variants

    # likeness controls
    identity_reference: bool = False
    consent_id: str | None = None

    label: str = ""

    @model_validator(mode="after")
    def _need_a_prompt(self) -> SubmitRequest:
        has_item = any(i.prompt.strip() for i in self.items)
        if not self.prompt.strip() and not any(p.strip() for p in self.prompts) and not has_item:
            raise ValueError("provide 'prompt', a non-empty 'prompts' list, or 'items'")
        return self

    def all_prompts(self) -> list[str]:
        out = [p.strip() for p in ([self.prompt] + self.prompts) if p and p.strip()]
        return out


class Job(BaseModel):
    id: str
    batch_id: str
    status: JobStatus = "queued"
    model_id: str
    backend: str
    prompt: str
    negative_prompt: str = ""
    seed: int
    params: dict[str, Any] = Field(default_factory=dict)
    label: str = ""
    progress: float = 0.0
    output_path: str | None = None
    thumb_path: str | None = None
    error: str | None = None
    created_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def terminal(self) -> bool:
        return self.status in ("done", "failed", "cancelled")


class SubmitResponse(BaseModel):
    batch_id: str
    jobs: list[Job]


class ConsentRequest(BaseModel):
    subject: str
    attested_by: str
    note: str = ""


class PromptPreviewRequest(BaseModel):
    prompt: str = ""
    prompts: list[str] = Field(default_factory=list)
    variants: int = Field(default=1, ge=1, le=200)
    seeds: list[int] = Field(default_factory=list)
    expand_wildcards: bool = True
    limit: int = Field(default=25, ge=1, le=500)
