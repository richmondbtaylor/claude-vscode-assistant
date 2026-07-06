"""Composite a rendered screenshot card onto a panorama or standalone slide.

Usage:
    python composite_card.py <base_image> <card_png> <center_x> <center_y> <target_width> <output_path>

    base_image    Panorama (pano-XX.jpg) or standalone slide image
    card_png      RGBA card from render_card.py (glow included)
    center_x/y    Pixel position in the base image where the card CENTER
                  lands. In seamless mode put center_x on a zone boundary
                  so the card straddles two slides.
    target_width  Final width in base-image pixels for the whole card PNG
                  (glow padding included)
    output_path   Composited image output (jpg)

Run BEFORE slice_panorama.py so boundary-straddling bleed survives slicing.
Warns if the card enters the outer 12% of the base width -- that area must
stay plain background so seams between panorama groups stay invisible.
"""
import os
import sys

from PIL import Image


def run():
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)

    base_path = sys.argv[1]
    card_path = sys.argv[2]
    cx = int(sys.argv[3])
    cy = int(sys.argv[4])
    target_w = int(sys.argv[5])
    out_path = sys.argv[6]

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)

    base = Image.open(base_path).convert("RGB")
    card = Image.open(card_path).convert("RGBA")
    target_h = int(round(card.height * target_w / card.width))
    card = card.resize((target_w, target_h), Image.LANCZOS)

    x0 = cx - target_w // 2
    y0 = cy - target_h // 2

    margin = int(base.width * 0.12)
    if x0 < margin or x0 + target_w > base.width - margin:
        print(
            f"WARNING: card spans x {x0}..{x0 + target_w} inside outer 12% "
            f"margin ({margin}px) -- may break invisible seams between groups"
        )

    base.paste(card, (x0, y0), card)
    base.save(out_path, quality=95)
    print(
        f"Saved {out_path} ({base.width}x{base.height}), "
        f"card at ({x0},{y0}) size {target_w}x{target_h}"
    )


if __name__ == "__main__":
    run()
