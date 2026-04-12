"""
PromptAnything.io Trade Show Presentation
Bishop AI Branding | PDF Output
"""
import asyncio
import os
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from pypdf import PdfWriter, PdfReader

OUTPUT_DIR = r"c:\Users\richm\.claude\temp"
FINAL_PDF = os.path.join(OUTPUT_DIR, "PromptAnything_TradeShow_2026.pdf")

# Bishop AI Brand Colors
DEEP_NAVY = "#000813"
DARK_NAVY = "#1D2333"
OFF_WHITE = "#E6E2DE"
WHITE = "#FAFBFA"
GOLD = "#E0B848"
BLUE = "#1894C9"
RED_CORAL = "#E05252"

COMMON_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Montserrat:wght@400;500;600;700&family=Open+Sans:wght@300;400;600&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1920px;
    min-height: 1080px;
    font-family: 'Open Sans', sans-serif;
    background: {WHITE};
    color: {DEEP_NAVY};
    overflow: hidden;
}}

.slide {{
    width: 1920px;
    height: 1080px;
    padding: 80px 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    overflow: hidden;
}}

h1 {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 64px;
    line-height: 1.1;
    color: {DEEP_NAVY};
    margin-bottom: 30px;
}}

h2 {{
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 44px;
    line-height: 1.2;
    color: {DEEP_NAVY};
    margin-bottom: 24px;
}}

h3 {{
    font-family: 'Montserrat', sans-serif;
    font-weight: 600;
    font-size: 28px;
    color: {DEEP_NAVY};
    margin-bottom: 12px;
}}

p {{
    font-family: 'Open Sans', sans-serif;
    font-weight: 400;
    font-size: 22px;
    line-height: 1.6;
    color: {DARK_NAVY};
}}

.gold {{ color: {GOLD}; }}
.blue {{ color: {BLUE}; }}
.red {{ color: {RED_CORAL}; }}

.accent-bar {{
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 8px;
    background: linear-gradient(90deg, {GOLD}, {BLUE});
}}

.eyebrow {{
    font-family: 'Montserrat', sans-serif;
    font-weight: 600;
    font-size: 16px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: {GOLD};
    margin-bottom: 16px;
}}

.footer-badge {{
    position: absolute;
    bottom: 30px;
    right: 60px;
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    font-size: 14px;
    color: {DARK_NAVY};
    opacity: 0.5;
}}
"""

slides = []

# ─── SLIDE 1: COVER ───
slides.append(f"""
<div class="slide" style="background: {WHITE}; justify-content: center; align-items: center; text-align: center;">
    <div style="margin-bottom: 40px;">
        <div style="display: inline-flex; align-items: center; gap: 20px; margin-bottom: 50px;">
            <svg width="90" height="90" viewBox="0 0 100 100">
                <rect x="10" y="10" width="70" height="65" rx="18" fill="none" stroke="{DEEP_NAVY}" stroke-width="6"/>
                <polygon points="45,25 50,40 65,45 50,50 45,65 40,50 25,45 40,40" fill="{DEEP_NAVY}"/>
                <path d="M30 75 L20 90" stroke="{DEEP_NAVY}" stroke-width="6" stroke-linecap="round"/>
            </svg>
            <div style="text-align: left;">
                <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; color: {DEEP_NAVY}; line-height: 1;">PROMPT</div>
                <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; color: {DEEP_NAVY}; line-height: 1; letter-spacing: 8px;">ANYTHING</div>
            </div>
        </div>
    </div>
    <h1 style="font-size: 56px; max-width: 1200px;">The Universal Interface for<br><span class="gold">Artificial Intelligence.</span></h1>
    <p style="font-size: 26px; max-width: 900px; margin-top: 20px; color: {DARK_NAVY};">
        Translate your ideas into precision-engineered AI instructions.<br>
        Get superior results from any AI model, every time.
    </p>
    <div style="margin-top: 50px; display: flex; gap: 30px; align-items: center;">
        <div style="background: {GOLD}; color: {DEEP_NAVY}; padding: 18px 50px; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 20px;">promptanything.io</div>
    </div>
    <div class="accent-bar"></div>
