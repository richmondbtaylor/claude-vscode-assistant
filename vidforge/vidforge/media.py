"""Frame encoding helpers.

Prefers a real MP4 (imageio-ffmpeg, then a system ffmpeg) and degrades to an
animated WebP so the app still produces something watchable on a box with no
ffmpeg installed.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

Frame = Any  # numpy array or PIL.Image


def _to_pil(frame: Frame):
    from PIL import Image

    if isinstance(frame, Image.Image):
        return frame.convert("RGB")
    return Image.fromarray(frame).convert("RGB")


def _encode_imageio(frames: Sequence[Frame], out: Path, fps: int) -> bool:
    try:
        import imageio.v3 as iio
        import numpy as np
    except ImportError:
        return False
    try:
        stack = np.stack([np.asarray(_to_pil(f)) for f in frames])
        iio.imwrite(out, stack, fps=fps, codec="libx264", macro_block_size=None)
        return out.exists() and out.stat().st_size > 0
    except Exception:
        return False


# Tried in order. Most builds have libx264; the fallbacks keep a stripped
# ffmpeg (no x264) from silently demoting the whole app to animated WebP.
_CODECS = (
    ("libx264", ".mp4", ["-pix_fmt", "yuv420p"]),
    ("libvpx-vp9", ".webm", ["-pix_fmt", "yuv420p"]),
    ("libvpx", ".webm", ["-pix_fmt", "yuv420p"]),
    ("mpeg4", ".mp4", ["-q:v", "3"]),
)


def _png_bytes(frames: Sequence[Frame]) -> list[bytes]:
    import io

    out = []
    for frame in frames:
        buffer = io.BytesIO()
        _to_pil(frame).save(buffer, "PNG")
        out.append(buffer.getvalue())
    return out


def _encode_ffmpeg(frames: Sequence[Frame], out: Path, fps: int) -> Path | None:
    """Pipe PNG frames into ffmpeg over stdin.

    image2pipe is present in essentially every build - including the stripped
    ones that ship without the image2 (numbered-file) demuxer - and it avoids
    writing a temp PNG per frame.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    payload = _png_bytes(frames)

    for codec, suffix, extra in _CODECS:
        target = out.with_suffix(suffix)
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "image2pipe", "-c:v", "png", "-framerate", str(fps), "-i", "-",
            "-c:v", codec, *extra,
            # h264/vp9 need even dimensions; pad rather than crop so nothing
            # the model generated is thrown away
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            str(target),
        ]
        try:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with proc:
                for chunk in payload:
                    proc.stdin.write(chunk)
                proc.stdin.close()
                proc.wait(timeout=600)
        except (subprocess.SubprocessError, OSError, BrokenPipeError):
            target.unlink(missing_ok=True)
            continue
        if proc.returncode == 0 and target.exists() and target.stat().st_size > 0:
            return target
        target.unlink(missing_ok=True)
    return None


def _encode_webp(frames: Sequence[Frame], out: Path, fps: int) -> Path:
    images = [_to_pil(f) for f in frames]
    target = out.with_suffix(".webp")
    images[0].save(
        target,
        save_all=True,
        append_images=images[1:],
        duration=max(1, int(1000 / max(1, fps))),
        loop=0,
        quality=90,
    )
    return target


def encode_video(frames: Sequence[Frame], out_path: Path, fps: int = 16) -> Path:
    """Write ``frames`` to ``out_path``. Returns the path actually written."""
    if not frames:
        raise ValueError("nothing to encode: the pipeline returned zero frames")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if _encode_imageio(frames, out_path, fps):
        return out_path
    via_ffmpeg = _encode_ffmpeg(frames, out_path, fps)
    if via_ffmpeg is not None:
        return via_ffmpeg
    return _encode_webp(frames, out_path, fps)


def write_thumbnail(frames: Sequence[Frame] | None, video_path: Path, thumb_path: Path) -> Path | None:
    """Poster frame for the gallery: first frame if we have it, else via ffmpeg."""
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if frames:
            image = _to_pil(frames[0])
            image.thumbnail((640, 640))
            image.save(thumb_path, "JPEG", quality=85)
            return thumb_path
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg and video_path.exists():
            subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", str(video_path),
                 "-frames:v", "1", "-vf", "scale=640:-2", str(thumb_path)],
                check=True, capture_output=True, timeout=120,
            )
            return thumb_path if thumb_path.exists() else None
    except Exception:
        return None
    return None
