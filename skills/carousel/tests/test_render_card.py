import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_card.py"


def test_renders_tilted_card_on_transparency(tmp_path):
    src = tmp_path / "shot.png"
    Image.new("RGB", (800, 600), (30, 60, 200)).save(src)
    out = tmp_path / "card.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.mode == "RGBA"
    assert img.width >= 2000  # 2x render incl. glow padding
    assert img.getpixel((2, 2))[3] == 0  # corners transparent
    cx, cy = img.width // 2, img.height // 2
    assert img.getpixel((cx, cy))[3] == 255  # card center opaque
