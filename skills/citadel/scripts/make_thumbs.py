"""
Manual-paste compositor for thumbnails: subject FULLY inside the frame.

Rich's rule (feedback_thumbnail_subject_never_cut_off): the subject must never
be cut off by the left/right/top frame edges. Only a bottom-edge waist crop is
allowed. composite.py's --side right places the subject with a 12-15% right
bleed, so use THIS script for thumbnails instead.

Usage:
  python make_thumbs.py <background> <grid> <output> --pose N [--scale 0.85] [--right-pad 0.02]
"""

import argparse
from PIL import Image
from composite import crop_pose, detect_grid, remove_bg, defringe, sharpen_rgb


def make_thumb(bg_path, grid_path, output_path, pose_index, scale=0.85,
               right_pad=0.02, bottom_crop=0.03, single=False):
    bg = Image.open(bg_path).convert("RGBA")
    grid = Image.open(grid_path).convert("RGB")
    bg_w, bg_h = bg.size

    if single:
        print("Single-photo mode")
        pose = grid
    else:
        cols, rows = detect_grid(grid)
        print(f"Grid {cols}x{rows}, pose {pose_index}")
        pose = crop_pose(grid, pose_index)
    subject = defringe(remove_bg(pose))

    target_h = int(bg_h * scale)
    target_w = int(target_h * subject.width / subject.height)
    subject = sharpen_rgb(subject.resize((target_w, target_h), Image.LANCZOS))

    # fully inside horizontally; only the bottom edge may crop (waist)
    x = bg_w - target_w - int(bg_w * right_pad)
    y = bg_h - target_h + int(bg_h * bottom_crop)
    assert x >= 0, "subject wider than frame; lower --scale"
    print(f"Pasting {target_w}x{target_h} at ({x}, {y})")
    bg.paste(subject, (x, y), subject)
    bg.convert("RGB").save(output_path, "JPEG", quality=92)
    print(f"Saved: {output_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("background")
    p.add_argument("grid")
    p.add_argument("output")
    p.add_argument("--pose", type=int, default=0)
    p.add_argument("--scale", type=float, default=0.85)
    p.add_argument("--right-pad", type=float, default=0.02)
    p.add_argument("--bottom-crop", type=float, default=0.03)
    p.add_argument("--single", action="store_true", help="Reference is a single photo, not a grid")
    a = p.parse_args()
    make_thumb(a.background, a.grid, a.output, a.pose, a.scale, a.right_pad, a.bottom_crop, a.single)


if __name__ == "__main__":
    main()
