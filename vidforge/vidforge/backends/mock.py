"""Deterministic backend that needs no GPU and no weights.

It exists so the queue, the UI, the batch runner and the tests are all
exercisable on any machine - and so a new install shows a working end-to-end
render before multi-gigabyte checkpoints are downloaded.
"""

from __future__ import annotations

import colorsys
import hashlib
import threading
import time

from ..media import encode_video, write_thumbnail
from .base import Backend, GenRequest, GenResult, ProgressFn


class MockBackend(Backend):
    name = "mock"

    def generate(
        self, req: GenRequest, on_progress: ProgressFn, cancel: threading.Event
    ) -> GenResult:
        from PIL import Image, ImageDraw

        width = int(req.get("width", 512))
        height = int(req.get("height", 288))
        frames_n = int(req.get("num_frames", 24))
        fps = int(req.get("fps", 12))
        # Seed and prompt drive the colour ramp, so identical inputs look identical.
        digest = hashlib.sha256(f"{req.prompt}|{req.seed}".encode()).digest()
        hue0 = digest[0] / 255

        frames = []
        for i in range(frames_n):
            self.check_cancelled(cancel)
            hue = (hue0 + i / max(1, frames_n)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.55, 0.85)
            image = Image.new("RGB", (width, height), (int(r * 255), int(g * 255), int(b * 255)))
            draw = ImageDraw.Draw(image)
            draw.text((12, 12), f"mock {i + 1}/{frames_n}", fill=(20, 20, 20))
            draw.text((12, 28), f"seed {req.seed}", fill=(20, 20, 20))
            draw.text((12, 44), req.prompt[:60], fill=(20, 20, 20))
            frames.append(image)
            on_progress((i + 1) / frames_n)
            time.sleep(0.01)  # keep cancellation observable

        video = encode_video(frames, req.out_path, fps=fps)
        thumb = write_thumbnail(frames, video, req.out_path.with_suffix(".jpg"))
        return GenResult(video_path=video, thumb_path=thumb)
