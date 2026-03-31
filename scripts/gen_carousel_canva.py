"""
promptAnything.io — Claude Code x VS Code Carousel
Brand: Black/Light alternating, Gold accent, Poppins + Open Sans
Output: 9 x 1080x1080 PNGs for Canva
"""
import asyncio
import os
from playwright.async_api import async_playwright

OUTPUT_DIR = r"C:\Users\richm\Desktop\claude-vscode-carousel-canva"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Brand tokens ──────────────────────────────────────────────────────────────
DARK  = "#0D0D0D"
LIGHT = "#F5F5F5"
GOLD  = "#E0B848"
BLUE  = "#1894C9"

SLIDES = [
    {
        "bg": DARK, "accent": GOLD,
        "tip": None,
        "headline": 'You\'re using\nClaude Code <span style="color:#E0B848">wrong.</span>',
        "body": ["Here are 7 tips that", "change everything."],
        "num": "01 / 09", "center": True, "type": "hook",
    },
    {
        "bg": LIGHT, "accent": GOLD,
        "tip": "TIP 01",
        "headline": "CLAUDE.md loads your\nrules automatically.",
        "body": ["Drop stack, preferences, and rules there.", "Claude reads it on every session."],
        "num": "02 / 09", "center": False, "type": "tip",
    },
    {
        "bg": DARK, "accent": GOLD,
        "tip": "TIP 02",
        "headline": "@filename pulls code\ninto context directly.",
        "body": ["Stop pasting code into the chat.", "@ does it instantly."],
        "num": "03 / 09", "center": False, "type": "tip",
    },
    {
        "bg": LIGHT, "accent": GOLD,
        "tip": "TIP 03",
        "headline": "/plan aligns before\nanything gets written.",
        "body": ["Type /plan before big changes.", "Catch mistakes before they cost you."],
        "num": "04 / 09", "center": False, "type": "tip",
    },
    {
        "bg": DARK, "accent": GOLD,
        "tip": "TIP 04",
        "headline": "Paste screenshots in.\nClaude reads them.",
        "body": ["UI, error messages, diagrams.", "No more describing what you see."],
        "num": "05 / 09", "center": False, "type": "tip",
    },
    {
        "bg": LIGHT, "accent": GOLD,
        "tip": "TIP 05",
        "headline": "/clear resets context\nbetween tasks.",
        "body": ["Stale context = worse output.", "Fresh context = sharper code."],
        "num": "06 / 09", "center": False, "type": "tip",
    },
    {
        "bg": DARK, "accent": GOLD,
        "tip": "TIP 06",
        "headline": "Hooks run scripts\non every file save.",
        "body": ["Linters, tests, formatters.", "Set once in settings.json. Done."],
        "num": "07 / 09", "center": False, "type": "tip",
    },
    {
        "bg": LIGHT, "accent": GOLD,
        "tip": "TIP 07",
        "headline": "Claude reads your\ngit history too.",
        "body": ["Ask what changed recently.", "It understands full context."],
        "num": "08 / 09", "center": False, "type": "tip",
    },
    {
        "bg": DARK, "accent": GOLD,
        "tip": None,
        "headline": '<span style="color:#E0B848">Save this.</span>\nOpen VS Code.\nTry one tip today.',
        "body": ["Which tip did you not know?", "Drop it in the comments."],
        "num": "09 / 09", "center": True, "type": "cta",
    },
]


def hex_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def dot_grid_svg(x, y, cols, rows, gap, r, color):
    dots = []
    for row in range(rows):
        for col in range(cols):
            cx = x + col * gap
            cy = y + row * gap
            dots.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
    return "\n".join(dots)


