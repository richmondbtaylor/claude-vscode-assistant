import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "composite_card.py"


def _make_inputs(tmp_path):
    base = tmp_path / "base.jpg"
    Image.new("RGB", (3000, 1250), (8, 11, 20)).save(base)
    card = tmp_path / "card.png"
    c = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
    for x in range(100, 300):
        for y in range(75, 225):
            c.putpixel((x, y), (255, 255, 255, 255))
    c.save(card)
    return base, card


def test_composites_card_at_center(tmp_path):
    base, card = _make_inputs(tmp_path)
    out = tmp_path / "out.jpg"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(base), str(card),
         "1500", "625", "800", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    img = Image.open(out)
    assert img.size == (3000, 1250)
    assert img.getpixel((1500, 625))[0] > 200  # white card visible at center
    assert img.getpixel((100, 100))[0] < 30    # background untouched
    assert "WARNING" not in result.stdout


def test_warns_when_card_enters_outer_margin(tmp_path):
    base, card = _make_inputs(tmp_path)
    out = tmp_path / "out.jpg"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(base), str(card),
         "200", "625", "800", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stdout
