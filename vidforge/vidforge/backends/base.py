"""Backend contract shared by the mock, diffusers and ComfyUI implementations."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..config import ModelSpec, Settings


class Cancelled(Exception):
    """Raised by a backend when the worker asks it to stop mid-generation."""


class BackendUnavailable(Exception):
    """Raised by ``preflight`` when the backend cannot run on this machine."""


@dataclass(slots=True)
class GenRequest:
    job_id: str
    model: ModelSpec
    prompt: str
    negative_prompt: str
    seed: int
    out_path: Path
    params: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        value = self.params.get(key, default)
        return default if value is None else value


@dataclass(slots=True)
class GenResult:
    video_path: Path
    thumb_path: Path | None = None


ProgressFn = Callable[[float], None]


class Backend(ABC):
    name: str = "base"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def preflight(self) -> None:
        """Raise ``BackendUnavailable`` if this backend cannot serve requests."""

    @abstractmethod
    def generate(
        self, req: GenRequest, on_progress: ProgressFn, cancel: threading.Event
    ) -> GenResult:
        ...

    @staticmethod
    def check_cancelled(cancel: threading.Event) -> None:
        if cancel.is_set():
            raise Cancelled("cancelled by operator")