def build_svg_layer(slide):
    acc = slide["accent"]
    stype = slide["type"]
    a_ring  = hex_rgba(acc, 0.15)
    a_ring2 = hex_rgba(acc, 0.08)
    a_fill  = hex_rgba(acc, 0.06)
    a_dot   = hex_rgba(acc, 0.35)
    a_line  = hex_rgba(acc, 0.30)

    if stype in ("hook", "cta"):
        # Large concentric rings, centered + bold corner dots + radial fill
        return f"""
        <svg style="position:absolute;top:0;left:0;width:1080px;height:1080px;overflow:hidden;pointer-events:none;">
          <!-- radial glow fill -->
          <circle cx="540" cy="500" r="460" fill="{a_fill}"/>
          <!-- rings -->
          <circle cx="540" cy="500" r="450" fill="none" stroke="{a_ring}" stroke-width="1.5"/>
          <circle cx="540" cy="500" r="340" fill="none" stroke="{a_ring}" stroke-width="1"/>
          <circle cx="540" cy="500" r="230" fill="none" stroke="{a_ring2}" stroke-width="1"/>
          <circle cx="540" cy="500" r="120" fill="none" stroke="{a_ring2}" stroke-width="0.8"/>
          <!-- dot grids corners -->
          {dot_grid_svg(80, 80, 5, 5, 26, 3, a_dot)}
          {dot_grid_svg(878, 878, 5, 5, 26, 3, a_dot)}
          <!-- cross marks -->
          <line x1="80" y1="950" x2="100" y2="950" stroke="{a_line}" stroke-width="1.5"/>
          <line x1="90" y1="940" x2="90" y2="960" stroke="{a_line}" stroke-width="1.5"/>
          <line x1="980" y1="115" x2="1000" y2="115" stroke="{a_line}" stroke-width="1.5"/>
          <line x1="990" y1="105" x2="990" y2="125" stroke="{a_line}" stroke-width="1.5"/>
          <!-- bold accent bar top-left -->
          <rect x="100" y="90" width="60" height="4" rx="2" fill="{acc}" opacity="0.7"/>
        </svg>"""

    else:
        # Tip slides: large filled arc corner + bold dot grid + accent lines
        return f"""
        <svg style="position:absolute;top:0;left:0;width:1080px;height:1080px;overflow:hidden;pointer-events:none;">
          <!-- large filled arc bottom-right -->
          <circle cx="1100" cy="1100" r="620" fill="{a_fill}"/>
          <circle cx="1100" cy="1100" r="620" fill="none" stroke="{a_ring}" stroke-width="1.5"/>
          <circle cx="1100" cy="1100" r="480" fill="none" stroke="{a_ring2}" stroke-width="1"/>
          <circle cx="1100" cy="1100" r="340" fill="none" stroke="{a_ring2}" stroke-width="0.8"/>
          <!-- small arc top-left -->
          <circle cx="-20" cy="-20" r="280" fill="none" stroke="{a_ring2}" stroke-width="1"/>
          <!-- dot grid top-right -->
          {dot_grid_svg(855, 80, 6, 5, 26, 3, a_dot)}
          <!-- cross mark bottom-left -->
          <line x1="100" y1="952" x2="122" y2="952" stroke="{a_line}" stroke-width="1.5"/>
          <line x1="111" y1="941" x2="111" y2="963" stroke="{a_line}" stroke-width="1.5"/>
          <!-- bold diagonal accent lines top-right -->
          <line x1="970" y1="90" x2="1010" y2="90" stroke="{acc}" stroke-width="2.5" opacity="0.5"/>
          <line x1="985" y1="104" x2="1010" y2="104" stroke="{acc}" stroke-width="1.5" opacity="0.3"/>
        </svg>"""


