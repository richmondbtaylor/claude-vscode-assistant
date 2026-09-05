"""Machine setup: work out what this box can run, then get it there.

`vidforge setup` exists so getting from a clean checkout to a rendering GPU is
one command instead of an afternoon of reading install matrices. It detects the
accelerator, picks the matching torch wheel index, installs the extras, and
pre-fetches a model that actually fits the card it found.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

# Model suggestions keyed by the VRAM they realistically want.
_LADDER = (
    (22, "wan-14b", "Wan 2.2 14B - the good one"),
    (14, "wan-i2v", "Wan 2.1 I2V 14B - animate a still"),
    (10, "ltx", "LTX-Video - fastest iteration loop"),
    (6, "wan-1_3b", "Wan 2.1 T2V 1.3B - the sensible first download"),
)
_FALLBACK = ("mock", "no usable accelerator found - mock renders without one")


@dataclass(slots=True)
class Machine:
    system: str
    machine: str
    python: str
    vendor: str = "none"  # nvidia | amd | apple | none
    device_name: str = ""
    vram_gb: float = 0.0
    torch_version: str = ""
    torch_accelerated: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return bool(self.torch_version) and (self.torch_accelerated or self.vendor == "none")


def _nvidia() -> tuple[str, float] | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout.strip().splitlines()
    except (subprocess.SubprocessError, OSError):
        return None
    if not out:
        return None
    # Take the largest card if there are several; that is the one to plan for.
    best = ("", 0.0)
    for line in out:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            continue
        try:
            mib = float(parts[1])
        except ValueError:
            continue
        if mib > best[1]:
            best = (parts[0], mib)
    return (best[0], round(best[1] / 1024, 1)) if best[0] else None


def detect() -> Machine:
    info = Machine(
        system=platform.system(),
        machine=platform.machine(),
        python=platform.python_version(),
    )

    nvidia = _nvidia()
    if nvidia:
        info.vendor, info.device_name = "nvidia", nvidia[0]
        info.vram_gb = nvidia[1]
    elif info.system == "Darwin" and info.machine in ("arm64", "aarch64"):
        info.vendor, info.device_name = "apple", "Apple silicon (MPS)"
        # Unified memory: assume roughly half is usable for a model.
        info.vram_gb = round(_apple_memory_gb() / 2, 1)
    elif shutil.which("rocminfo"):
        info.vendor, info.device_name = "amd", "AMD (ROCm)"

    try:
        import torch

        info.torch_version = torch.__version__
        info.torch_accelerated = bool(
            torch.cuda.is_available()
            or (getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
        )
        if torch.cuda.is_available() and not info.vram_gb:
            props = torch.cuda.get_device_properties(0)
            info.device_name = info.device_name or props.name
            info.vram_gb = round(props.total_memory / 1024**3, 1)
    except ImportError:
        info.notes.append("torch is not installed")
    except Exception as exc:  # a broken torch install should still report
        info.notes.append(f"torch present but unusable: {exc}")

    if info.vendor != "none" and info.torch_version and not info.torch_accelerated:
        info.notes.append(
            f"a {info.vendor} device is present but torch cannot see it - "
            "this is usually a CPU-only torch build"
        )
    return info


def _apple_memory_gb() -> float:
    try:
        out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True,
                             text=True, timeout=10, check=True).stdout.strip()
        return float(out) / 1024**3
    except (subprocess.SubprocessError, OSError, ValueError):
        return 16.0


def torch_install(info: Machine) -> list[str]:
    """The pip arguments that get a working torch on this machine."""
    if info.vendor == "nvidia":
        # cu124 wheels cover every driver from 550 on, which is what a card
        # new enough to run a video model will have.
        return ["torch", "--index-url", "https://download.pytorch.org/whl/cu124"]
    if info.vendor == "amd":
        return ["torch", "--index-url", "https://download.pytorch.org/whl/rocm6.2"]
    if info.vendor == "apple":
        return ["torch"]  # MPS ships in the default wheel
    return ["torch", "--index-url", "https://download.pytorch.org/whl/cpu"]


def recommend(info: Machine) -> tuple[str, str]:
    if info.vendor == "none":
        return _FALLBACK
    for need, model_id, why in _LADDER:
        if info.vram_gb >= need:
            return model_id, why
    if info.vendor == "apple":
        return "wan-1_3b", "Apple silicon: small models only, and expect it to be slow"
    return _FALLBACK


def report(info: Machine) -> str:
    model_id, why = recommend(info)
    lines = [
        f"  platform     {info.system} {info.machine}, python {info.python}",
        f"  accelerator  {info.device_name or 'none detected'}"
        + (f"  ({info.vram_gb:g} GB)" if info.vram_gb else ""),
        f"  torch        {info.torch_version or 'not installed'}"
        + ("  [accelerated]" if info.torch_accelerated else ""),
        f"  suggested    {model_id}  - {why}",
    ]
    lines += [f"  note         {n}" for n in info.notes]
    return "\n".join(lines)


def _run(args: list[str], dry: bool) -> int:
    printable = " ".join(args)
    print(f"  $ {printable}")
    if dry:
        return 0
    return subprocess.call(args)


def _pip(dry: bool) -> list[str]:
    """Prefer uv when it is around; it is what this project is set up for."""
    if shutil.which("uv"):
        return ["uv", "pip", "install"]
    return [sys.executable, "-m", "pip", "install"]


def install(info: Machine, *, dry: bool = False, extras: bool = True) -> int:
    pip = _pip(dry)
    if not info.torch_accelerated or not info.torch_version:
        code = _run([*pip, *torch_install(info)], dry)
        if code != 0:
            return code
    if extras:
        return _run([*pip, "-e", ".[diffusers]"], dry)
    return 0


def prefetch(model_id: str, settings, *, dry: bool = False) -> int:
    """Pull a model's weights now, so the first render is not a 20 GB wait."""
    try:
        spec = settings.model(model_id)
    except KeyError as exc:
        print(f"  {exc}")
        return 2
    if spec.backend != "diffusers" or not spec.repo:
        print(f"  {model_id} needs no download ({spec.backend} backend)")
        return 0
    print(f"  fetching {spec.repo} ...")
    if dry:
        return 0
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(spec.repo)
    except ImportError:
        print("  huggingface_hub is missing; run the install step first")
        return 2
    except Exception as exc:
        print(f"  download failed: {exc}")
        return 2
    return 0


def doctor_json(info: Machine) -> str:
    model_id, why = recommend(info)
    payload = {
        "system": info.system, "machine": info.machine, "python": info.python,
        "vendor": info.vendor, "device": info.device_name, "vram_gb": info.vram_gb,
        "torch": info.torch_version, "accelerated": info.torch_accelerated,
        "ready": info.ready, "suggested_model": model_id, "reason": why,
        "notes": info.notes,
    }
    return json.dumps(payload, indent=2)
