import asyncio
from playwright.async_api import async_playwright
from pypdf import PdfWriter, PdfReader
import os

OUTPUT_DIR = r"c:\Users\richm\.claude\temp"
FINAL_PDF = os.path.join(OUTPUT_DIR, "FROM_SAAS_TO_AGENTS_Keynote.pdf")

# Brand colors
DEEP_NAVY = "#000813"
DARK_NAVY = "#1D2333"
WHITE_BG = "#FAFBFA"
OFF_WHITE = "#E6E2DE"
GOLD = "#E0B848"
BLUE = "#1894C9"
RED_CORAL = "#E05252"

SLIDE_W = 1920
SLIDE_H = 1080

# --- SVG icon library ---
ICON_BRIEFCASE = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><rect x="8" y="22" width="48" height="34" rx="4" stroke="{GOLD}" stroke-width="3" fill="none"/><path d="M24 22V16a4 4 0 014-4h8a4 4 0 014 4v6" stroke="{GOLD}" stroke-width="3" fill="none"/><line x1="8" y1="36" x2="56" y2="36" stroke="{GOLD}" stroke-width="2" opacity="0.4"/></svg>'''
ICON_LIGHTNING = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><polygon points="36,4 16,36 30,36 28,60 48,28 34,28" fill="{GOLD}" opacity="0.9"/></svg>'''
ICON_CHART_DOWN = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><polyline points="8,16 24,28 38,20 56,48" stroke="{RED_CORAL}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polygon points="48,48 56,48 56,40" fill="{RED_CORAL}" opacity="0.7"/><line x1="8" y1="56" x2="56" y2="56" stroke="{DARK_NAVY}" stroke-width="2" opacity="0.2"/></svg>'''
ICON_ROCKET = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><path d="M32 8c0 0-16 12-16 32l8 8 8-4 8 4 8-8c0-20-16-32-16-32z" stroke="{GOLD}" stroke-width="3" fill="none"/><circle cx="32" cy="28" r="5" stroke="{GOLD}" stroke-width="2" fill="none"/><path d="M24 48l-6 8M40 48l6 8" stroke="{GOLD}" stroke-width="2" stroke-linecap="round"/></svg>'''
ICON_DOLLAR = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><circle cx="32" cy="32" r="26" stroke="{GOLD}" stroke-width="3" fill="none"/><path d="M32 14v36M24 22c0 0 0-4 8-4s8 4 8 4-1 6-8 8-8 8-8 8 0 4 8 4 8-4 8-4" stroke="{GOLD}" stroke-width="2.5" fill="none" stroke-linecap="round"/></svg>'''
ICON_TARGET = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><circle cx="32" cy="32" r="26" stroke="{GOLD}" stroke-width="2.5" fill="none"/><circle cx="32" cy="32" r="16" stroke="{GOLD}" stroke-width="2" fill="none" opacity="0.6"/><circle cx="32" cy="32" r="6" fill="{GOLD}"/></svg>'''
ICON_PEOPLE = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><circle cx="22" cy="20" r="8" stroke="{RED_CORAL}" stroke-width="2.5" fill="none"/><path d="M6 52c0-10 7-18 16-18s16 8 16 18" stroke="{RED_CORAL}" stroke-width="2.5" fill="none"/><circle cx="44" cy="20" r="8" stroke="{RED_CORAL}" stroke-width="2.5" fill="none" opacity="0.5"/><path d="M34 52c0-10 4-18 10-18s10 8 10 18" stroke="{RED_CORAL}" stroke-width="2.5" fill="none" opacity="0.5"/></svg>'''
ICON_WARNING = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><path d="M32 8L4 56h56L32 8z" stroke="{RED_CORAL}" stroke-width="3" fill="none"/><line x1="32" y1="24" x2="32" y2="40" stroke="{RED_CORAL}" stroke-width="3" stroke-linecap="round"/><circle cx="32" cy="48" r="2.5" fill="{RED_CORAL}"/></svg>'''
ICON_BRIDGE = f'''<svg width="80" height="64" viewBox="0 0 80 64" fill="none"><path d="M4 48 Q20 12 40 12 Q60 12 76 48" stroke="{GOLD}" stroke-width="3" fill="none"/><line x1="4" y1="48" x2="76" y2="48" stroke="{GOLD}" stroke-width="2"/><line x1="20" y1="48" x2="20" y2="26" stroke="{GOLD}" stroke-width="2" opacity="0.5"/><line x1="40" y1="48" x2="40" y2="12" stroke="{GOLD}" stroke-width="2" opacity="0.5"/><line x1="60" y1="48" x2="60" y2="26" stroke="{GOLD}" stroke-width="2" opacity="0.5"/></svg>'''
ICON_CUBE = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><path d="M32 4L4 20v24l28 16 28-16V20L32 4z" stroke="{GOLD}" stroke-width="2.5" fill="none"/><path d="M32 4v40M4 20l28 24M60 20L32 44" stroke="{GOLD}" stroke-width="1.5" opacity="0.4"/></svg>'''
ICON_GLOBE = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><circle cx="32" cy="32" r="26" stroke="{BLUE}" stroke-width="2.5" fill="none"/><ellipse cx="32" cy="32" rx="12" ry="26" stroke="{BLUE}" stroke-width="2" fill="none"/><line x1="6" y1="32" x2="58" y2="32" stroke="{BLUE}" stroke-width="1.5"/><path d="M10 18h44M10 46h44" stroke="{BLUE}" stroke-width="1.5" opacity="0.4"/></svg>'''
ICON_CHIP = f'''<svg width="64" height="64" viewBox="0 0 64 64" fill="none"><rect x="16" y="16" width="32" height="32" rx="4" stroke="{BLUE}" stroke-width="2.5" fill="none"/><circle cx="32" cy="32" r="8" stroke="{BLUE}" stroke-width="2" fill="none"/><line x1="16" y1="24" x2="6" y2="24" stroke="{BLUE}" stroke-width="2"/><line x1="16" y1="32" x2="6" y2="32" stroke="{BLUE}" stroke-width="2"/><line x1="16" y1="40" x2="6" y2="40" stroke="{BLUE}" stroke-width="2"/><line x1="48" y1="24" x2="58" y2="24" stroke="{BLUE}" stroke-width="2"/><line x1="48" y1="32" x2="58" y2="32" stroke="{BLUE}" stroke-width="2"/><line x1="48" y1="40" x2="58" y2="40" stroke="{BLUE}" stroke-width="2"/><line x1="24" y1="16" x2="24" y2="6" stroke="{BLUE}" stroke-width="2"/><line x1="32" y1="16" x2="32" y2="6" stroke="{BLUE}" stroke-width="2"/><line x1="40" y1="16" x2="40" y2="6" stroke="{BLUE}" stroke-width="2"/><line x1="24" y1="48" x2="24" y2="58" stroke="{BLUE}" stroke-width="2"/><line x1="32" y1="48" x2="32" y2="58" stroke="{BLUE}" stroke-width="2"/><line x1="40" y1="48" x2="40" y2="58" stroke="{BLUE}" stroke-width="2"/></svg>'''
ICON_ARROW_SHIFT = f'''<svg width="80" height="64" viewBox="0 0 80 64" fill="none"><path d="M10 44H50" stroke="{DARK_NAVY}" stroke-width="3" stroke-linecap="round" opacity="0.3" stroke-dasharray="6 4"/><path d="M10 20H60L72 32L60 44" stroke="{GOLD}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polygon points="72,32 62,26 62,38" fill="{GOLD}"/></svg>'''