def build_html(slide):
    bg    = slide["bg"]
    acc   = slide["accent"]
    stype = slide["type"]

    svg_layer = build_svg_layer(slide)

    # Ghost tip number
    tip_watermark = ""
    if slide["tip"]:
        num_only = slide["tip"].split(" ")[-1]
        wm_color = hex_rgba(GOLD, 0.10) if bg == DARK else hex_rgba("#0D0D0D", 0.50)
        tip_watermark = f"""
        <div style="
            position:absolute; right:50px; bottom:80px;
            font-size:280px; font-weight:900;
            color:{wm_color}; line-height:1;
            font-family:'Poppins', sans-serif;
            user-select:none; z-index:0;
        ">{num_only}</div>"""

    # Derive text colors from bg
    is_dark    = bg == DARK
    fg         = "#FAFBFA" if is_dark else "#0D0D0D"
    body_color = "#888888" if is_dark else "#3A3A3A"
    num_color  = hex_rgba("#FFFFFF", 0.22) if is_dark else hex_rgba("#000000", 0.22)

    # Chip
    chip_html = ""
    if slide["tip"]:
        chip_html = f"""
        <div style="
            display:inline-flex; align-items:center;
            background:{GOLD}; color:{DARK};
            font-size:12px; font-weight:700;
            font-family:'Poppins', sans-serif;
            letter-spacing:0.16em; text-transform:uppercase;
            padding:9px 22px; border-radius:100px;
            margin-bottom:32px;
        ">{slide["tip"]}</div>"""

    # Gold accent bar + separator below chip
    bar_html = ""
    if stype == "tip":
        bar_html = f"""
        <div style="width:56px; height:3px; background:{GOLD}; border-radius:2px; margin-bottom:28px;"></div>"""

    # Headline
    raw_hl = slide["headline"].replace("\n", "<br>")
    align      = "center" if slide["center"] else "flex-start"
    text_align = "center" if slide["center"] else "left"
    justify    = "center" if slide["center"] else "flex-start"

    # Body
    body_html = "".join(
        f'<div style="font-size:27px; font-weight:400; font-family:\'Open Sans\',sans-serif; color:{body_color}; line-height:1.7; margin-bottom:2px;">{ln}</div>'
        for ln in slide["body"]
    )

    # Gold bottom accent bar (full width)
    bottom_bar = f'<div style="position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{GOLD},{hex_rgba(GOLD,0)});"></div>'

    # promptAnything.io wordmark bottom-left
    brand_html = f"""
    <div style="
        position:absolute; bottom:48px; left:104px;
        font-size:12px; font-weight:600;
        font-family:'Poppins', sans-serif;
        color:{GOLD}; letter-spacing:0.06em;
        text-transform:uppercase; opacity:0.75;
    ">promptAnything.io</div>"""

    slide_num_html = f"""
    <div style="
        position:absolute; bottom:48px; right:104px;
        font-size:12px; font-weight:500;
        font-family:'Poppins', sans-serif;
        color:{num_color}; letter-spacing:0.10em;
    ">{slide["num"]}</div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    width:1080px; height:1080px;
    background:{bg};
    overflow:hidden;
}}
</style>
</head>
<body>
<div style="
    width:1080px; height:1080px;
    padding:96px 104px;
    display:flex; flex-direction:column;
    justify-content:{justify};
    align-items:{align};
    position:relative;
">
    {svg_layer}
    {tip_watermark}

    <div style="position:relative; z-index:1; display:flex; flex-direction:column; align-items:{align}; width:100%;">
        {chip_html}
        {bar_html}
        <div style="
            font-size:62px; font-weight:900;
            font-family:'Poppins', sans-serif;
            color:{fg}; line-height:1.08;
            letter-spacing:-0.02em;
            margin-bottom:32px;
            text-align:{text_align};
        ">{raw_hl}</div>
        <div style="text-align:{text_align};">
            {body_html}
        </div>
    </div>

    {bottom_bar}
    {brand_html}
    {slide_num_html}
</div>
</body>
</html>"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})

        for i, slide in enumerate(SLIDES):
            html = build_html(slide)
            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(1800)
            shot = await page.screenshot(type="png")

            fname = os.path.join(OUTPUT_DIR, f"slide-{i+1:02d}.png")
            with open(fname, "wb") as f:
                f.write(shot)
            print(f"  slide-{i+1:02d}.png")

        await browser.close()

    print(f"\nDone -> {OUTPUT_DIR}")


asyncio.run(main())
