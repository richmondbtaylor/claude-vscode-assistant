"""Slice a wide panorama image into N equal carousel panels.

Usage:
    python slice_panorama.py <panorama_path> <num_panels> <output_dir> [start_slide_num] [panel_ratio]

    panorama_path    Path to the generated panorama image
    num_panels       Number of slides to slice it into (2 or 3 typical)
    output_dir       Directory for slide-XX.jpg outputs (created if missing)
    start_slide_num  Slide number of the first panel (default 1) so numbering
                     continues across multiple panorama groups
    panel_ratio      W:H of each panel, default 4:5

Center-crops the panorama to exactly num_panels * panel_ratio, then slices
into equal panels. Adjacent panels share the exact boundary pixels, so the
carousel bleeds seamlessly from slide to slide.
"""
import os
import sys

from PIL import Image


def run():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    pano_path = sys.argv[1]
    num_panels = int(sys.argv[2])
    out_dir = sys.argv[3]
    start_num = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    ratio_str = sys.argv[5] if len(sys.argv) > 5 else "4:5"

    rw, rh = (int(x) for x in ratio_str.split(":"))
    panel_ratio = rw / rh
    target_ratio = num_panels * panel_ratio

    img = Image.open(pano_path)
    w, h = img.size
    actual_ratio = w / h

    if actual_ratio > target_ratio:
        # Too wide: center-crop width
        new_w = int(round(h * target_ratio))
        x0 = (w - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, h))
    elif actual_ratio < target_ratio:
        # Too tall: center-crop height
        new_h = int(round(w / target_ratio))
        y0 = (h - new_h) // 2
        img = img.crop((0, y0, w, y0 + new_h))

    w, h = img.size
    os.makedirs(out_dir, exist_ok=True)

    panel_w = w / num_panels
    for i in range(num_panels):
        x0 = int(round(i * panel_w))
        x1 = int(round((i + 1) * panel_w))
        panel = img.crop((x0, 0, x1, h))
        out_path = os.path.join(out_dir, f"slide-{start_num + i:02d}.jpg")
        panel.convert("RGB").save(out_path, quality=95)
        print(f"Saved {out_path} ({panel.size[0]}x{panel.size[1]})")

    print(f"Done: {num_panels} panels from {pano_path} (cropped to {w}x{h})")


if __name__ == "__main__":
    run()