# Scaled icon helpers
def scale_icon(svg, size):
    return svg.replace('width="64"', f'width="{size}"').replace('height="64"', f'height="{size}"').replace('width="80"', f'width="{size}"')

FOOTER = f'<div style="position:absolute; bottom:50px; right:80px; font-family:\'Montserrat\',sans-serif; font-weight:700; font-size:18px; color:{GOLD}; letter-spacing:2px;">BISHOP AI</div>'


def build_slide_html(slide_content):
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&family=Montserrat:wght@400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{SLIDE_W}px; height:{SLIDE_H}px; overflow:hidden; }}
.slide {{ width:{SLIDE_W}px; height:{SLIDE_H}px; display:flex; flex-direction:column; justify-content:center; align-items:center; position:relative; }}
</style>
</head><body>{slide_content}</body></html>"""


# ============================================================
# SECTION TRANSITION SLIDES (Hero's Journey chapter openers)
# ============================================================

def section_transition(section_num, section_label, title, subtitle="", bg=DEEP_NAVY, accent=GOLD, icon_svg=""):
    """Full-bleed section divider slide with big number, label, and title."""
    icon_html = f'<div style="position:absolute; top:50%; right:120px; transform:translateY(-50%); opacity:0.07;">{scale_icon(icon_svg, 320)}</div>' if icon_svg else ""
    sub_html = f'<p style="font-family:\'Open Sans\',sans-serif; font-weight:400; font-size:28px; color:{"rgba(255,255,255,0.5)" if bg == DEEP_NAVY else DARK_NAVY}; margin-top:24px; max-width:1000px; line-height:1.5; opacity:0.7;">{subtitle}</p>' if subtitle else ""
    text_color = WHITE_BG if bg == DEEP_NAVY else DEEP_NAVY
    num_color = accent

    # Progress dots at bottom
    dots = ""
    for i in range(1, 8):
        active = "1" if i <= section_num else "0.25"
        dots += f'<div style="width:{"40px" if i == section_num else "12px"}; height:12px; border-radius:6px; background:{accent}; opacity:{active};"></div>'
    progress = f'<div style="position:absolute; bottom:50px; left:80px; display:flex; gap:10px; align-items:center;">{dots}</div>'

    return build_slide_html(f"""
<div class="slide" style="background:{bg}; padding:100px 140px; text-align:left;">
    {icon_html}
    <!-- section number -->
    <div style="font-family:'Poppins',sans-serif; font-weight:800; font-size:180px; color:{num_color}; opacity:0.12; position:absolute; top:40px; left:100px; line-height:1;">{section_num}</div>
    <!-- section label -->
    <div style="margin-bottom:16px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:20px; color:{accent}; letter-spacing:4px; text-transform:uppercase;">{section_label}</span>
    </div>
    <!-- title -->
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:64px; color:{text_color}; line-height:1.12; max-width:1200px;">{title}</h1>
    <div style="width:80px; height:5px; background:{accent}; margin:30px 0; border-radius:3px;"></div>
    {sub_html}
    {progress}
    {FOOTER}
