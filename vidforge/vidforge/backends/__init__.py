"""Backend registry."""

from __future__ import annotations

from ..config import Settings
from .base import Backend, BackendUnavailable, Cancelled, GenRequest, GenResult

__all__ = [
    "Backend", "BackendUnavailable", "Cancelled", "GenRequest", "GenResult",
    "get_backend", "available_backends",
]

_CACHE: dict[tuple[int, str], Backend] = {}


def available_backends() -> tuple[str, ...]:
    return ("mock", "diffusers", "comfyui")


def get_backend(name: str, settings: Settings) -> Backend:
    """Build (and cache) a backend. Cached so diffusers keeps its loaded pipeline."""
    key = (id(settings), name)
    if key in _CACHE:
        return _CACHE[key]

    if name == "mock":
        from .mock import MockBackend as cls
    elif name == "diffusers":
        from .diffusers_backend import DiffusersBackend as cls
    elif name == "comfyui":
        from .comfyui import ComfyBackend as cls
    else:
        raise BackendUnavailable(
            f"unknown backend {name!r}; expected one of {', '.join(available_backends())}"
        )

    backend = cls(settings)
    _CACHE[key] = backend
    return backend