</div>
""")

# ─── SLIDE 2: THE PROBLEM ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow" style="color: {RED_CORAL};">THE PROBLEM</div>
    <h1 style="font-size: 58px;">AI's Biggest Bottleneck<br>Isn't the Technology. <span class="red">It's Us.</span></h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 50px; margin-top: 50px;">
        <div style="background: {OFF_WHITE}; padding: 40px; border-radius: 16px; border-left: 5px solid {RED_CORAL};">
            <h3>The Promise</h3>
            <p style="font-size: 20px;">AI models are exponentially powerful, but the vast majority of people cannot communicate their goals effectively to them.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 40px; border-radius: 16px; border-left: 5px solid {RED_CORAL};">
            <h3>The Language Barrier</h3>
            <p style="font-size: 20px;">This leads to frustration, wasted time, and mediocre results. An estimated <strong style="color: {RED_CORAL};">95% of AI users</strong> are only scratching the surface.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 40px; border-radius: 16px; border-left: 5px solid {RED_CORAL};">
            <h3>The Real Cost</h3>
            <p style="font-size: 20px;">This gap costs businesses billions in lost productivity and is the primary reason enterprise AI adoption is stalling.</p>
        </div>
    </div>
    <div style="margin-top: 50px; background: {DEEP_NAVY}; padding: 28px 50px; border-radius: 12px;">
        <p style="color: {WHITE}; font-size: 24px; font-family: 'Montserrat', sans-serif; font-weight: 600; text-align: center;">It's not the AI's fault. It's our inability to communicate with it.</p>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 3: HIDDEN COSTS ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow" style="color: {RED_CORAL};">WHY THIS MATTERS</div>
    <h1 style="font-size: 54px;">The Hidden Cost Behind Prompting</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px;">
        <div style="background: {OFF_WHITE}; padding: 36px; border-radius: 16px; display: flex; align-items: flex-start; gap: 24px;">
            <div style="min-width: 70px; height: 70px; background: {RED_CORAL}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 24px;">40%</div>
            <div>
                <h3 style="font-size: 24px;">Operational Failure</h3>
                <p style="font-size: 19px;">Up to 40% failure rate in production with competing point solutions, wasting compute and time.</p>
            </div>
        </div>
        <div style="background: {OFF_WHITE}; padding: 36px; border-radius: 16px; display: flex; align-items: flex-start; gap: 24px;">
            <div style="min-width: 70px; height: 70px; background: {RED_CORAL}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 24px;">80%</div>
            <div>
                <h3 style="font-size: 24px;">Wasted Spend</h3>
                <p style="font-size: 19px;">Inefficient prompts cause token waste, driving up to 80% of total cost of ownership during customization.</p>
            </div>
        </div>
        <div style="background: {OFF_WHITE}; padding: 36px; border-radius: 16px; display: flex; align-items: flex-start; gap: 24px;">
            <div style="min-width: 70px; height: 70px; background: {RED_CORAL}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 24px;">12x</div>
            <div>
                <h3 style="font-size: 24px;">Labor Inefficiency</h3>
                <p style="font-size: 19px;">Poor prompts create up to a 12x loss factor in initial iteration time for teams.</p>
            </div>
        </div>
        <div style="background: {OFF_WHITE}; padding: 36px; border-radius: 16px; display: flex; align-items: flex-start; gap: 24px;">
            <div style="min-width: 70px; height: 70px; background: {RED_CORAL}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 20px;">$270K</div>
            <div>
                <h3 style="font-size: 24px;">High Frictional Cost</h3>
                <p style="font-size: 19px;">Relies on expensive, scarce Prompt Engineers (salaries up to $270K+) doing manual, slow trial-and-error iteration.</p>
            </div>
        </div>
    </div>
    <div style="margin-top: 36px; text-align: center;">
        <p style="font-size: 22px; font-family: 'Montserrat', sans-serif; font-weight: 600; color: {RED_CORAL};">Static prompts incur a 156% opportunity cost compared to continuously optimized ones.</p>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 4: THE SOLUTION ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow" style="color: {GOLD};">THE SOLUTION</div>
    <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 80px; align-items: center;">
        <div>
            <h1 style="font-size: 52px; line-height: 1.15;">The AI Conversation Partner That <span class="gold">Understands Your Intent.</span></h1>
            <p style="font-size: 23px; margin-top: 24px; max-width: 700px;">
                We are not another prompt-fixing tool. We are the bridge between your idea and the AI's perfect execution.
            </p>
            <p style="font-size: 23px; margin-top: 20px; max-width: 700px;">
                <strong>promptanything.io</strong> is an intelligent, AI-agnostic platform that acts as your personal AI strategist, translating your natural language goals into precision-engineered instructions.
            </p>
            <div style="margin-top: 40px; display: flex; gap: 20px;">
                <div style="background: {GOLD}15; border: 2px solid {GOLD}; padding: 16px 28px; border-radius: 10px;">
                    <p style="font-size: 18px; font-weight: 600; color: {GOLD};">AI-Agnostic</p>
                </div>
                <div style="background: {BLUE}15; border: 2px solid {BLUE}; padding: 16px 28px; border-radius: 10px;">
                    <p style="font-size: 18px; font-weight: 600; color: {BLUE};">Dynamic Prompts</p>
                </div>
                <div style="background: {DEEP_NAVY}10; border: 2px solid {DEEP_NAVY}; padding: 16px 28px; border-radius: 10px;">
                    <p style="font-size: 18px; font-weight: 600; color: {DEEP_NAVY};">Auto Model Routing</p>
                </div>
            </div>
        </div>
        <div style="background: {OFF_WHITE}; border-radius: 24px; padding: 60px; display: flex; align-items: center; justify-content: center; min-height: 500px;">
            <svg width="280" height="280" viewBox="0 0 100 100">
                <rect x="10" y="10" width="70" height="65" rx="18" fill="none" stroke="{GOLD}" stroke-width="4"/>
                <polygon points="45,25 50,40 65,45 50,50 45,65 40,50 25,45 40,40" fill="{GOLD}"/>
                <path d="M30 75 L20 90" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
            </svg>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 5: HOW IT WORKS ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow">HOW IT WORKS</div>
    <h1 style="font-size: 50px; margin-bottom: 50px;">Three Steps to Superior AI Output</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 50px;">
        <div style="position: relative;">
            <div style="width: 80px; height: 80px; background: {GOLD}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;">
                <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 36px; color: {WHITE};">1</span>
            </div>
            <h2 style="font-size: 32px; color: {GOLD};">State Your Goal</h2>
            <p style="font-size: 20px; margin-top: 16px;">Type a simple, natural language request. No special syntax or "prompt engineering" jargon needed.</p>
            <div style="margin-top: 24px; background: {OFF_WHITE}; padding: 20px; border-radius: 10px; border-left: 4px solid {GOLD};">
                <p style="font-size: 17px; font-style: italic;">"I need a social media campaign to promote our new eco-friendly water bottle."</p>
            </div>
        </div>
        <div style="position: relative;">
            <div style="width: 80px; height: 80px; background: {BLUE}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;">
                <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 36px; color: {WHITE};">2</span>
            </div>
            <h2 style="font-size: 32px; color: {BLUE};">Guided Refinement</h2>
            <p style="font-size: 20px; margin-top: 16px;">Our AI engine analyzes your request and asks smart clarifying questions derived from your profile and task.</p>
            <div style="margin-top: 24px; background: {OFF_WHITE}; padding: 20px; border-radius: 10px; border-left: 4px solid {BLUE};">
                <p style="font-size: 17px; font-style: italic;">"Who is the target audience?" "What platforms?" "What tone should we use?"</p>
            </div>
        </div>
        <div style="position: relative;">
            <div style="width: 80px; height: 80px; background: {DEEP_NAVY}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;">
                <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 36px; color: {GOLD};">3</span>
            </div>
            <h2 style="font-size: 32px; color: {DEEP_NAVY};">Execute & Deliver</h2>
            <p style="font-size: 20px; margin-top: 16px;">We construct a master prompt, route it to the top-performing AI model for your task, and deliver superior output in seconds.</p>
            <div style="margin-top: 24px; background: {OFF_WHITE}; padding: 20px; border-radius: 10px; border-left: 4px solid {DEEP_NAVY};">
                <p style="font-size: 17px; font-style: italic;">Auto-routed to the best model. Ready-to-use results, instantly.</p>
            </div>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 6: TECHNOLOGY ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow">UNDER THE HOOD</div>
    <h1 style="font-size: 50px; margin-bottom: 40px;">The Technology That Powers It</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
        <div style="background: {DEEP_NAVY}; padding: 44px; border-radius: 16px;">
            <h3 style="color: {GOLD}; font-size: 26px; margin-bottom: 16px;">Dynamic Prompt Engine</h3>
            <p style="color: {OFF_WHITE}; font-size: 19px;">A proprietary system that algorithmically constructs hyper-contextualized prompts. It leverages a vast library of 'prompt components' combined with cognitive frameworks, personalized using your profile data and live answers.</p>
        </div>
        <div style="background: {DEEP_NAVY}; padding: 44px; border-radius: 16px;">
            <h3 style="color: {GOLD}; font-size: 26px; margin-bottom: 16px;">Automated Model Selection</h3>
            <p style="color: {OFF_WHITE}; font-size: 19px;">We continuously benchmark hundreds of AI models across thousands of task types, creating a proprietary real-time leaderboard. Your task is automatically routed to the current best-in-class model.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 44px; border-radius: 16px; border: 2px solid {BLUE}20;">
            <h3 style="color: {BLUE}; font-size: 26px; margin-bottom: 16px;">AI-Agnostic Architecture</h3>
            <p style="font-size: 19px;">Not tied to a single model. We integrate with and route tasks to any AI model, current or future. As new, better models emerge, you instantly benefit.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 44px; border-radius: 16px; border: 2px solid {GOLD}20;">
            <h3 style="color: {GOLD}; font-size: 26px; margin-bottom: 16px;">Continuous Benchmarking</h3>
            <p style="font-size: 19px;">A proprietary, real-time leaderboard of AI model performance across thousands of specific task types. We dynamically route each prompt to the objectively best-performing model.</p>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 7: WHY NOW ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow" style="color: {BLUE};">MARKET TIMING</div>
    <h1 style="font-size: 54px; margin-bottom: 50px;">Why Now?</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 50px;">
        <div style="text-align: center;">
            <div style="width: 120px; height: 120px; background: {GOLD}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 28px;">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="{WHITE}" stroke-width="2">
                    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"/>
                    <polyline points="16,7 22,7 22,13"/>
                </svg>
            </div>
            <h2 style="font-size: 28px;">Cambrian Explosion of AI</h2>
            <p style="font-size: 20px; margin-top: 16px;">The AI market is projected to reach <strong style="color: {GOLD};">$32 Trillion by 2034</strong>, touching nearly every aspect of the global economy.</p>
        </div>
        <div style="text-align: center;">
            <div style="width: 120px; height: 120px; background: {DARK_NAVY}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 28px;">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="{WHITE}" stroke-width="2">
                    <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
                </svg>
            </div>
            <h2 style="font-size: 28px;">Fragmentation</h2>
            <p style="font-size: 20px; margin-top: 16px;">Hundreds of specialized AI models have emerged, each excelling at different tasks. Users don't know which to choose.</p>
        </div>
        <div style="text-align: center;">
            <div style="width: 120px; height: 120px; background: {BLUE}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 28px;">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="{WHITE}" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 8v4l3 3"/>
                </svg>
            </div>
            <h2 style="font-size: 28px;">Model Fatigue</h2>
            <p style="font-size: 20px; margin-top: 16px;">Enterprises are struggling to standardize AI usage. The market needs a <strong style="color: {BLUE};">universal translator</strong> for all AIs.</p>
        </div>
    </div>
    <div style="margin-top: 50px; background: {GOLD}; padding: 28px 50px; border-radius: 12px; text-align: center;">
        <p style="color: {DEEP_NAVY}; font-size: 24px; font-family: 'Montserrat', sans-serif; font-weight: 700;">The market needs a single interface to harness the power of all AIs. That is promptanything.io.</p>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 8: PLANS & PRICING ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow">PRICING</div>
    <h1 style="font-size: 50px; margin-bottom: 50px;">Plans Built for Every Team</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; align-items: stretch;">
        <div style="background: {OFF_WHITE}; padding: 48px 40px; border-radius: 20px; text-align: center; display: flex; flex-direction: column;">
            <h3 style="font-size: 22px; color: {DARK_NAVY}; margin-bottom: 8px;">Individual</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; color: {DEEP_NAVY}; margin: 16px 0;">$15<span style="font-size: 22px; font-weight: 400;">/mo</span></div>
            <p style="font-size: 17px; color: {DARK_NAVY}; margin-bottom: 28px;">Students, freelancers, creators, and AI enthusiasts</p>
            <div style="border-top: 2px solid {DEEP_NAVY}15; padding-top: 24px; text-align: left; flex-grow: 1;">
                <p style="font-size: 17px; margin-bottom: 12px;">&#10003; Core Dynamic Prompt Generator</p>
                <p style="font-size: 17px; margin-bottom: 12px;">&#10003; 50 master prompts / month</p>
                <p style="font-size: 17px;">&#10003; Standard AI model access</p>
            </div>
        </div>
        <div style="background: {DEEP_NAVY}; padding: 48px 40px; border-radius: 20px; text-align: center; display: flex; flex-direction: column; position: relative; border: 3px solid {GOLD};">
            <div style="position: absolute; top: -16px; left: 50%; transform: translateX(-50%); background: {GOLD}; color: {DEEP_NAVY}; padding: 6px 24px; border-radius: 20px; font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 14px;">MOST POPULAR</div>
            <h3 style="font-size: 22px; color: {GOLD}; margin-bottom: 8px;">Pro / Teams</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; color: {WHITE}; margin: 16px 0;">$35<span style="font-size: 22px; font-weight: 400; color: {OFF_WHITE};">/seat/mo</span></div>
            <p style="font-size: 17px; color: {OFF_WHITE}; margin-bottom: 28px;">Professionals, startups, and growing teams</p>
            <div style="border-top: 2px solid {WHITE}20; padding-top: 24px; text-align: left; flex-grow: 1;">
                <p style="font-size: 17px; color: {OFF_WHITE}; margin-bottom: 12px;">&#10003; Unlimited prompts</p>
                <p style="font-size: 17px; color: {OFF_WHITE}; margin-bottom: 12px;">&#10003; Collaboration tools & shared libraries</p>
                <p style="font-size: 17px; color: {OFF_WHITE}; margin-bottom: 12px;">&#10003; Priority Beta model access</p>
                <p style="font-size: 17px; color: {OFF_WHITE};">&#10003; Prompt/Agent Marketplace</p>
            </div>
        </div>
        <div style="background: {OFF_WHITE}; padding: 48px 40px; border-radius: 20px; text-align: center; display: flex; flex-direction: column;">
            <h3 style="font-size: 22px; color: {DARK_NAVY}; margin-bottom: 8px;">Enterprise</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; color: {DEEP_NAVY}; margin: 16px 0;">$76<span style="font-size: 22px; font-weight: 400;">/seat/mo</span></div>
            <p style="font-size: 17px; color: {DARK_NAVY}; margin-bottom: 28px;">Large organizations scaling AI securely</p>
            <div style="border-top: 2px solid {DEEP_NAVY}15; padding-top: 24px; text-align: left; flex-grow: 1;">
                <p style="font-size: 17px; margin-bottom: 12px;">&#10003; Advanced security & compliance</p>
                <p style="font-size: 17px; margin-bottom: 12px;">&#10003; Custom brand voice training</p>
                <p style="font-size: 17px; margin-bottom: 12px;">&#10003; Detailed analytics & ROI tracking</p>
                <p style="font-size: 17px;">&#10003; Dedicated account management</p>
            </div>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 9: COMPETITIVE LANDSCAPE ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow">HOW WE COMPARE</div>
    <h1 style="font-size: 50px; margin-bottom: 16px;">Competitive Landscape</h1>
    <p style="font-size: 22px; margin-bottom: 40px;">Comparing the ability to create dynamic, context-aware prompts</p>
    <div style="display: flex; flex-direction: column; gap: 28px; max-width: 1400px;">
        <div style="display: flex; align-items: center; gap: 30px;">
            <div style="min-width: 320px; text-align: right; font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 22px;">Dynamic Prompt Generation</div>
            <div style="flex-grow: 1; background: {OFF_WHITE}; border-radius: 10px; height: 60px; position: relative; overflow: hidden;">
                <div style="width: 90%; height: 100%; background: {GOLD}; border-radius: 10px; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px;">
                    <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 28px; color: {DEEP_NAVY};">90%</span>
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 30px;">
            <div style="min-width: 320px; text-align: right; font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 22px;">Personalization & Context</div>
            <div style="flex-grow: 1; background: {OFF_WHITE}; border-radius: 10px; height: 60px; position: relative; overflow: hidden;">
                <div style="width: 85%; height: 100%; background: {BLUE}; border-radius: 10px; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px;">
                    <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 28px; color: {WHITE};">85%</span>
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 30px;">
            <div style="min-width: 320px; text-align: right; font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 22px;">Framework Integration</div>
            <div style="flex-grow: 1; background: {OFF_WHITE}; border-radius: 10px; height: 60px; position: relative; overflow: hidden;">
                <div style="width: 75%; height: 100%; background: {DARK_NAVY}; border-radius: 10px; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px;">
                    <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 28px; color: {WHITE};">75%</span>
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 30px;">
            <div style="min-width: 320px; text-align: right; font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 22px; color: {DARK_NAVY}80;">Competitors' Prompt Refinement</div>
            <div style="flex-grow: 1; background: {OFF_WHITE}; border-radius: 10px; height: 60px; position: relative; overflow: hidden;">
                <div style="width: 40%; height: 100%; background: {RED_CORAL}60; border-radius: 10px; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px;">
                    <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 28px; color: {DEEP_NAVY};">40%</span>
                </div>
            </div>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 10: MARKET OPPORTUNITY ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow" style="color: {GOLD};">MARKET SIZE</div>
    <h1 style="font-size: 50px; margin-bottom: 40px;">Market Opportunity</h1>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
        <div style="background: {GOLD}; padding: 44px; border-radius: 16px;">
            <h3 style="color: {DEEP_NAVY}; font-size: 20px; margin-bottom: 8px;">TAM (Total Addressable Market)</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 48px; color: {DEEP_NAVY}; margin-bottom: 12px;">$32T</div>
            <p style="color: {DEEP_NAVY}; font-size: 19px;">The Global AI Market by 2034. We grow as the entire ecosystem expands.</p>
        </div>
        <div style="background: {DEEP_NAVY}; padding: 44px; border-radius: 16px;">
            <h3 style="color: {GOLD}; font-size: 20px; margin-bottom: 8px;">SAM (Serviceable Addressable)</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 48px; color: {WHITE}; margin-bottom: 12px;">1B+</div>
            <p style="color: {OFF_WHITE}; font-size: 19px;">Knowledge workers and creators worldwide who directly benefit from enhanced AI productivity tools.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 44px; border-radius: 16px; border: 2px solid {BLUE}30;">
            <h3 style="color: {BLUE}; font-size: 20px; margin-bottom: 8px;">SOM (Serviceable Obtainable)</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 48px; color: {DEEP_NAVY}; margin-bottom: 12px;">10M</div>
            <p style="font-size: 19px;">Tech-forward professionals, marketers, developers, and creators in North America and Europe.</p>
        </div>
        <div style="background: {OFF_WHITE}; padding: 44px; border-radius: 16px; border: 2px solid {GOLD}30;">
            <h3 style="color: {GOLD}; font-size: 20px; margin-bottom: 8px;">3-Year Target</h3>
            <div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 48px; color: {DEEP_NAVY}; margin-bottom: 12px;">$30M ARR</div>
            <p style="font-size: 19px;">100,000 paying users at a blended $25/mo ARPU. 1% of our initial SOM.</p>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 11: ROADMAP ───
slides.append(f"""
<div class="slide" style="background: {WHITE};">
    <div class="eyebrow">WHAT'S AHEAD</div>
    <h1 style="font-size: 50px; margin-bottom: 60px;">Product Roadmap</h1>
    <div style="position: relative; padding-left: 60px;">
        <div style="position: absolute; left: 30px; top: 0; bottom: 0; width: 4px; background: linear-gradient({GOLD}, {BLUE});"></div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 36px 80px;">
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {GOLD}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {GOLD};">COMPLETED</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Public MVP Launch</h3>
                    <p style="font-size: 18px; margin-top: 6px;">Core platform live with Dynamic Prompt Engine</p>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {GOLD}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {GOLD};">COMPLETED</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Prompt/Agent Marketplace</h3>
                    <p style="font-size: 18px; margin-top: 6px;">Community marketplace with first 1,000 paying users</p>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {BLUE}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {BLUE};">IN PROGRESS</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Multi-modal Integrations</h3>
                    <p style="font-size: 18px; margin-top: 6px;">Image, Video, and Presentation Slide generation</p>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {BLUE}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {BLUE};">IN PROGRESS</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Teams/Enterprise Platform</h3>
                    <p style="font-size: 18px; margin-top: 6px;">Collaboration, Education Hub, and enterprise security</p>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {DARK_NAVY}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {DARK_NAVY};">UPCOMING</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Public Developer API</h3>
                    <p style="font-size: 18px; margin-top: 6px;">Open ecosystem for third-party integrations</p>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 20px; position: relative;">
                <div style="position: absolute; left: -48px; width: 20px; height: 20px; background: {DARK_NAVY}; border-radius: 50%; border: 4px solid {WHITE};"></div>
                <div>
                    <p style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 18px; color: {DARK_NAVY};">UPCOMING</p>
                    <h3 style="font-size: 22px; margin-top: 4px;">Autonomous Agent Capabilities</h3>
                    <p style="font-size: 18px; margin-top: 6px;">AI agents that orchestrate multi-model workflows</p>
                </div>
            </div>
        </div>
    </div>
    <div class="accent-bar"></div>
    <div class="footer-badge">promptanything.io</div>