</div>""")


# ============================================================
# SLIDE 1: TITLE
# ============================================================
def slide_title():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; text-align:center; padding:80px;">
    <div style="position:absolute; top:-60px; right:-60px; width:300px; height:300px; border-radius:50%; border:2px solid {GOLD}; opacity:0.12;"></div>
    <div style="position:absolute; bottom:-80px; left:-80px; width:400px; height:400px; border-radius:50%; border:2px solid {BLUE}; opacity:0.08;"></div>
    <div style="position:absolute; top:60px; left:80px;">
        <div style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:22px; color:{DARK_NAVY}; letter-spacing:3px;">KEYNOTE</div>
    </div>
    <div style="width:120px; height:6px; background:{GOLD}; margin-bottom:50px; border-radius:3px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:68px; color:{DEEP_NAVY}; letter-spacing:-2px; line-height:1.1; max-width:1500px;">FROM SAAS TO AGENTS</h1>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; margin-top:16px; opacity:0.6; max-width:1100px;">The End of Software You Rent</p>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px 0; border-radius:2px;"></div>
    <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:28px; color:{DARK_NAVY}; letter-spacing:1px;">Richmond &nbsp;|&nbsp; CEO & Founder</p>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:24px; color:{DARK_NAVY}; margin-top:10px; opacity:0.7;">Bishop AI &nbsp;+&nbsp; Prompt Anything</p>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 1: THE ORDINARY WORLD (Origin Story)
# ============================================================
def slide_origin():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; top:80px; right:120px; opacity:0.12;">{scale_icon(ICON_BRIEFCASE, 180)}</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE BEGINNING</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:72px; color:{DEEP_NAVY}; line-height:1.1;">Corporate. Sales. GTM.</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:35px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; line-height:1.6; max-width:1200px;">Director to CRO track. Salesforce ecosystem.</p>
    {FOOTER}
</div>""")


def slide_breaking_point():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; top:80px; right:120px; opacity:0.15;">{scale_icon(ICON_WARNING, 160)}</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{RED_CORAL}; letter-spacing:3px;">THE BREAKING POINT</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:66px; color:{DEEP_NAVY}; line-height:1.15; max-width:1400px;">Toxic culture.<br>No change.<br><span style="color:{RED_CORAL};">Especially with AI.</span></h1>
    {FOOTER}
</div>""")


def slide_i_quit():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; text-align:center; padding:80px;">
    <div style="position:absolute; top:40px; left:60px; display:flex; gap:12px; opacity:0.15;">
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:140px; color:{WHITE_BG}; letter-spacing:-3px;">I quit.</h1>
    <div style="width:100px; height:5px; background:{GOLD}; margin:40px auto; border-radius:3px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:300; font-size:28px; color:{OFF_WHITE}; opacity:0.7;">Six months into the role of my life.<br>No backup plan. No investors. No safety net.</p>
    {FOOTER}
</div>""")


def slide_show_of_hands():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:40px; left:60px; display:flex; gap:12px; opacity:0.15;">
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
        <div style="width:10px; height:10px; border-radius:50%; background:{GOLD};"></div>
    </div>
    <div style="margin-bottom:24px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">SHOW OF HANDS</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:58px; color:{WHITE_BG}; line-height:1.2; max-width:1300px; margin:0 auto;">Who here has Googled<br><span style="color:{GOLD};">"will AI take my job"</span><br>in the last six months?</h1>
    <div style="width:100px; height:5px; background:{GOLD}; margin:40px auto; border-radius:3px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:300; font-size:26px; color:{OFF_WHITE}; opacity:0.6; max-width:1000px; margin:0 auto;">That is a tough title to carry into a room full of people who have jobs.</p>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 2: THE CALL TO ADVENTURE (The Data)
# ============================================================
def slide_sergey():
    """Sergey Brin hackathon story - the non-answer that said everything."""
    return build_slide_html(f"""
<div class="slide" style="background:{OFF_WHITE}; padding:100px 140px; text-align:left;">
    <!-- large quote mark -->
    <div style="position:absolute; top:60px; left:100px; font-family:'Poppins',sans-serif; font-weight:800; font-size:300px; color:{GOLD}; opacity:0.08; line-height:1;">&ldquo;</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE QUESTION</span>
    </div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:30px; color:{DARK_NAVY}; line-height:1.6; max-width:1300px; margin-top:10px;">I asked Sergey Brin, co-founder of Google, at a hackathon:</p>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:46px; color:{DEEP_NAVY}; line-height:1.2; max-width:1300px; margin-top:30px;">"What are your thoughts on the transition from Software as a Service to Agents as a Service?"</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:35px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:30px; color:{DARK_NAVY}; line-height:1.6; max-width:1300px;">His answer: <span style="font-family:'Poppins',sans-serif; font-weight:600; color:{GOLD};">Nobody knows what is happening in the future, but it is very exciting what is coming.</span></p>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:26px; color:{DARK_NAVY}; margin-top:24px; opacity:0.6;">A non-answer from someone whose words move markets.<br>100 people in that room heard it loud and clear.</p>
    {FOOTER}
</div>""")


def slide_stat(label, stat, subtitle, stat_color=GOLD, label_color=None, accent="gold", icon=""):
    if label_color is None:
        label_color = GOLD if accent == "gold" else RED_CORAL if accent == "red" else BLUE
    bar_color = GOLD if accent == "gold" else RED_CORAL if accent == "red" else BLUE
    icon_html = f'<div style="position:absolute; top:80px; right:120px; opacity:0.12;">{icon}</div>' if icon else ""
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    {icon_html}
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{label_color}; letter-spacing:3px;">{label}</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:120px; color:{stat_color}; line-height:1; letter-spacing:-3px;">{stat}</h1>
    <div style="width:80px; height:4px; background:{bar_color}; margin:30px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; line-height:1.5; max-width:1200px;">{subtitle}</p>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 3: CROSSING THE THRESHOLD (The Leap)
