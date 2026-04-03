"""
Image Generator -- Creates carousel slide images via KIE AI pipeline.

Takes carousel content JSON and generates one image per slide,
then uploads all images to Google Drive.
"""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from config import ASPECT_RATIO, HANDLE, IMAGES_DIR, KIE_SCRIPT, PROMPTS_DIR, RESOLUTION, STYLE_PRESETS, GDRIVE_SCRIPT


def _build_slide_prompt(slide: dict, style_preset: str, total_slides: int) -> str:
    """Build a dense KIE AI prompt for a single slide."""
    style = STYLE_PRESETS.get(style_preset, STYLE_PRESETS["clean_editorial"])
    bg = style["background"]
    text_color = style["text_color"]
    accent = style["accent"]
    slide_num = slide["number"]
    headline = slide.get("headline", "")
    subtext = slide.get("subtext", "")
    slide_type = slide.get("type", "value")
    visual_notes = slide.get("visual_notes", "")

    # Base prompt
    prompt = (
        f"Social media carousel slide, {ASPECT_RATIO} aspect ratio. "
        f"Clean {style_preset.replace('_', ' ')} design. "
        f"Background: solid {bg}. "
        f"In the top-right corner, small text reading '{slide_num}/{total_slides}' in muted gray. "
    )

    # Slide-type-specific formatting
    if slide_type == "hook":
        prompt += (
            f"Centered layout with generous whitespace. "
            f"Large ultra-bold sans-serif headline text reading '{headline}' at 64pt size, centered. "
        )
        if subtext:
            prompt += f"Below it, medium-weight text reading '{subtext}' at 32pt. "
        # Highlight key words with accent
        words = headline.split()
        if len(words) > 3:
            highlight_words = " ".join(words[2:4])
            prompt += f"The words '{highlight_words}' have a soft {accent} brush-stroke highlight behind them. "

    elif slide_type == "cta":
        prompt += (
            f"Centered layout with generous whitespace. "
            f"Large ultra-bold sans-serif text reading '{headline}' at 56pt, centered. "
        )
        if subtext:
            prompt += f"Below a thin divider line, medium text reading '{subtext}' at 28pt centered. "
        prompt += f"Key action words highlighted in {accent} color for emphasis. "

    else:  # value slides
        if slide_num <= 9:  # Numbered tip slides
            tip_number = slide_num - 1  # Slide 2 = tip 1, etc.
            prompt += (
                f"Top section has a large coral-red circled number '{tip_number}' as a decorative element. "
                f"Below it, bold sans-serif headline reading '{headline}' at 56pt, centered. "
            )
            # Highlight key phrase
            words = headline.split()
            if len(words) > 2:
                highlight_words = " ".join(words[-2:])
                prompt += f"The words '{highlight_words}' have a soft {accent} brush-stroke highlight behind them. "
        else:
            prompt += f"Bold sans-serif headline reading '{headline}' at 56pt, centered. "

        if subtext:
            prompt += f"Below, medium-weight text reading '{subtext}' at 24pt. "

    # Visual notes from content generator
    if visual_notes:
        prompt += f"{visual_notes} "

    # Branding
    prompt += f"Small text '{HANDLE}' in muted gray at the bottom center. "

    # Quality directives
    prompt += (
        "Ultra-clean, minimal, maximum whitespace. "
        "Pixel-perfect text rendering, ultra-sharp, perfectly legible at phone screen size. "
        "Negative: blurry text, garbled typography, illegible fonts, busy layouts, "
        "stock photos, photorealistic faces, lens flare, bokeh, gradients, drop shadows, "
        "decorative clutter, multiple fonts, colorful backgrounds."
    )

    return prompt


