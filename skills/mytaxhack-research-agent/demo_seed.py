"""
Demo seeder — writes 25 synthetic leads (5 per platform) to a new Google Sheet tab.
All leads have relevance_score >= 71. Run with:  python demo_seed.py
"""

import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

# Patch the worksheet name BEFORE importing notifier (which caches it at import time)
TAB_NAME = f"Demo - {datetime.now().strftime('%Y-%m-%d')}"
import config as _cfg
_cfg.SHEET_WORKSHEET_NAME = TAB_NAME

import notifier
import importlib
importlib.reload(notifier)  # pick up the patched worksheet name

from analyzer import RawPost, PostAnalysis

NOW = datetime.now(timezone.utc)

LEADS: list[tuple[RawPost, PostAnalysis]] = [

    # ── Reddit (5) ──────────────────────────────────────────────────────────
    (
        RawPost(id="demo_reddit_1", platform="reddit", url="https://reddit.com/r/smallbusiness/comments/demo1",
                author="jake_smb_owner", title="Need a CPA who actually understands SaaS — tired of generalists",
                body="We're doing $1.2M ARR and my CPA just does basic returns. Looking for someone who knows R&D credits and can do proactive planning.",
                subreddit="smallbusiness", published_at=NOW),
        PostAnalysis(relevance_score=92, intent_score=88, intent_type="help_seeking", urgency="high",
                     pain_points=["generalist CPA", "no proactive planning", "missing R&D credits"],
                     budget_signals=["$1.2M ARR"], suggested_reply="Happy to help — we specialize in exactly this for SaaS founders.",
                     should_contact=True, reasoning="Actively seeking CPA replacement, R&D credit eligible SaaS, clear budget signals."),
    ),
    (
        RawPost(id="demo_reddit_2", platform="reddit", url="https://reddit.com/r/Entrepreneur/comments/demo2",
                author="agency_cfo_sarah", title="S-corp election — worth it for a $600K/yr agency?",
                body="Profitable digital marketing agency, sole owner. CPA mentioned S-corp but couldn't explain the actual savings. Anyone done this analysis?",
                subreddit="Entrepreneur", published_at=NOW),
        PostAnalysis(relevance_score=85, intent_score=79, intent_type="help_seeking", urgency="medium",
                     pain_points=["uninformed CPA advice", "entity structure uncertainty"],
                     budget_signals=["$600K revenue"], suggested_reply="S-corp election at $600K ARR can save $10K-$18K/yr — worth modeling.",
                     should_contact=True, reasoning="Decision maker, ICP industry, revenue above threshold, CPA frustration signal."),
    ),
    (
        RawPost(id="demo_reddit_3", platform="reddit", url="https://reddit.com/r/AskAccountants/comments/demo3",
                author="ecomm_founder_mike", title="R&D tax credit for custom Shopify development — am I eligible?",
                body="We built proprietary inventory software for our ecommerce brand. 3 devs on payroll. Is this qualified R&D spend?",
                subreddit="AskAccountants", published_at=NOW),
        PostAnalysis(relevance_score=90, intent_score=85, intent_type="help_seeking", urgency="high",
                     pain_points=["R&D credit eligibility uncertainty", "custom software spend"],
                     budget_signals=["3 devs on payroll", "proprietary software build"],
                     suggested_reply="Yes — internal-use software can qualify. Happy to walk through QRE calculation.",
                     should_contact=True, reasoning="Direct R&D credit question, employees exist, ecommerce ICP."),
    ),
    (
        RawPost(id="demo_reddit_4", platform="reddit", url="https://reddit.com/r/agency/comments/demo4",
                author="ppc_agency_tom", title="Our tax bill jumped $80K this year — CPA says nothing we can do",
                body="Agency hit $2M revenue last year. CPA just said 'pay the taxes.' Feels like there should be more strategy here. Is that normal?",
                subreddit="agency", published_at=NOW),
        PostAnalysis(relevance_score=88, intent_score=82, intent_type="pain_expressing", urgency="high",
                     pain_points=["large unexpected tax bill", "passive CPA", "no tax strategy"],
                     budget_signals=["$2M revenue", "$80K tax surprise"],
                     suggested_reply="That's not normal at $2M — there's real strategy available. Let's talk.",
                     should_contact=True, reasoning="Strong pain signal, clear decision-maker frustration, ICP agency revenue."),
    ),
    (
        RawPost(id="demo_reddit_5", platform="reddit", url="https://reddit.com/r/consulting/comments/demo5",
                author="msp_owner_dan", title="Quarterly estimated taxes killing cash flow — any optimization strategies?",
                body="IT consulting firm, 8 employees, $900K revenue. Paying huge quarterlies. Is there a smarter structure to smooth this out?",
                subreddit="consulting", published_at=NOW),
        PostAnalysis(relevance_score=78, intent_score=72, intent_type="help_seeking", urgency="medium",
                     pain_points=["cash flow strain from quarterly taxes", "no tax smoothing strategy"],
                     budget_signals=["$900K revenue", "8 employees"],
                     suggested_reply="Yes — S-corp + retirement accounts can dramatically cut quarterly burden.",
                     should_contact=True, reasoning="Warm signal, IT consulting ICP, revenue + employee count qualify."),
    ),

    # ── LinkedIn (5) ────────────────────────────────────────────────────────
    (
        RawPost(id="demo_linkedin_1", platform="linkedin", url="https://linkedin.com/posts/demo-saas-ceo",
                author="Amanda Reyes", title="Amanda Reyes on LinkedIn: Anyone have a CPA recommendation for a bootstrapped SaaS?",
                body="We crossed $500K ARR this year. My accountant does personal returns — not the right fit anymore. Looking for a tech-focused CPA.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=87, intent_score=83, intent_type="help_seeking", urgency="high",
                     pain_points=["wrong-fit CPA", "business has outgrown accountant"],
                     budget_signals=["$500K ARR milestone"],
                     suggested_reply="Congrats on the milestone — this is exactly when the right CPA pays for itself.",
                     should_contact=True, reasoning="Active referral request, SaaS founder, crossed revenue threshold."),
    ),
    (
        RawPost(id="demo_linkedin_2", platform="linkedin", url="https://linkedin.com/posts/demo-agency-owner",
                author="Chris Patel", title="Chris Patel on LinkedIn: Just got hit with a $55K tax bill I wasn't expecting",
                body="Nobody told me I should have been making quarterly payments as an LLC. Painful lesson. Need a proactive accountant ASAP.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=84, intent_score=80, intent_type="pain_expressing", urgency="high",
                     pain_points=["surprise tax bill", "no quarterly guidance", "reactive accounting"],
                     budget_signals=["$55K tax liability signal"],
                     suggested_reply="This is solvable — and the right CPA prevents it from happening again.",
                     should_contact=True, reasoning="Strong pain, urgency, active search for proactive CPA."),
    ),
    (
        RawPost(id="demo_linkedin_3", platform="linkedin", url="https://linkedin.com/posts/demo-founder-ecomm",
                author="Lisa Huang", title="Lisa Huang on LinkedIn: Did you know software companies can claim R&D tax credits?",
                body="Just learned my SaaS qualifies for the R&D credit and we left $40K on the table last year. Sharing so others don't miss it.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=76, intent_score=70, intent_type="education_seeking", urgency="low",
                     pain_points=["missed R&D credits in prior year"],
                     budget_signals=["$40K missed credit — suggests $400K+ in QREs"],
                     suggested_reply="Still recoverable — amended returns go back 3 years. Worth a quick call.",
                     should_contact=True, reasoning="Evangelist post signals recent discovery, amendable years available."),
    ),
    (
        RawPost(id="demo_linkedin_4", platform="linkedin", url="https://linkedin.com/posts/demo-cfo-smb",
                author="Ryan Torres", title="Ryan Torres on LinkedIn: Looking for a CPA who specializes in real estate + business",
                body="We have a property management company and a separate consulting LLC. Need someone who can see the whole picture and do real planning.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=80, intent_score=75, intent_type="help_seeking", urgency="medium",
                     pain_points=["multi-entity complexity", "no integrated tax strategy"],
                     budget_signals=["multiple business entities", "real estate + consulting"],
                     suggested_reply="Multi-entity planning is one of our core specialties — happy to map it out.",
                     should_contact=True, reasoning="Active CPA search, multi-entity = complex engagement, decision maker."),
    ),
    (
        RawPost(id="demo_linkedin_5", platform="linkedin", url="https://linkedin.com/posts/demo-ecomm-brand",
                author="Marcus Webb", title="Marcus Webb on LinkedIn: Is my ecommerce brand spending too much in taxes?",
                body="$1.8M in revenue this year, paying ~28% effective tax rate. Other founders I know are paying less. Is there something I'm missing?",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=86, intent_score=81, intent_type="help_seeking", urgency="medium",
                     pain_points=["high effective tax rate", "feels overtaxed vs peers"],
                     budget_signals=["$1.8M revenue", "28% effective rate"],
                     suggested_reply="28% at $1.8M is likely 8-12 points too high — common with the wrong structure.",
                     should_contact=True, reasoning="Revenue benchmark, comparison pain, active curiosity = warm entry point."),
    ),

    # ── Quora (5) ───────────────────────────────────────────────────────────
    (
        RawPost(id="demo_quora_1", platform="quora", url="https://quora.com/Does-my-software-startup-qualify-for-R-D-tax-credits",
                author="Alex M.", title="Does my software startup qualify for R&D tax credits?",
                body="We have 5 engineers building an AI-powered analytics platform. Annual payroll ~$800K. Haven't claimed R&D credits before.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=91, intent_score=86, intent_type="help_seeking", urgency="high",
                     pain_points=["unclaimed R&D credits", "uncertainty about qualification"],
                     budget_signals=["$800K payroll = likely $150K-$200K credit"],
                     suggested_reply="Almost certainly yes — AI platform + $800K eng payroll is a strong R&D profile.",
                     should_contact=True, reasoning="Direct R&D question, tech startup, quantifiable payroll signal."),
    ),
    (
        RawPost(id="demo_quora_2", platform="quora", url="https://quora.com/What-should-I-look-for-in-a-CPA-for-my-small-business",
                author="Priya S.", title="What should I look for in a CPA for my small business?",
                body="Running a $400K/yr consulting practice. Current CPA is a generalist who mostly does my personal return. Ready to upgrade.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=79, intent_score=74, intent_type="help_seeking", urgency="medium",
                     pain_points=["generalist CPA", "reactive vs proactive accounting"],
                     budget_signals=["$400K consulting revenue"],
                     suggested_reply="Look for industry specialization + proactive planning, not just compliance work.",
                     should_contact=True, reasoning="Shopping for a CPA upgrade, consulting ICP, revenue signal present."),
    ),
    (
        RawPost(id="demo_quora_3", platform="quora", url="https://quora.com/How-can-an-agency-owner-reduce-their-tax-bill-legally",
                author="Brian K.", title="How can an agency owner reduce their tax bill legally?",
                body="Digital marketing agency, $750K revenue, sole owner S-corp. Paying way too much. CPA says max out 401K but that's about it.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=83, intent_score=78, intent_type="pain_expressing", urgency="medium",
                     pain_points=["limited tax advice", "feels overtaxed", "passive CPA"],
                     budget_signals=["$750K agency revenue"],
                     suggested_reply="S-corp + defined benefit plan + QBI stacking can cut that bill significantly.",
                     should_contact=True, reasoning="Agency ICP, S-corp already set, CPA frustration, active optimization intent."),
    ),
    (
        RawPost(id="demo_quora_4", platform="quora", url="https://quora.com/Should-I-switch-from-LLC-to-S-corp-at-300k-revenue",
                author="Nina W.", title="Should I switch from LLC to S-corp at $300K revenue?",
                body="Freelance UX designer, just crossed $300K. Read S-corps save on self-employment tax but my accountant hasn't brought it up.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=75, intent_score=71, intent_type="help_seeking", urgency="medium",
                     pain_points=["self-employment tax burden", "uninformed accountant"],
                     budget_signals=["$300K revenue crossover point"],
                     suggested_reply="At $300K yes, S-corp election typically saves $8K-$15K/yr — worth modeling.",
                     should_contact=True, reasoning="Threshold revenue, self-education on entity structure, CPA gap."),
    ),
    (
        RawPost(id="demo_quora_5", platform="quora", url="https://quora.com/What-are-the-best-tax-strategies-for-SaaS-founders",
                author="Kevin L.", title="What are the best tax strategies for SaaS founders?",
                body="Just raised a seed round and paying myself a salary for the first time. Want to set up tax strategy properly from day one.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=77, intent_score=73, intent_type="education_seeking", urgency="medium",
                     pain_points=["starting from scratch on tax strategy", "first salary as founder"],
                     budget_signals=["seed-funded startup", "salary + equity structure forming"],
                     suggested_reply="Perfect time to set this up right — founder comp + R&D credits + entity choice all matter early.",
                     should_contact=True, reasoning="SaaS founder, proactive mindset, early-stage = high LTV if onboarded now."),
    ),

    # ── Twitter / X (5) ─────────────────────────────────────────────────────
    (
        RawPost(id="demo_twitter_1", platform="twitter", url="https://x.com/smb_owner_val/status/demo1",
                author="Val on X", title="Val on X: Anyone know a CPA who actually gets ecommerce? DMs open",
                body="Been through 3 CPAs in 4 years. All charge the same, none understand inventory accounting or Amazon FBA. Ready to pay more for the right fit.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=86, intent_score=82, intent_type="help_seeking", urgency="high",
                     pain_points=["repeated bad CPA experiences", "industry-specific needs unmet"],
                     budget_signals=["willing to pay premium", "multi-year search signal"],
                     suggested_reply="We specialize in ecommerce — inventory costing, FBA reconciliation, tax strategy. DM us.",
                     should_contact=True, reasoning="Active solicitation, high frustration, ecommerce ICP, premium-willing."),
    ),
    (
        RawPost(id="demo_twitter_2", platform="twitter", url="https://x.com/founder_greg_k/status/demo2",
                author="Greg K on X", title="Greg K on X: Paid $90K in taxes last year on $1.1M revenue. That's wild right?",
                body="Friends with similar revenue paying half that. My CPA just says 'you had a good year.' I feel like I'm missing something big.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=89, intent_score=84, intent_type="pain_expressing", urgency="high",
                     pain_points=["8.2% effective rate vs peers", "passive CPA with no strategy"],
                     budget_signals=["$1.1M revenue", "$90K tax = large savings opportunity"],
                     suggested_reply="You are missing something — that rate with a good CPA should be 4-6%. Let's talk.",
                     should_contact=True, reasoning="Strong pain, comparison trigger, high revenue, active and public post."),
    ),
    (
        RawPost(id="demo_twitter_3", platform="twitter", url="https://x.com/saas_ceo_jess/status/demo3",
                author="Jess M on X", title="Jess M on X: Do SaaS companies actually qualify for R&D tax credits? Asking for me",
                body="We spend $600K/yr on engineering. Someone told me we could claim R&D credits. My CPA has never mentioned it. Is this real?",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=90, intent_score=87, intent_type="help_seeking", urgency="high",
                     pain_points=["missed R&D credits", "uninformed CPA"],
                     budget_signals=["$600K engineering spend = ~$60K-$120K credit"],
                     suggested_reply="Very real — $600K in eng spend likely generates $60K-$120K in credits. DM us.",
                     should_contact=True, reasoning="Direct R&D question, massive opportunity, SaaS CEO."),
    ),
    (
        RawPost(id="demo_twitter_4", platform="twitter", url="https://x.com/agency_owner_t/status/demo4",
                author="Tanya B on X", title="Tanya B on X: Starting to think my accountant has no idea what they're doing for my business",
                body="Just found out I could have set up a SEP-IRA two years ago and saved thousands. Why didn't they tell me?",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=76, intent_score=71, intent_type="pain_expressing", urgency="medium",
                     pain_points=["missed retirement account opportunity", "reactive CPA"],
                     budget_signals=["multi-year lost savings signal"],
                     suggested_reply="That's a real gap — proactive CPAs surface these before year-end. Happy to review.",
                     should_contact=True, reasoning="Frustration trigger, warming up to CPA switch, amendable opportunity."),
    ),
    (
        RawPost(id="demo_twitter_5", platform="twitter", url="https://x.com/ecomm_brand_jp/status/demo5",
                author="JP on X", title="JP on X: Hired a bookkeeper, need a CPA — recommendations for ecommerce $2M+?",
                body="Brand crossed $2M this year. Have a bookkeeper in place. Now need strategic CPA who can do tax planning not just filing.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=88, intent_score=85, intent_type="help_seeking", urgency="high",
                     pain_points=["needs strategic CPA tier", "books already clean = easy onboarding"],
                     budget_signals=["$2M+ ecommerce revenue"],
                     suggested_reply="Perfect stage to add a strategic CPA — books clean, revenue ready for real planning.",
                     should_contact=True, reasoning="Active request, $2M+ ICP threshold, clean books = fast onboarding."),
    ),

    # ── Facebook (5) ────────────────────────────────────────────────────────
    (
        RawPost(id="demo_facebook_1", platform="facebook", url="https://facebook.com/groups/smallbiz/posts/demo1",
                author="Donna R", title="Donna R in Small Business Owners Group: CPA recommendations for an S-corp LLC?",
                body="Running a $450K cleaning business with 12 employees. Current CPA does basic filing but I know we're leaving money on the table.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=82, intent_score=77, intent_type="help_seeking", urgency="medium",
                     pain_points=["basic compliance CPA", "unoptimized S-corp structure"],
                     budget_signals=["$450K revenue", "12 employees = payroll complexity"],
                     suggested_reply="Service business at $450K with employees — lots of opportunity here. Happy to talk.",
                     should_contact=True, reasoning="Group referral request, service ICP, S-corp signal, employees present."),
    ),
    (
        RawPost(id="demo_facebook_2", platform="facebook", url="https://facebook.com/groups/entrepreneurs/posts/demo2",
                author="Carlos M", title="Carlos M in Entrepreneurs Group: Got audited last year — looking for a better CPA",
                body="Small audit, nothing serious, but my accountant was useless during the process. $700K consulting firm. Want someone proactive.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=84, intent_score=79, intent_type="pain_expressing", urgency="high",
                     pain_points=["useless CPA during audit", "audit anxiety", "no proactive defense"],
                     budget_signals=["$700K consulting firm"],
                     suggested_reply="Audit support is a differentiator — a proactive CPA minimizes exposure before it happens.",
                     should_contact=True, reasoning="Audit trigger = high urgency, consulting ICP, active switch intent."),
    ),
    (
        RawPost(id="demo_facebook_3", platform="facebook", url="https://facebook.com/groups/saas-founders/posts/demo3",
                author="Rachel T", title="Rachel T in SaaS Founders Group: Tax credits for software companies — what am I missing?",
                body="Just read about R&D credits and state-level incentives. We have 4 developers full-time and custom-built our entire platform.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=88, intent_score=83, intent_type="education_seeking", urgency="medium",
                     pain_points=["unclaimed R&D credits", "state incentive unawareness"],
                     budget_signals=["4 FTE engineers", "custom platform = full QRE stack"],
                     suggested_reply="R&D credits + state incentives could be $80K+ combined. Worth a free credit assessment.",
                     should_contact=True, reasoning="Self-educating founder, strong QRE profile, SaaS ICP."),
    ),
    (
        RawPost(id="demo_facebook_4", platform="facebook", url="https://facebook.com/groups/agency-owners/posts/demo4",
                author="Sam L", title="Sam L in Agency Owners Group: Switching CPAs after 5 years — what questions should I ask?",
                body="Marketing agency, $1.3M revenue, finally fed up. CPA has never once suggested anything proactive. Just want good questions to vet the next one.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=85, intent_score=80, intent_type="help_seeking", urgency="high",
                     pain_points=["5 years of passive accounting", "never proactive", "mid-switch"],
                     budget_signals=["$1.3M agency revenue"],
                     suggested_reply="Great timing — here are 5 questions to ask. Also happy to have that conversation directly.",
                     should_contact=True, reasoning="Actively switching CPAs, high revenue, agency ICP, warm entry point."),
    ),
    (
        RawPost(id="demo_facebook_5", platform="facebook", url="https://facebook.com/groups/ecommerce-sellers/posts/demo5",
                author="Maya J", title="Maya J in Ecommerce Sellers Group: How much should I be paying a CPA at $800K Amazon revenue?",
                body="Been quoted everything from $2K to $18K/yr. No idea what's fair or what I should be getting for the money.",
                subreddit=None, published_at=NOW),
        PostAnalysis(relevance_score=73, intent_score=70, intent_type="education_seeking", urgency="low",
                     pain_points=["pricing confusion", "unsure what CPA services should include"],
                     budget_signals=["$800K Amazon revenue"],
                     suggested_reply="Range depends on complexity — $800K Amazon at full service should be $6K-$12K.",
                     should_contact=True, reasoning="Price shopping = actively evaluating CPAs, ecommerce ICP."),
    ),
]


def _reset_tab() -> None:
    """Delete all data rows (keep header) if the tab already exists."""
    import gspread
    gc = gspread.oauth(credentials_filename=os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json"))
    spreadsheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    try:
        ws = spreadsheet.worksheet(TAB_NAME)
        num_rows = ws.row_count
        if num_rows > 1:
            ws.delete_rows(2, num_rows)
        print(f"[demo] Cleared existing tab '{TAB_NAME}'")
    except gspread.WorksheetNotFound:
        pass  # Tab doesn't exist yet — notifier will create it


def main():
    _reset_tab()
    print(f"[demo] Writing {len(LEADS)} leads to tab: '{TAB_NAME}'")
    success = 0
    for i, (post, analysis) in enumerate(LEADS, 1):
        ok = notifier.log_to_sheets(post, analysis, cross_platform="")
        if ok:
            success += 1
            print(f"  [{i:02d}] OK  [{post.platform.upper():<9}] score={analysis.relevance_score}  {post.title[:65]}")
        else:
            print(f"  [{i:02d}] FAIL [{post.platform.upper():<9}] {post.title[:65]}")

    print(f"\n[demo] Done. {success}/{len(LEADS)} leads written to tab '{TAB_NAME}'.")


if __name__ == "__main__":
    main()