# ============================================================
def slide_stat_dual(label1, stat1, sub1, label2, stat2, sub2, accent_color=RED_CORAL):
    """Two stats side-by-side for denser data slides."""
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:80px 140px; text-align:left;">
    <div style="display:flex; gap:80px; width:100%;">
        <div style="flex:1;">
            <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{accent_color}; letter-spacing:3px;">{label1}</span>
            <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:90px; color:{accent_color}; line-height:1; letter-spacing:-2px; margin-top:16px;">{stat1}</h1>
            <div style="width:60px; height:4px; background:{accent_color}; margin:24px 0; border-radius:2px;"></div>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{DARK_NAVY}; line-height:1.5;">{sub1}</p>
        </div>
        <div style="width:3px; background:{OFF_WHITE};"></div>
        <div style="flex:1;">
            <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{accent_color}; letter-spacing:3px;">{label2}</span>
            <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:90px; color:{accent_color}; line-height:1; letter-spacing:-2px; margin-top:16px;">{stat2}</h1>
            <div style="width:60px; height:4px; background:{accent_color}; margin:24px 0; border-radius:2px;"></div>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{DARK_NAVY}; line-height:1.5;">{sub2}</p>
        </div>
    </div>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 4: TESTS & ALLIES (Building in Public)
# ============================================================
def slide_bishop_ai():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">WHO WE ARE</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:64px; color:{DEEP_NAVY}; line-height:1.15;">Bishop AI / Prompt Anything</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:35px 0; border-radius:2px;"></div>
    <div style="display:flex; gap:60px; margin-top:20px;">
        <div style="flex:1; background:{OFF_WHITE}; padding:40px; border-radius:16px; border-top:4px solid {GOLD};">
            <div style="margin-bottom:16px; opacity:0.7;">{ICON_ROCKET}</div>
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:26px; color:{DEEP_NAVY};">Bishop AI</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY}; margin-top:12px; line-height:1.6;">We help businesses replace their software with agents. Not whitepapers. Real builds.</p>
        </div>
        <div style="flex:1; background:{OFF_WHITE}; padding:40px; border-radius:16px; border-top:4px solid {BLUE};">
            <div style="margin-bottom:16px; opacity:0.7;">{ICON_LIGHTNING}</div>
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:26px; color:{DEEP_NAVY};">Prompt Anything</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY}; margin-top:12px; line-height:1.6;">Anyone becomes an expert prompt engineer. Bring the idea. We build the prompt, pick the model, deliver the result.</p>
        </div>
    </div>
    {FOOTER}
</div>""")


def slide_prompt_bridge():
    """The bridge metaphor - people stopped asking how to use AI, started asking to replace software."""
    return build_slide_html(f"""
<div class="slide" style="background:{OFF_WHITE}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); opacity:0.06;">{scale_icon(ICON_BRIDGE, 500)}</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE SHIFT IN DEMAND</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{DEEP_NAVY}; line-height:1.2; max-width:1200px;">They stopped asking<br>how to <span style="opacity:0.4; text-decoration:line-through;">use AI.</span></h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:58px; color:{GOLD}; line-height:1.2;">They started asking us<br>to replace their software.</h1>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 5: THE ORDEAL & REVELATION
# ============================================================
def slide_docusign():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:60px; right:100px; opacity:0.12;">{scale_icon(ICON_LIGHTNING, 160)}</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE MOMENT</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:60px; color:{DEEP_NAVY}; line-height:1.15;">We built DocuSign<br>in <span style="color:{GOLD};">30 minutes.</span></h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <div style="width:600px; height:16px; background:{OFF_WHITE}; border-radius:8px; margin:20px auto; overflow:hidden;">
        <div style="width:100%; height:100%; background:linear-gradient(90deg, {GOLD}, {BLUE}); border-radius:8px;"></div>
    </div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:24px; color:{DARK_NAVY}; opacity:0.5; margin-top:8px;">0 min &mdash;&mdash;&mdash;&mdash; 30 min</p>
    {FOOTER}
</div>""")


def slide_anyone_can():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:0; left:0; width:100%; height:100%; overflow:hidden; opacity:0.06;">
        <div style="position:absolute; top:100px; left:200px; width:400px; height:2px; background:{GOLD};"></div>
        <div style="position:absolute; top:100px; left:600px; width:2px; height:300px; background:{GOLD};"></div>
        <div style="position:absolute; top:400px; left:600px; width:500px; height:2px; background:{GOLD};"></div>
        <div style="position:absolute; top:200px; right:300px; width:2px; height:400px; background:{BLUE};"></div>
        <div style="position:absolute; bottom:200px; left:100px; width:600px; height:2px; background:{BLUE};"></div>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:68px; color:{WHITE_BG}; line-height:1.15;">Software is now a <span style="color:{GOLD};">commodity.</span></h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{OFF_WHITE}; opacity:0.7; max-width:1100px; margin:0 auto;">A client paid $40,000/year for DocuSign.<br>We rebuilt it in one prompt. They cancelled that week.</p>
    {FOOTER}
</div>""")


