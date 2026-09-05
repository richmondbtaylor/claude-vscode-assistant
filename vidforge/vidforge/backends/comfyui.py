"""Drive a locally running ComfyUI instance over its HTTP API.

For most people this is the practical path: ComfyUI already has the node
ecosystem for Wan / LTX / Hunyuan video plus LoRA stacking, and it applies no
content filtering of its own. vidforge adds what ComfyUI lacks - a durable
queue, batch prompt expansion, a searchable gallery and reproducible metadata.

Workflows are plain "Save (API Format)" exports with placeholder tokens:

    "text": "%prompt%", "seed": "%seed%", "width": "%width%"

Any token whose value is exactly the placeholder is substituted with the typed
value (int/float), otherwise it is interpolated into the surrounding string.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from ..media import write_thumbnail
from .base import Backend, BackendUnavailable, Cancelled, GenRequest, GenResult, ProgressFn

_VIDEO_KEYS = ("gifs", "videos", "images")
_POLL_SECONDS = 1.0


def substitute(node: Any, values: dict[str, Any]) -> Any:
    """Recursively replace ``%token%`` placeholders inside a workflow graph."""
    if isinstance(node, dict):
        return {k: substitute(v, values) for k, v in node.items()}
    if isinstance(node, list):
        return [substitute(v, values) for v in node]
    if isinstance(node, str):
        for key, value in values.items():
            token = f"%{key}%"
            if node == token:
                return value  # keep the native type (int seed, float cfg, ...)
            if token in node:
                node = node.replace(token, str(value))
        return node
    return node


class ComfyBackend(Backend):
    name = "comfyui"

    def __init__(self, settings) -> None:  # noqa: ANN001 - Settings
        super().__init__(settings)
        self.base_url = settings.comfy_url
        self.client_id = uuid.uuid4().hex

    def _client(self, timeout: float = 30.0) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=timeout)

    def preflight(self) -> None:
        try:
            with self._client(timeout=5.0) as client:
                client.get("/system_stats").raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise BackendUnavailable(
                f"no ComfyUI at {self.base_url} - start it (`python main.py --listen`) "
                "or set VIDFORGE_COMFY_URL"
            ) from exc

    # --- workflow ---------------------------------------------------------
    def _workflow(self, req: GenRequest) -> dict:
        if not req.model.workflow:
            raise BackendUnavailable(
                f"model {req.model.id!r} needs a `workflow` path (a ComfyUI API-format export)"
            )
        path = Path(req.model.workflow).expanduser()
        if not path.is_absolute():
            path = self.settings.home / path
        if not path.exists():
            raise BackendUnavailable(f"workflow not found: {path}")
        graph = json.loads(path.read_text(encoding="utf-8"))
        if "prompt" in graph and "nodes" not in graph:  # tolerate a wrapped export
            graph = graph["prompt"]
        values = {
            "prompt": req.prompt,
            "negative_prompt": req.negative_prompt,
            "seed": int(req.seed),
            "steps": int(req.get("steps", 25)),
            "cfg": float(req.get("guidance_scale", 6.0)),
            "guidance_scale": float(req.get("guidance_scale", 6.0)),
            "width": int(req.get("width", 832)),
            "height": int(req.get("height", 480)),
            "num_frames": int(req.get("num_frames", 81)),
            "fps": int(req.get("fps", 16)),
            "init_image": str(req.params.get("init_image") or ""),
        }
        return substitute(graph, values)

    # --- execution --------------------------------------------------------
    def generate(
        self, req: GenRequest, on_progress: ProgressFn, cancel: threading.Event
    ) -> GenResult:
        self.preflight()
        graph = self._workflow(req)

        with self._client() as client:
            response = client.post(
                "/prompt", json={"prompt": graph, "client_id": self.client_id}
            )
            if response.status_code >= 400:
                raise RuntimeError(f"ComfyUI rejected the workflow: {response.text[:800]}")
            prompt_id = response.json()["prompt_id"]

            history = self._await_result(client, prompt_id, on_progress, cancel)
            outputs = history.get("outputs") or {}
            file_ref = _first_output(outputs)
            if file_ref is None:
                raise RuntimeError(
                    "the workflow finished but produced no video output - make sure it ends "
                    "in a saving node (e.g. VHS_VideoCombine or SaveAnimatedWEBP)"
                )
            video = self._download(client, file_ref, req.out_path)

        thumb = write_thumbnail(None, video, req.out_path.with_suffix(".jpg"))
        on_progress(1.0)
        return GenResult(video_path=video, thumb_path=thumb)

    def _await_result(
        self, client: httpx.Client, prompt_id: str, on_progress: ProgressFn,
        cancel: threading.Event,
    ) -> dict:
        # ComfyUI streams fine-grained progress over its websocket; polling
        # history keeps this dependency-free, so progress here is coarse:
        # it creeps toward 0.9 and snaps to 1.0 on completion.
        started = time.monotonic()
        while True:
            if cancel.is_set():
                try:
                    client.post("/interrupt")
                except httpx.HTTPError:
                    pass
                raise Cancelled("cancelled by operator")

            entry = client.get(f"/history/{prompt_id}").json().get(prompt_id)
            if entry:
                status = (entry.get("status") or {}).get("status_str")
                if status == "error":
                    raise RuntimeError(_comfy_error(entry))
                if entry.get("outputs"):
                    return entry

            elapsed = time.monotonic() - started
            on_progress(min(0.9, elapsed / (elapsed + 45)))
            time.sleep(_POLL_SECONDS)

    def _download(self, client: httpx.Client, ref: dict, out_path: Path) -> Path:
        params = {
            "filename": ref.get("filename", ""),
            "subfolder": ref.get("subfolder", ""),
            "type": ref.get("type", "output"),
        }
        response = client.get("/view", params=params, timeout=300.0)
        response.raise_for_status()
        suffix = Path(params["filename"]).suffix or out_path.suffix
        target = out_path.with_suffix(suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return target

    # --- helpers ----------------------------------------------------------
    def upload_image(self, path: Path) -> str:
        """Push a local init image into ComfyUI's input folder; returns its name."""
        with self._client(timeout=120.0) as client, path.open("rb") as fh:
            response = client.post(
                "/upload/image",
                files={"image": (path.name, fh, "application/octet-stream")},
                data={"overwrite": "true"},
            )
            response.raise_for_status()
        return response.json().get("name", path.name)


def _first_output(outputs: dict) -> dict | None:
    for node in outputs.values():
        for key in _VIDEO_KEYS:
            entries = node.get(key)
            if entries:
                return entries[0]
    return None


def _comfy_error(entry: dict) -> str:
    for kind, payload in (entry.get("status") or {}).get("messages", []):
        if kind == "execution_error":
            node = payload.get("node_type", "?")
            return f"ComfyUI node {node} failed: {payload.get('exception_message', 'unknown error')}"
    return "ComfyUI reported an execution error"
