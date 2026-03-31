import asyncio
import io
import os
from playwright.async_api import async_playwright
from PIL import Image

OUTPUT = r"C:\Users\richm\Desktop\claude-code-vscode-carousel.pdf"

SLIDES = [
    {
        "theme": "dark",
        "tip": None,
        "headline": "You're using\nClaude Code wrong.",
        "body": ["Here are 7 tips that", "change everything."],
        "num": "01 / 09",
        "center": True,
    },
    {
        "theme": "light",
        "tip": "TIP 01",
        "headline": "CLAUDE.md loads your\nrules automatically.",
        "body": ["Drop stack, preferences, and rules there.", "Claude reads it on every session."],
        "num": "02 / 09",
        "center": False,
    },
    {
        "theme": "dark",
        "tip": "TIP 02",
        "headline": "@filename pulls code\ninto context directly.",
        "body": ["Stop pasting code into the chat.", "@ does it instantly."],
        "num": "03 / 09",
        "center": False,
    },
    {
        "theme": "light",
        "tip": "TIP 03",
        "headline": "/plan aligns before\nanything gets written.",
        "body": ["Type /plan before big changes.", "Catch mistakes before they cost you."],
        "num": "04 / 09",
        "center": False,
    },
    {
        "theme": "dark",
        "tip": "TIP 04",
        "headline": "Paste screenshots in.\nClaude reads them.",
        "body": ["UI, error messages, diagrams.", "No more describing what you see."],
        "num": "05 / 09",
        "center": False,
    },
    {
        "theme": "light",
        "tip": "TIP 05",
        "headline": "/clear resets context\nbetween tasks.",
        "body": ["Stale context = worse output.", "Fresh context = sharper code."],
        "num": "06 / 09",
        "center": False,
    },
    {
        "theme": "dark",
        "tip": "TIP 06",
        "headline": "Hooks run scripts\non every file save.",
        "body": ["Linters, tests, formatters.", "Set once in settings.json. Done."],
        "num": "07 / 09",
        "center": False,
    },
    {
        "theme": "light",
        "tip": "TIP 07",
        "headline": "Claude reads your\ngit history too.",
        "body": ["Ask what changed recently.", "It understands full context."],
        "num": "08 / 09",
        "center": False,
    },
    {
        "theme": "dark",
        "tip": None,
        "headline": "Save this.\nOpen VS Code.\nTry one tip today.",
        "body": ["Which tip did you not know?", "Drop it in the comments."],
        "num": "09 / 09",
        "center": True,
    },
]


def build_html(slide):
    dark = slide["theme"] == "dark"
    bg          = "#0D0D0D" if dark else "#F5F5F5"
    fg          = "#FFFFFF" if dark else "#0D0D0D"
    sub         = "#666666" if dark else "#888888"
    chip_bg     = "#FFFFFF" if dark else "#0D0D0D"
    chip_fg     = "#0D0D0D" if dark else "#FFFFFF"
    muted       = "#2A2A2A" if dark else "#DDDDDD"
    brand_col   = "#444444" if dark else "#BBBBBB"

    chip_html = ""
    if slide["tip"]:
        chip_html = f"""
        <div style="
            display:inline-flex; align-items:center;
            background:{chip_bg}; color:{chip_fg};
            font-size:13px; font-weight:700;
            letter-spacing:0.12em; text-transform:uppercase;
            padding:10px 20px; border-radius:100px;
            margin-bottom:52px;
        ">{slide["tip"]}</div>
        """

    headline_html = slide["headline"].replace("\n", "<br>")
    body_html = "".join(
        f'<div style="font-size:28px; font-weight:400; color:{sub}; line-height:1.6; margin-bottom:4px;">{line}</div>'
        for line in slide["body"]
    )

    align = "center" if slide["center"] else "flex-start"
    text_align = "center" if slide["center"] else "left"
    justify = "center" if slide["center"] else "flex-start"

    # Tip number watermark
    tip_num_watermark = ""
    if slide["tip"]:
        num_only = slide["tip"].split(" ")[-1]
        watermark_color = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.04)"
        tip_num_watermark = f"""
        <div style="
            position:absolute; right:60px; bottom:100px;
            font-size:220px; font-weight:900;
            color:{watermark_color}; line-height:1;
            font-family:'Inter', sans-serif;
            user-select:none; pointer-events:none;
        ">{num_only}</div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    width:1080px; height:1080px;
    background:{bg};
    font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
    overflow:hidden;
}}
</style>
</head>
<body>
<div style="
    width:1080px; height:1080px;
    padding:96px 100px;
    display:flex; flex-direction:column;
    justify-content:{justify};
    align-items:{align};
    position:relative;
">
    {tip_num_watermark}
    {chip_html}
    <div style="
        font-size:66px; font-weight:900;
        color:{fg}; line-height:1.08;
        letter-spacing:-0.025em;
        margin-bottom:36px;
        text-align:{text_align};
        position:relative; z-index:1;
    ">{headline_html}</div>
    <div style="text-align:{text_align}; position:relative; z-index:1;">
        {body_html}
    </div>
    <div style="
        position:absolute; bottom:56px; left:100px;
        font-size:13px; font-weight:600;
        color:{brand_col}; letter-spacing:0.06em;
        text-transform:uppercase;
    ">Claude Code x VS Code</div>
    <div style="
        position:absolute; bottom:56px; right:100px;
        font-size:13px; font-weight:500;
        color:{muted}; letter-spacing:0.08em;
    ">{slide["num"]}</div>
    <div style="
        position:absolute; top:96px; left:100px;
        width:40px; height:4px;
        background:{fg}; opacity:0.15;
        border-radius:2px;
    "></div>
</div>
</body>
</html>"""


async def main():
    images = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})

        for i, slide in enumerate(SLIDES):
            html = build_html(slide)
            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(1500)
            shot = await page.screenshot(type="png")
            img = Image.open(io.BytesIO(shot)).convert("RGB")
            images.append(img)
            print(f"  Slide {i+1}/9 rendered")

        await browser.close()

    images[0].save(OUTPUT, save_all=True, append_images=images[1:], resolution=96)
    print(f"\nPDF saved -> {OUTPUT}")


asyncio.run(main())