def slide_agentforce():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; top:70px; right:100px; opacity:0.1;">{scale_icon(ICON_GLOBE, 160)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{BLUE}; letter-spacing:3px;">SALESFORCE IS BURNING THE SAAS PLAYBOOK</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:110px; color:{GOLD}; line-height:1; letter-spacing:-3px;">$540M ARR</h1>
    <div style="width:80px; height:4px; background:{BLUE}; margin:30px 0; border-radius:2px;"></div>
    <div style="display:flex; gap:80px; margin-top:10px;">
        <div style="background:{OFF_WHITE}; padding:24px 32px; border-radius:12px;">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:42px; color:{BLUE};">330%</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY};">YoY Growth</p>
        </div>
        <div style="background:{OFF_WHITE}; padding:24px 32px; border-radius:12px;">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:42px; color:{BLUE};">18,500</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY};">Deals in Q4</p>
        </div>
        <div style="background:{OFF_WHITE}; padding:24px 32px; border-radius:12px;">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:42px; color:{BLUE};">2.4B</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY};">Agentic Work Units</p>
        </div>
    </div>
    {FOOTER}
</div>""")


def slide_zendesk():
    """Zendesk pay-per-outcome — the single most powerful pricing shift slide."""
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; top:70px; right:100px; opacity:0.1;">{scale_icon(ICON_DOLLAR, 180)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">PAY PER OUTCOME &middot; ZENDESK</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:160px; color:{GOLD}; line-height:1; letter-spacing:-5px;">$1.50</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:30px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; line-height:1.5; max-width:1300px;">Per AI-resolved customer issue.<br><span style="font-family:'Poppins',sans-serif; font-weight:700; color:{DEEP_NAVY};">Not per agent. Not per seat. Per outcome.</span></p>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:26px; color:{DARK_NAVY}; margin-top:28px; opacity:0.55;">You pay for what gets done, not for who is sitting at a desk.</p>
    {FOOTER}
</div>""")


def slide_agent_economics():
    return build_slide_html(f"""
<div class="slide" style="background:{OFF_WHITE}; padding:100px 140px; text-align:center;">
    <div style="position:absolute; top:60px; right:100px; opacity:0.1;">{scale_icon(ICON_DOLLAR, 150)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">AGENT ECONOMICS</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:140px; color:{GOLD}; line-height:1; letter-spacing:-4px;">$1.44<span style="font-size:60px; color:{DEEP_NAVY};">/hr</span></h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:30px auto; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; line-height:1.5;">To run an AI agent. 24/7. 100 tokens/second.</p>
    <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:22px; color:{DARK_NAVY}; margin-top:15px; opacity:0.6;">Andrew Ng</p>
    {FOOTER}
</div>""")


def slide_cost_curve():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; bottom:120px; right:100px; display:flex; align-items:flex-end; gap:20px; opacity:0.15;">
        <div style="width:30px; height:200px; background:{BLUE}; border-radius:6px 6px 0 0;"></div>
        <div style="width:30px; height:140px; background:{BLUE}; border-radius:6px 6px 0 0;"></div>
        <div style="width:30px; height:80px; background:{BLUE}; border-radius:6px 6px 0 0;"></div>
        <div style="width:30px; height:40px; background:{GOLD}; border-radius:6px 6px 0 0;"></div>
        <div style="width:30px; height:16px; background:{GOLD}; border-radius:6px 6px 0 0;"></div>
    </div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{BLUE}; letter-spacing:3px;">PLATFORM SHIFT</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:120px; color:{BLUE}; line-height:1; letter-spacing:-3px;">1,000x</h1>
    <div style="width:80px; height:4px; background:{BLUE}; margin:30px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:32px; color:{DARK_NAVY}; line-height:1.5;">LLM inference cost drop in 3 years.</p>
    <div style="display:flex; gap:60px; margin-top:40px;">
        <div style="background:{OFF_WHITE}; padding:24px 32px; border-radius:12px;">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:42px; color:{GOLD};">27 &rarr; 90</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY};">Inference providers</p>
        </div>
        <div style="background:{OFF_WHITE}; padding:24px 32px; border-radius:12px;">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:42px; color:{GOLD};">253 &rarr; 650+</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{DARK_NAVY};">Available models</p>
        </div>
    </div>
    {FOOTER}
</div>""")


def slide_the_shift():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); opacity:0.06;">{scale_icon(ICON_ARROW_SHIFT, 600)}</div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:58px; color:{DARK_NAVY}; line-height:1.3; text-decoration:line-through; opacity:0.4;">Software as a Service</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:72px; color:{GOLD}; line-height:1.15;">Agents as a Service</h1>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{DARK_NAVY}; margin-top:30px; opacity:0.6;">This is not an upgrade. This is the next platform.<br>And it has already started without you.</p>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 6: THE REWARD
# ============================================================
def slide_business_in_box():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; padding:100px 140px; text-align:center;">
    <div style="position:absolute; top:50px; right:80px; opacity:0.08;">{scale_icon(ICON_CUBE, 180)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE PRODUCT</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:68px; color:{WHITE_BG}; line-height:1.15;">Business in a Box</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:35px auto; border-radius:2px;"></div>
    <div style="display:flex; gap:50px; justify-content:center; margin-top:30px;">
        <div style="background:rgba(255,255,255,0.08); padding:40px 50px; border-radius:16px; border:1px solid rgba(224,184,72,0.3);">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:48px; color:{GOLD};">50</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{OFF_WHITE};">employees</p>
        </div>
        <div style="background:rgba(255,255,255,0.08); padding:40px 50px; border-radius:16px; border:1px solid rgba(224,184,72,0.3);">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:48px; color:{GOLD};">100</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{OFF_WHITE};">employees</p>
        </div>
        <div style="background:rgba(255,255,255,0.08); padding:40px 50px; border-radius:16px; border:1px solid rgba(224,184,72,0.3);">
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:48px; color:{GOLD};">1,000</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{OFF_WHITE};">employees</p>
        </div>
    </div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:26px; color:{OFF_WHITE}; margin-top:35px; opacity:0.7;">Custom to who you are and what you do.</p>
    {FOOTER}
</div>""")