def _generate_single_slide(prompt_path: str, output_path: str) -> dict:
    """Run generate_kie.py for a single slide. Returns result dict."""
    try:
        result = subprocess.run(
            [sys.executable, KIE_SCRIPT, prompt_path, output_path, ASPECT_RATIO],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max per slide
        )
        if result.returncode == 0:
            return {"success": True, "path": output_path}
        else:
            return {"success": False, "path": output_path, "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "path": output_path, "error": "Timeout (5 min)"}
    except Exception as e:
        return {"success": False, "path": output_path, "error": str(e)}


def _upload_to_gdrive(image_path: str) -> str:
    """Upload a single image to Google Drive. Returns the drive link or empty string."""
    try:
        result = subprocess.run(
            [sys.executable, GDRIVE_SCRIPT, image_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            # Try to extract drive link from output
            for line in result.stdout.split("\n"):
                if "drive.google.com" in line or "docs.google.com" in line:
                    return line.strip()
            return "uploaded (link not parsed)"
        return ""
    except Exception as e:
        print(f"[image] Drive upload failed for {image_path}: {e}")
        return ""


def generate_images(carousel: dict) -> tuple[list[str], list[str]]:
    """
    Generate KIE AI images for all slides in the carousel.

    Returns:
        (image_paths, drive_links) -- lists of local paths and Drive URLs
    """
    slides = carousel.get("slides", [])
    style_preset = carousel.get("style_preset", "clean_editorial")
    total_slides = len(slides)

    # Create date-based directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    topic_slug = carousel.get("chosen_topic", {}).get("angle", "carousel")
    topic_slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in topic_slug)
    topic_slug = topic_slug.replace(" ", "-").lower()[:40]
    folder_name = f"{date_str}_{topic_slug}"

    prompt_dir = os.path.join(PROMPTS_DIR, folder_name)
    image_dir = os.path.join(IMAGES_DIR, folder_name)
    os.makedirs(prompt_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Create JSON prompt files for each slide
    prompt_paths = []
    output_paths = []
    for slide in slides:
        slide_num = slide["number"]
        prompt_text = _build_slide_prompt(slide, style_preset, total_slides)

        prompt_data = {
            "task": "carousel_slide_generation",
            "schema_version": "prism-2.0",
            "model_target": "nano-banana-2",
            "prompt": prompt_text,
            "api_parameters": {
                "aspect_ratio": ASPECT_RATIO,
                "resolution": RESOLUTION,
                "output_format": "jpg",
            },
        }

        prompt_path = os.path.join(prompt_dir, f"slide-{slide_num:02d}.json")
        output_path = os.path.join(image_dir, f"slide-{slide_num:02d}.jpg")

        with open(prompt_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2)

        prompt_paths.append(prompt_path)
        output_paths.append(output_path)

    print(f"[image] Generating {len(slides)} slides via KIE AI (parallel, 4 at a time)...")

    # Generate images in parallel (4 at a time)
    image_paths = []
    failed = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_generate_single_slide, pp, op): (pp, op)
            for pp, op in zip(prompt_paths, output_paths)
        }
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                print(f"[image] Done: {os.path.basename(result['path'])}")
                image_paths.append(result["path"])
            else:
                print(f"[image] FAILED: {os.path.basename(result['path'])} -- {result['error'][:100]}")
                failed.append(result)

    image_paths.sort()  # Ensure slide order
    print(f"[image] Generated {len(image_paths)}/{len(slides)} slides")

    if failed:
        print(f"[image] {len(failed)} slides failed. Check logs.")

    # Upload to Google Drive
    print("[image] Uploading to Google Drive...")
    drive_links = []
    for img_path in image_paths:
        link = _upload_to_gdrive(img_path)
        drive_links.append(link)

    return image_paths, drive_links


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with a simple 3-slide carousel
    test_carousel = {
        "style_preset": "clean_editorial",
        "chosen_topic": {"angle": "test carousel"},
        "slides": [
            {"number": 1, "type": "hook", "headline": "3 AI Tips You Need", "subtext": "That Actually Work", "visual_notes": ""},
            {"number": 2, "type": "value", "headline": "Start With Screenshots", "subtext": "Drag images into Claude Code", "visual_notes": ""},
            {"number": 3, "type": "cta", "headline": "Follow for more AI tips", "subtext": "@bishop_ai_", "visual_notes": ""},
        ],
    }
    paths, links = generate_images(test_carousel)
    print(f"\nPaths: {paths}")
    print(f"Links: {links}")