</div>
""")

# ─── SLIDE 12: VISION ───
slides.append(f"""
<div class="slide" style="background: {DEEP_NAVY};">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; height: 100%;">
        <div>
            <div class="eyebrow" style="color: {GOLD};">THE VISION</div>
            <h1 style="color: {WHITE}; font-size: 60px; line-height: 1.1;">Where We<br>Are <span style="color: {GOLD};">Headed.</span></h1>
            <p style="color: {OFF_WHITE}; font-size: 23px; margin-top: 30px; line-height: 1.7;">
                Our platform will enable <strong style="color: {GOLD};">autonomous AI agents</strong> to orchestrate the power of multiple AI models, <strong style="color: {BLUE};">dynamically chaining tasks and tools</strong> to solve complex problems beyond human capability.
            </p>
            <p style="color: {OFF_WHITE}; font-size: 23px; margin-top: 24px; line-height: 1.7;">
                This is the first step towards accessible human-led superintelligence, where AI systems create their own workflows and applications.
            </p>
        </div>
        <div style="display: flex; align-items: center; justify-content: center;">
            <div style="width: 400px; height: 400px; border-radius: 50%; border: 3px solid {GOLD}30; display: flex; align-items: center; justify-content: center; position: relative;">
                <div style="width: 300px; height: 300px; border-radius: 50%; border: 3px solid {BLUE}30; display: flex; align-items: center; justify-content: center;">
                    <div style="width: 200px; height: 200px; border-radius: 50%; border: 3px solid {GOLD}; display: flex; align-items: center; justify-content: center;">
                        <svg width="80" height="80" viewBox="0 0 100 100">
                            <polygon points="45,10 55,35 80,40 60,55 65,80 45,65 25,80 30,55 10,40 35,35" fill="{GOLD}"/>
                        </svg>
                    </div>
                </div>
                <div style="position: absolute; top: 10px; right: 40px; width: 16px; height: 16px; background: {GOLD}; border-radius: 50%;"></div>
                <div style="position: absolute; bottom: 50px; left: 20px; width: 12px; height: 12px; background: {BLUE}; border-radius: 50%;"></div>
                <div style="position: absolute; bottom: 20px; right: 80px; width: 10px; height: 10px; background: {GOLD}60; border-radius: 50%;"></div>
            </div>
        </div>
    </div>
    <div class="accent-bar"></div>