def slide_market_size():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:80px 140px; text-align:left;">
    <div style="position:absolute; top:60px; right:100px; opacity:0.1;">{scale_icon(ICON_TARGET, 140)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">MARKET OPPORTUNITY</span>
    </div>
    <div style="display:flex; gap:50px; align-items:flex-start; margin-top:20px;">
        <div style="flex:1; background:{OFF_WHITE}; padding:45px; border-radius:16px;">
            <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:18px; color:{DARK_NAVY}; letter-spacing:2px; opacity:0.6;">SAAS TODAY</p>
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{DEEP_NAVY}; margin-top:10px;">$315-430B</p>
        </div>
        <div style="flex:1; background:{OFF_WHITE}; padding:45px; border-radius:16px; border:2px solid {GOLD};">
            <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:18px; color:{GOLD}; letter-spacing:2px;">AGENTIC AI BY 2030</p>
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{GOLD}; margin-top:10px;">$52.6B</p>
        </div>
        <div style="flex:1; background:{OFF_WHITE}; padding:45px; border-radius:16px; border:2px solid {BLUE};">
            <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:18px; color:{BLUE}; letter-spacing:2px;">CAGR</p>
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{BLUE}; margin-top:10px;">44-46%</p>
        </div>
    </div>
    <div style="margin-top:40px; background:{OFF_WHITE}; padding:30px 40px; border-radius:12px; border-left:4px solid {GOLD};">
        <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:26px; color:{DARK_NAVY};">Most important emerging role of 2026: <span style="font-family:'Montserrat',sans-serif; font-weight:700; color:{GOLD};">AI Orchestration Specialist</span></p>
        <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:20px; color:{DARK_NAVY}; opacity:0.6; margin-top:8px;">Eightfold AI</p>
    </div>
    {FOOTER}
</div>""")


def slide_your_journey():
    """The hero's journey is not my story. It's yours."""
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; text-align:center; padding:100px 160px;">
    <div style="width:80px; height:4px; background:{GOLD}; margin:0 auto 50px; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:58px; color:{WHITE_BG}; line-height:1.2; max-width:1100px; margin:0 auto;">The hero's journey<br>is not my story.</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:68px; color:{GOLD}; line-height:1.15;">It's yours.</h1>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{OFF_WHITE}; margin-top:30px; opacity:0.6; max-width:900px;">You are sitting in the same seat I was two years ago.<br>The world is moving. The question is whether you move with it.</p>
    {FOOTER}
</div>""")


# ============================================================
# SECTION 7: THE RETURN / CTA
# ============================================================
def slide_not_too_late():
    """You are not too late. But you are running out of early."""
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; text-align:center; padding:100px 160px;">
    <!-- urgency visual: shrinking time bar -->
    <div style="width:800px; height:12px; background:{OFF_WHITE}; border-radius:6px; margin:0 auto 60px; overflow:hidden; position:relative;">
        <div style="width:35%; height:100%; background:linear-gradient(90deg, {GOLD}, {RED_CORAL}); border-radius:6px;"></div>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:56px; color:{DEEP_NAVY}; line-height:1.2;">You are not too late.</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:40px auto; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:56px; color:{RED_CORAL}; line-height:1.2;">But you are running<br>out of early.</h1>
    {FOOTER}
</div>""")


def slide_cta():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; padding:80px 120px; text-align:center;">
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:18px; color:{GOLD}; letter-spacing:4px;">WHERE TO GO NEXT</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{WHITE_BG}; line-height:1.15; margin-bottom:50px;">Three ways to go deeper.</h1>
    <div style="display:flex; gap:40px; justify-content:center;">
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:44px 36px; border-radius:20px; text-align:center; border:1px solid rgba(255,255,255,0.1); border-top:4px solid {BLUE};">
            <div style="font-family:'Poppins',sans-serif; font-weight:800; font-size:44px; color:{BLUE}; line-height:1;">1</div>
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:22px; color:{WHITE_BG}; margin:16px 0 8px;">Follow on LinkedIn</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:600; font-size:18px; color:{BLUE}; margin-bottom:12px;">@RichmondTaylor</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:18px; color:{OFF_WHITE}; opacity:0.7; line-height:1.5;">Daily builds. Real results.<br>Zero fluff.</p>
            <div style="width:110px; height:110px; margin:24px auto 0; background:rgba(255,255,255,0.9); border-radius:12px; display:flex; align-items:center; justify-content:center;">
                <span style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:13px; color:{DARK_NAVY}; letter-spacing:1px;">QR CODE</span>
            </div>
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:44px 36px; border-radius:20px; text-align:center; border:1px solid rgba(255,255,255,0.1); border-top:4px solid {GOLD};">
            <div style="font-family:'Poppins',sans-serif; font-weight:800; font-size:44px; color:{GOLD}; line-height:1;">2</div>
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:22px; color:{WHITE_BG}; margin:16px 0 8px;">Free AI Audit</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:600; font-size:18px; color:{GOLD}; margin-bottom:12px;">Bishop AI</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:18px; color:{OFF_WHITE}; opacity:0.7; line-height:1.5;">We identify exactly which tools<br>agents can replace this quarter.</p>
            <div style="width:110px; height:110px; margin:24px auto 0; background:rgba(255,255,255,0.9); border-radius:12px; display:flex; align-items:center; justify-content:center;">
                <span style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:13px; color:{DARK_NAVY}; letter-spacing:1px;">QR CODE</span>
            </div>
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:44px 36px; border-radius:20px; text-align:center; border:1px solid rgba(255,255,255,0.1); border-top:4px solid {GOLD};">
            <div style="font-family:'Poppins',sans-serif; font-weight:800; font-size:44px; color:{GOLD}; line-height:1;">3</div>
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:22px; color:{WHITE_BG}; margin:16px 0 8px;">Free Skool Community</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:600; font-size:18px; color:{GOLD}; margin-bottom:12px;">Free to join</p>
            <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:18px; color:{OFF_WHITE}; opacity:0.7; line-height:1.5;">Courses + 3 agents: doc signing,<br>competitor intel &amp; Prompt Anything.</p>
            <div style="width:110px; height:110px; margin:24px auto 0; background:rgba(255,255,255,0.9); border-radius:12px; display:flex; align-items:center; justify-content:center;">
                <span style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:13px; color:{DARK_NAVY}; letter-spacing:1px;">QR CODE</span>
            </div>
        </div>
    </div>
    {FOOTER}
</div>""")


