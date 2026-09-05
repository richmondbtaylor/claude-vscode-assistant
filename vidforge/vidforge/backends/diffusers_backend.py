"""Local inference through Hugging Face diffusers.

This is the backend that makes the app "uncensored" in the only sense that
actually matters technically: the weights run on your machine, and the
post-hoc `safety_checker` / `watermarker` modules that ship bolted onto some
pipelines are removed at load time (see ``_unfilter``). No prompt is sent
anywhere. What the model can express is then purely a function of the
checkpoint and LoRAs you choose.

Pipelines are addressed by class name so the registry can target whatever
diffusers supports - WanPipeline, LTXPipeline, CogVideoXPipeline,
HunyuanVideoPipeline, AnimateDiffPipeline, StableVideoDiffusionPipeline, ...
"""

from __future__ import annotations

import gc
import threading
from pathlib import Path
from typing import Any

from ..media import encode_video, write_thumbnail
from .base import Backend, BackendUnavailable, Cancelled, GenRequest, GenResult, ProgressFn

_DTYPES = {"bfloat16": "bfloat16", "bf16": "bfloat16", "float16": "float16",
           "fp16": "float16", "half": "float16", "float32": "float32", "fp32": "float32"}


def _unfilter(pipe: Any) -> list[str]:
    """Detach content filters and watermarkers from a loaded pipeline.

    Some pipelines (SD-derived image ones, Stable Video Diffusion) carry a
    NSFW classifier that blanks frames it dislikes, and an invisible
    watermarker that mutates output pixels. Both are post-processing bolted on
    around the model, both produce silent corruption of legitimate output, and
    neither is load-bearing for generation.
    """
    removed = []
    had_checker = getattr(pipe, "safety_checker", None) is not None
    targets = ["safety_checker", "watermarker", "image_watermarker"]
    if had_checker:
        # Only the checker's own preprocessor: other pipelines use
        # feature_extractor for image conditioning, which we must keep.
        targets.append("feature_extractor")
    for attr in targets:
        if getattr(pipe, attr, None) is not None:
            try:
                setattr(pipe, attr, None)
                removed.append(attr)
            except (AttributeError, ValueError):
                pass
    if hasattr(pipe, "requires_safety_checker"):
        try:
            pipe.requires_safety_checker = False
        except (AttributeError, ValueError):
            pass
    if hasattr(pipe, "config") and hasattr(pipe.config, "requires_safety_checker"):
        try:
            pipe.register_to_config(requires_safety_checker=False)
        except Exception:
            pass
    return removed