</div>
""")

# ─── SLIDE 13: CTA / CLOSING ───
slides.append(f"""
<div class="slide" style="background: {WHITE}; justify-content: center; align-items: center; text-align: center;">
    <div style="margin-bottom: 40px;">
        <svg width="100" height="100" viewBox="0 0 100 100">
            <rect x="10" y="10" width="70" height="65" rx="18" fill="none" stroke="{GOLD}" stroke-width="5"/>
            <polygon points="45,25 50,40 65,45 50,50 45,65 40,50 25,45 40,40" fill="{GOLD}"/>
            <path d="M30 75 L20 90" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
        </svg>
    </div>
    <h1 style="font-size: 60px; max-width: 1100px;">Stop Wrestling with AI.<br><span class="gold">Start Commanding It.</span></h1>
    <p style="font-size: 26px; margin-top: 30px; max-width: 800px; color: {DARK_NAVY};">
        Visit our booth for a live demo. See how promptanything.io turns your ideas into precision AI output in seconds.
    </p>
    <div style="margin-top: 50px; display: flex; gap: 30px; align-items: center;">
        <div style="background: {GOLD}; color: {DEEP_NAVY}; padding: 22px 60px; border-radius: 10px; font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 28px;">promptanything.io</div>
    </div>
    <div style="margin-top: 40px; display: flex; gap: 40px; align-items: center;">
        <p style="font-size: 20px; color: {DARK_NAVY};">Richmond Taylor, Founder & CEO</p>
    </div>
    <div class="accent-bar"></div>
</div>
""")


async def render_pdf():
    slide_pdfs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for i, slide_html in enumerate(slides):
            full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head>
<body>{slide_html}</body></html>"""
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})
            await page.set_content(full_html, wait_until="networkidle")
            await page.wait_for_timeout(800)
            tmp = os.path.join(OUTPUT_DIR, f"_slide_{i}.pdf")
            await page.pdf(
                path=tmp,
                width="1920px",
                height="1080px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            slide_pdfs.append(tmp)
            await page.close()
            print(f"  Rendered slide {i+1}/{len(slides)}")
        await browser.close()

    writer = PdfWriter()
    for pdf_path in slide_pdfs:
        reader = PdfReader(pdf_path)
        for pg in reader.pages:
            writer.add_page(pg)
    with open(FINAL_PDF, "wb") as f:
        writer.write(f)
    for pdf_path in slide_pdfs:
        os.remove(pdf_path)
    print(f"\nDone! -> {FINAL_PDF}")

asyncio.run(render_pdf())