def slide_closer():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; text-align:center; padding:100px 160px;">
    <div style="position:absolute; top:-40px; left:-40px; width:200px; height:200px; border-radius:50%; border:2px solid {GOLD}; opacity:0.08;"></div>
    <div style="position:absolute; bottom:-60px; right:-60px; width:300px; height:300px; border-radius:50%; border:2px solid {BLUE}; opacity:0.06;"></div>
    <div style="width:80px; height:4px; background:{GOLD}; margin:0 auto 50px; border-radius:2px;"></div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:52px; color:{WHITE_BG}; line-height:1.25; max-width:1100px; margin:0 auto;">Build the future.<br>Or <span style="color:{GOLD};">subscribe</span> to<br>someone else's.</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:50px auto 40px; border-radius:2px;"></div>
    <p style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:28px; color:{OFF_WHITE};">Richmond</p>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:22px; color:{OFF_WHITE}; margin-top:10px; opacity:0.6;">@bishopaihq &nbsp;&middot;&nbsp; bishopaihq.com</p>
    {FOOTER}
</div>""")


# ============================================================
# NEW SLIDES for the trimmed deck
# ============================================================
def slide_what_are_agents():
    return build_slide_html(f"""
<div class="slide" style="background:{WHITE_BG}; padding:100px 140px; text-align:left;">
    <div style="position:absolute; top:80px; right:120px; opacity:0.1;">{scale_icon(ICON_CHIP, 180)}</div>
    <div style="margin-bottom:20px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{BLUE}; letter-spacing:3px;">WHAT ARE AGENTS</span>
    </div>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:64px; color:{DEEP_NAVY}; line-height:1.1; max-width:1500px;">Stop calling them chatbots.</h1>
    <div style="width:80px; height:4px; background:{GOLD}; margin:35px 0; border-radius:2px;"></div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{DARK_NAVY}; line-height:1.5; max-width:1500px;">A chatbot waits for a question.<br>An <span style="font-weight:700; color:{DEEP_NAVY};">agent</span> takes the action, checks the result, decides what to do next, and keeps going until the job is done.</p>
    <div style="display:flex; gap:50px; margin-top:50px;">
        <div style="flex:1; background:{OFF_WHITE}; padding:35px 40px; border-radius:14px; border-left:4px solid {DARK_NAVY};">
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:20px; color:{DARK_NAVY}; opacity:0.6; letter-spacing:2px;">SAAS</p>
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:30px; color:{DEEP_NAVY}; margin-top:10px;">Software you log into.</p>
        </div>
        <div style="flex:1; background:{OFF_WHITE}; padding:35px 40px; border-radius:14px; border-left:4px solid {GOLD};">
            <p style="font-family:'Montserrat',sans-serif; font-weight:700; font-size:20px; color:{GOLD}; letter-spacing:2px;">AGENT</p>
            <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:30px; color:{DEEP_NAVY}; margin-top:10px;">Software that logs in for you.</p>
        </div>
    </div>
    {FOOTER}
</div>""")


def slide_830_billion():
    return build_slide_html(f"""
<div class="slide" style="background:{DEEP_NAVY}; padding:100px 140px; text-align:center;">
    <div style="position:absolute; top:60px; right:100px; opacity:0.08;">{scale_icon(ICON_PEOPLE, 200)}</div>
    <div style="margin-bottom:15px;">
        <span style="font-family:'Montserrat',sans-serif; font-weight:600; font-size:20px; color:{GOLD}; letter-spacing:3px;">THE REFRAME</span>
    </div>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:28px; color:{OFF_WHITE}; opacity:0.7;">Everyone is asking the wrong question.<br>It is not <em>will AI take my job.</em></p>
    <h1 style="font-family:'Poppins',sans-serif; font-weight:800; font-size:160px; color:{GOLD}; line-height:1; letter-spacing:-4px; margin-top:30px;">830B</h1>
    <p style="font-family:'Open Sans',sans-serif; font-weight:400; font-size:24px; color:{OFF_WHITE}; opacity:0.55; margin-top:10px;">8.3 billion humans. Each with 100 agents working alongside them.</p>
    <div style="width:100px; height:5px; background:{GOLD}; margin:24px auto; border-radius:3px;"></div>
    <p style="font-family:'Poppins',sans-serif; font-weight:800; font-size:36px; color:{WHITE_BG}; line-height:1.3; max-width:1300px; margin:0 auto;">The internet did not eliminate salespeople.<br>It eliminated the ones who kept working off a <span style="color:{GOLD};">Rolodex.</span><br><span style="font-size:28px; opacity:0.7;">This is that moment. Your ceiling disappears.</span></p>
    {FOOTER}
