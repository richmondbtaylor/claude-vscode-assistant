import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "capture_screenshot.py"


def test_captures_local_page_at_2x(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(
        "<html><body style='margin:0;background:#123456'>"
        "<h1 style='color:white'>Hello</h1></body></html>"
    )
    out = tmp_path / "shot.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), page.resolve().as_uri(), str(out),
         "-", "1200", "700", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.size == (2400, 1400)  # 2x device scale