class DiffusersBackend(Backend):
    name = "diffusers"

    def __init__(self, settings) -> None:  # noqa: ANN001 - Settings, avoids a cycle
        super().__init__(settings)
        self._pipe: Any = None
        self._pipe_key: str | None = None
        self._lock = threading.Lock()

    # --- environment ------------------------------------------------------
    def preflight(self) -> None:
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
        except ImportError as exc:
            raise BackendUnavailable(
                "diffusers backend needs torch + diffusers. Install torch for your GPU "
                "first (https://pytorch.org/get-started/locally/), then "
                "`uv pip install -e '.[diffusers]'`."
            ) from exc

    def _device(self) -> str:
        import torch

        choice = (self.settings.device or "auto").lower()
        if choice != "auto":
            return choice
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    # --- pipeline loading -------------------------------------------------
    def _load(self, spec) -> Any:  # noqa: ANN001 - ModelSpec
        import diffusers
        import torch

        key = f"{spec.id}:{spec.repo}:{spec.pipeline_class}:{spec.dtype}"
        if self._pipe is not None and self._pipe_key == key:
            return self._pipe

        self._release()

        if not spec.pipeline_class:
            raise BackendUnavailable(f"model {spec.id!r} needs a `pipeline_class` in models.toml")
        try:
            pipeline_cls = getattr(diffusers, spec.pipeline_class)
        except AttributeError as exc:
            raise BackendUnavailable(
                f"diffusers has no pipeline named {spec.pipeline_class!r}; "
                "check the spelling or upgrade diffusers"
            ) from exc

        dtype = getattr(torch, _DTYPES.get((spec.dtype or "").lower(), "bfloat16"))
        source = spec.repo or ""
        if not source:
            raise BackendUnavailable(f"model {spec.id!r} needs a `repo` (HF id or local path)")

        if source.endswith((".safetensors", ".ckpt")) and hasattr(pipeline_cls, "from_single_file"):
            pipe = pipeline_cls.from_single_file(source, torch_dtype=dtype)
        else:
            pipe = pipeline_cls.from_pretrained(source, torch_dtype=dtype)

        _unfilter(pipe)

        for lora in spec.loras or []:
            repo = lora.get("repo") or lora.get("path")
            if not repo:
                continue
            pipe.load_lora_weights(repo, weight_name=lora.get("weight_name"),
                                   adapter_name=lora.get("name"))
            scale = lora.get("weight", lora.get("scale"))
            if scale is not None and hasattr(pipe, "set_adapters"):
                pipe.set_adapters([lora.get("name") or Path(str(repo)).stem], [float(scale)])

        device = self._device()
        if spec.offload and device == "cuda" and hasattr(pipe, "enable_model_cpu_offload"):
            # Keeps peak VRAM near one module's worth; the alternative is OOM
            # on anything under ~24GB for current video models.
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(device)

        vae = getattr(pipe, "vae", None)
        for method in ("enable_tiling", "enable_slicing"):
            if vae is not None and hasattr(vae, method):
                getattr(vae, method)()

        self._pipe, self._pipe_key = pipe, key
        return pipe

    def _release(self) -> None:
        if self._pipe is None:
            return
        self._pipe = None
        self._pipe_key = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    # --- generation -------------------------------------------------------
    def generate(
        self, req: GenRequest, on_progress: ProgressFn, cancel: threading.Event
    ) -> GenResult:
        self.preflight()
        import torch

        with self._lock:
            pipe = self._load(req.model)

            steps = int(req.get("steps", 30))
            kwargs: dict[str, Any] = {
                "prompt": req.prompt,
                "num_inference_steps": steps,
                "generator": torch.Generator("cpu").manual_seed(req.seed),
            }
            if req.negative_prompt:
                kwargs["negative_prompt"] = req.negative_prompt
            for key, name in (
                ("width", "width"), ("height", "height"),
                ("num_frames", "num_frames"), ("guidance_scale", "guidance_scale"),
            ):
                value = req.params.get(key)
                if value is not None:
                    kwargs[name] = value
            kwargs.update(req.get("extra", {}) or {})

            if req.model.kind == "i2v":
                init = req.params.get("init_image")
                if not init:
                    raise ValueError(f"model {req.model.id!r} is image-to-video: an init image is required")
                from PIL import Image

                path = Path(init)
                if not path.is_absolute():
                    path = self.settings.uploads_dir / path
                if not path.exists():
                    raise FileNotFoundError(f"init image not found: {path}")
                kwargs["image"] = Image.open(path).convert("RGB")

            # Drop anything this pipeline's signature does not accept, so one
            # registry can drive pipelines with quite different call surfaces.
            accepted = _accepted(pipe)
            if accepted:
                kwargs = {k: v for k, v in kwargs.items() if k in accepted}

            def _step(pipeline, step: int, timestep, callback_kwargs):  # noqa: ANN001
                if cancel.is_set():
                    raise Cancelled("cancelled by operator")
                on_progress(min(0.99, (step + 1) / max(1, steps)))
                return callback_kwargs

            if "callback_on_step_end" in accepted or not accepted:
                kwargs["callback_on_step_end"] = _step

            self.check_cancelled(cancel)
            result = pipe(**kwargs)

        frames = _extract_frames(result)
        video = encode_video(frames, req.out_path, fps=int(req.get("fps", 16)))
        thumb = write_thumbnail(frames, video, req.out_path.with_suffix(".jpg"))
        on_progress(1.0)
        return GenResult(video_path=video, thumb_path=thumb)


def _accepted(pipe: Any) -> set[str]:
    import inspect

    try:
        return set(inspect.signature(pipe.__call__).parameters)
    except (TypeError, ValueError):
        return set()


def _extract_frames(result: Any) -> list[Any]:
    frames = getattr(result, "frames", None)
    if frames is None:
        frames = getattr(result, "images", None)
    if frames is None:
        raise RuntimeError("pipeline returned no frames or images")
    # video pipelines return a batch: frames[0] is the clip
    if len(frames) and isinstance(frames[0], (list, tuple)):
        return list(frames[0])
    try:
        import numpy as np

        if isinstance(frames, np.ndarray) and frames.ndim == 5:
            return list(frames[0])
    except ImportError:
        pass
    return list(frames)