</div>""")


# ============================================================
# Large icons for stat slides
# ============================================================
ICON_CHART_DOWN_LG = scale_icon(ICON_CHART_DOWN, 160)
ICON_ROCKET_LG = scale_icon(ICON_ROCKET, 160)
ICON_DOLLAR_LG = scale_icon(ICON_DOLLAR, 160)
ICON_PEOPLE_LG = scale_icon(ICON_PEOPLE, 160)
ICON_WARNING_LG = scale_icon(ICON_WARNING, 160)
ICON_TARGET_LG = scale_icon(ICON_TARGET, 160)


# ============================================================
# FULL SLIDE ORDER - FROM SAAS TO AGENTS (updated)
# ============================================================
slides = [
    # --- TITLE ---
    slide_title(),                                                                           # 1

    # --- OPENER ---
    slide_show_of_hands(),                                                                   # 2

    # --- SECTION 1: ORIGIN STORY ---
    section_transition(1, "Origin Story", "I walked away from<br>the role of my life.",
                       bg=DEEP_NAVY, accent=GOLD, icon_svg=ICON_BRIEFCASE),                  # 3
    slide_origin(),                                                                          # 4
    slide_breaking_point(),                                                                  # 5
    slide_i_quit(),                                                                          # 6

    # --- SECTION 2: THE SHIFT ---
    section_transition(2, "The Shift", "I did not follow passion.<br>I followed the data.",
                       bg=DEEP_NAVY, accent=RED_CORAL, icon_svg=ICON_CHART_DOWN),            # 7
    slide_stat("THE GIANT IS LIMPING", "17% to 12.2%",
               "Median SaaS revenue growth collapsed in 24 months.",
               stat_color=RED_CORAL, accent="red", icon=ICON_CHART_DOWN_LG),                 # 8
    slide_stat_dual("PER-SEAT IS DYING", "21% to 15%",
                    "Companies stopped paying for chairs.",
                    "OUTCOMES ARE WINNING", "27% to 41%",
                    "They started paying for results.",
                    accent_color=GOLD),                                                       # 9

    # --- SECTION 3: WHAT ARE AGENTS ---
    section_transition(3, "What Are Agents?", "Software that works<br>while you sleep.",
                       bg=DEEP_NAVY, accent=BLUE, icon_svg=ICON_CHIP),                       # 10
    slide_what_are_agents(),                                                                 # 11
    slide_sergey(),                                                                          # 12

    # --- SECTION 4: THE INDUSTRY SIGNAL ---
    section_transition(4, "The Industry Signal", "If you don't believe me,<br>follow the money.",
                       bg=DEEP_NAVY, accent=GOLD, icon_svg=ICON_DOLLAR),                     # 13
    slide_agentforce(),                                                                      # 14
    slide_zendesk(),                                                                         # 15
    slide_market_size(),                                                                     # 16
    slide_the_shift(),                                                                       # 17

    # --- SECTION 5: YOU WILL NOT LOSE YOUR JOB ---
    section_transition(5, "You Will Not Lose Your Job", "AI does not replace people.<br>It removes the ceiling.",
                       bg=DEEP_NAVY, accent=GOLD, icon_svg=ICON_PEOPLE),                     # 18
    slide_830_billion(),                                                                     # 19

    # --- SECTION 6: THE INVITATION ---
    slide_not_too_late(),                                                                    # 20
    slide_cta(),                                                                             # 21
    slide_closer(),                                                                          # 22
]

TOTAL = len(slides)

CANVA_DIR = os.path.join(OUTPUT_DIR, "canva_slides")

async def render_slides():
    os.makedirs(CANVA_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        pdf_files = []

        for i, html in enumerate(slides):
            page = await browser.new_page(viewport={"width": SLIDE_W, "height": SLIDE_H})
            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(800)

            # PDF slide
            tmp = os.path.join(OUTPUT_DIR, f"_slide_{i+1:02d}.pdf")
            await page.pdf(
                path=tmp,
                width=f"{SLIDE_W}px",
                height=f"{SLIDE_H}px",
                print_background=True,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
            )
            pdf_files.append(tmp)

            # PNG slide for Canva
            png_path = os.path.join(CANVA_DIR, f"slide_{i+1:02d}.png")
            await page.screenshot(path=png_path, full_page=False)

            await page.close()
            print(f"  Rendered slide {i+1}/{TOTAL}")

        await browser.close()

    # Merge PDF
    writer = PdfWriter()
    for f in pdf_files:
        reader = PdfReader(f)
        for pg in reader.pages:
            writer.add_page(pg)

    with open(FINAL_PDF, "wb") as out:
        writer.write(out)

    for f in pdf_files:
        os.remove(f)

    print(f"\nDone! {TOTAL} slides saved to:")
    print(f"  PDF: {FINAL_PDF}")
    print(f"  Canva PNGs: {CANVA_DIR}/")


asyncio.run(render_slides())
