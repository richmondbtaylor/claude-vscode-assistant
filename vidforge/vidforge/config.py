"""Runtime configuration and the model registry.

Everything is file-driven so adding a checkpoint never means editing code:
drop an entry in ``$VIDFORGE_HOME/models.toml`` and restart.
"""

from __future__ import annotations

import os
import shutil
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent


def _home() -> Path:
    return Path(os.environ.get("VIDFORGE_HOME") or Path.home() / ".vidforge").expanduser()


@dataclass(slots=True)
class ModelSpec:
    """One generateable model, as declared in ``models.toml``."""

    id: str
    backend: str  # "diffusers" | "comfyui" | "mock"
    kind: str = "t2v"  # "t2v" (text to video) | "i2v" (image to video)
    label: str = ""

    # diffusers backend
    repo: str | None = None  # HF repo id or a local directory
    pipeline_class: str | None = None  # e.g. "WanPipeline", "LTXPipeline"
    dtype: str = "bfloat16"
    loras: list[dict] = field(default_factory=list)
    offload: bool = True  # sequential CPU offload; slower but fits smaller cards

    # comfyui backend
    workflow: str | None = None  # path to an API-format workflow JSON

    # per-model defaults merged under whatever the request sends
    defaults: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.label = self.label or self.id
        if self.kind not in ("t2v", "i2v"):
            raise ValueError(f"model {self.id!r}: kind must be 't2v' or 'i2v', got {self.kind!r}")


@dataclass(slots=True)
class Settings:
    home: Path
    host: str
    port: int
    device: str
    comfy_url: str
    models: dict[str, ModelSpec]

    @property
    def outputs_dir(self) -> Path:
        return self.home / "outputs"

    @property
    def wildcards_dir(self) -> Path:
        return self.home / "wildcards"

    @property
    def uploads_dir(self) -> Path:
        return self.home / "uploads"

    @property
    def db_path(self) -> Path:
        return self.home / "vidforge.db"

    @property
    def models_file(self) -> Path:
        return self.home / "models.toml"

    @property
    def consent_file(self) -> Path:
        return self.home / "consent.json"

    def ensure_dirs(self) -> None:
        for path in (self.home, self.outputs_dir, self.wildcards_dir, self.uploads_dir):
            path.mkdir(parents=True, exist_ok=True)

    def model(self, model_id: str) -> ModelSpec:
        try:
            return self.models[model_id]
        except KeyError:
            known = ", ".join(sorted(self.models)) or "<none>"
            raise KeyError(f"unknown model {model_id!r}; registered models: {known}") from None


def _seed_home(home: Path) -> None:
    """First run: copy the example registry and wildcards into VIDFORGE_HOME."""
    home.mkdir(parents=True, exist_ok=True)
    target = home / "models.toml"
    if not target.exists():
        example = PROJECT_DIR / "config" / "models.example.toml"
        if example.exists():
            shutil.copy(example, target)
    wildcards = home / "wildcards"
    wildcards.mkdir(exist_ok=True)
    shipped = PROJECT_DIR / "wildcards"
    if shipped.is_dir():
        for src in shipped.glob("*.txt"):
            dst = wildcards / src.name
            if not dst.exists():
                shutil.copy(src, dst)


def load_models(path: Path) -> dict[str, ModelSpec]:
    """Parse ``models.toml``. Bad entries are skipped loudly rather than fatally."""
    if not path.exists():
        return {}
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    specs: dict[str, ModelSpec] = {}
    for model_id, body in (raw.get("model") or {}).items():
        if not isinstance(body, dict):
            continue
        fields = {f for f in ModelSpec.__slots__ if f != "id"}
        kwargs = {k: v for k, v in body.items() if k in fields}
        try:
            specs[model_id] = ModelSpec(id=model_id, **kwargs)
        except (TypeError, ValueError) as exc:  # keep the rest of the registry usable
            print(f"vidforge: skipping model {model_id!r}: {exc}")
    return specs


def build_settings() -> Settings:
    home = _home()
    _seed_home(home)
    models = load_models(home / "models.toml")
    # The mock backend is always available: it makes the UI, the queue and the
    # tests runnable on a machine with no GPU and no weights downloaded.
    models.setdefault("mock", ModelSpec(id="mock", backend="mock", label="Mock (no GPU)"))
    settings = Settings(
        home=home,
        host=os.environ.get("VIDFORGE_HOST", "127.0.0.1"),
        port=int(os.environ.get("VIDFORGE_PORT", "8787")),
        device=os.environ.get("VIDFORGE_DEVICE", "auto"),
        comfy_url=os.environ.get("VIDFORGE_COMFY_URL", "http://127.0.0.1:8188").rstrip("/"),
        models=models,
    )
    settings.ensure_dirs()
    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return build_settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
