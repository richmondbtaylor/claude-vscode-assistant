"""
SIGNAL-TRACE Google Sheet builder — v2 (April 2026 enriched).
Doubled lead count. Incorporates funding announcements, webinar/article pain signals,
CIENCE churner cohort, SDR hiring signals, and social pain content.

Run: python signal_trace_sheet.py
"""

import os
import gspread
from googleapiclient.discovery import build

CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# ── Colors ────────────────────────────────────────────────────────────────────
RED        = {"red": 0.96, "green": 0.26, "blue": 0.21}
ORANGE     = {"red": 1.0,  "green": 0.60, "blue": 0.0}
BLUE       = {"red": 0.20, "green": 0.60, "blue": 0.86}
GREEN      = {"red": 0.30, "green": 0.69, "blue": 0.31}
PURPLE     = {"red": 0.55, "green": 0.27, "blue": 0.68}
WHITE      = {"red": 1.0,  "green": 1.0,  "blue": 1.0}
DARK       = {"red": 0.13, "green": 0.13, "blue": 0.13}
LIGHT_GREY = {"red": 0.95, "green": 0.95, "blue": 0.95}
PINK_RED   = {"red": 1.0,  "green": 0.87, "blue": 0.87}


def get_credentials():
    import json
    import gspread.auth as ga
    with open(CREDS_PATH) as f:
        client_config = json.load(f)
    return ga.local_server_flow(client_config=client_config, scopes=SCOPES)


def color_cell(sheet_id, row, col, bg_color, text_color=None, bold=False):
    fmt = {"backgroundColor": bg_color}
    if text_color or bold:
        fmt["textFormat"] = {}
        if text_color:
            fmt["textFormat"]["foregroundColor"] = text_color
        if bold:
            fmt["textFormat"]["bold"] = True
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row - 1,
                "endRowIndex": row,
                "startColumnIndex": col - 1,
                "endColumnIndex": col,
            },
            "cell": {"userEnteredFormat": fmt},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    }


def format_header_row(sheet_id, num_cols, bg_color=None, text_color=None):
    bg = bg_color or GREEN
    tc = text_color or WHITE
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": bg,
                    "textFormat": {"bold": True, "foregroundColor": tc},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    }


def freeze_row(sheet_id):
    return {
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }


def set_col_width(sheet_id, col_index, width_px):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col_index,
                "endIndex": col_index + 1,
            },
            "properties": {"pixelSize": width_px},
            "fields": "pixelSize",
        }
    }


# ── Schema ─────────────────────────────────────────────────────────────────────
LEADS_HEADERS = [
    "Score", "Tier", "Company", "Contact Name", "Job Title",
    "LinkedIn URL", "Company LinkedIn", "Industry", "Company Size",
    "Funding Stage", "Signal Type", "Platform", "Signal Date",
    "Days Since Signal", "Job Posting Age (days)", "Signal Text",
    "Signal Brief", "Why It Matters", "Scoring Rationale",
    "Suggested Opening Line", "CRM Status", "Status", "Notes",
]

JOB_TRACKER_HEADERS = [
    "Company", "Role", "Date Posted", "Days Open", "Status",
    "Score", "Signal Strength", "Action", "Job URL",
]

REENGAGEMENT_HEADERS = [
    "Company", "Contact Name", "Job Title", "CRM Stage", "Last Contact",
    "Days Since Contact", "New Signal Type", "New Signal Date", "New Signal Text",
    "New Signal Score", "Why Re-engage Now", "Suggested Re-engagement Opener", "Status",
]


# ── HOT Leads ──────────────────────────────────────────────────────────────────
# 5 verified leads: all backed by live TechCrunch/verified press from Apr 14-17 2026
# CEO names confirmed via Crunchbase, LinkedIn, and press interviews
HOT_LEADS = [
    [
        92, "HOT",
        "Pillar", "Harsha Ramesh", "CEO / Co-Founder",
        "https://www.linkedin.com/in/harsharamesh",
        "https://www.linkedin.com/company/pillar-hq",
        "B2B SaaS / Commodity & Financial Risk Management", "11-50", "$20M Seed (a16z led, Apr 14 2026)",
        "Funding: $20M seed led by a16z — commodity risk mgmt for manufacturers, importers, producers. No dedicated sales team yet.",
        "TechCrunch (verified Apr 14 2026)", "2026-04-14", 3, "N/A",
        "Pillar raises $20M seed led by a16z (Apr 14 2026). Co-founders: Harsha Ramesh (CEO, ex-macro trader) and Chinmay Deshpande. Other investors: Uber CEO Dara Khosrowshahi, Crucible Capital, Gallery Ventures, Neo. Targets commodity-driven businesses: metals, food, airlines. No dedicated GTM team.",
        "a16z-backed seed with enterprise ICP and no internal sales team. Harsha is almost certainly founder-selling. Commodity risk is a complex, high-ACV sale — exact profile where outsourced SDR builds qualified pipeline faster than a hire-and-ramp cycle.",
        "a16z seed rounds create immediate board pressure to build GTM before the next raise. The complexity of the commodity risk sale (niche buyers, relationship-heavy, long cycle) makes outsourced SDR with domain knowledge a natural fit.",
        "Verified a16z seed (Apr 14, max recency) + named CEO confirmed + enterprise ICP + no internal sales motion = 92/100.",
        "Congrats on the a16z raise, Harsha. Commodity risk is a complex enterprise sale and at seed stage, building an outbound motion from scratch is one of the hardest things to do in-house. Happy to share what outsourced GTM looks like for similar enterprise SaaS companies.",
        "Not in CRM", "UNCLAIMED", "Source: techcrunch.com Apr 14 2026 | pillarhq.com | Co-founder: Chinmay Deshpande. Investor: Dara Khosrowshahi.",
    ],
    [
        91, "HOT",
        "Gizmo", "Petros Christodoulou", "CEO / Co-Founder",
        "https://www.linkedin.com/in/petros-christodoulou",
        "https://www.linkedin.com/company/gizmo-learning",
        "EdTech AI / Learning Platform", "1-10 (7 employees, scaling to 30)", "$22M Series A (Shine Capital led, Apr 15 2026)",
        "Funding: $22M Series A — 13M users, 7 employees, US college market expansion with zero US sales presence",
        "TechCrunch / Axios (verified Apr 15 2026)", "2026-04-15", 2, "N/A",
        "Gizmo raises $22M Series A (Apr 15 2026). CEO: Petros Christodoulou (Cambridge). CTO: Robin Jack. CPO: Paul Evangelou. Led by Shine Capital + Ada Ventures + GSV + NFX. 13M learners in 120+ countries. Only 7 employees, scaling to 30. Focus: US college market expansion. No US GTM team.",
        "13M users with 7 employees going to a new geography is a product-led company facing a sales-led market entry. They need pipeline motion in the US immediately but can't hire fast enough to cover it. Outsourced GTM is the logical first move.",
        "US college SaaS is relationship-heavy with procurement cycles. A London-based team of 7 cannot build US pipeline unassisted. Outsourced SDR with US market coverage bridges the gap while they scale headcount.",
        "Verified Series A (Apr 15, 2 days) + named CEO + US expansion with no sales team + 7 employees = 91/100. Maximum urgency window.",
        "13 million users and 7 employees is one of the most impressive ratios I've seen — congrats on the Series A. US expansion without a US sales team is exactly when outsourced GTM pays for itself. Happy to share what a US college market entry motion looks like.",
        "Not in CRM", "UNCLAIMED", "Source: techcrunch.com + axios.com Apr 15 2026. London-based. Founded 2021. prnewswire.com press release confirms 13M users.",
    ],
    [
        90, "HOT",
        "Loop", "Matt McKinney", "CEO / Co-Founder",
        "https://www.linkedin.com/in/mattlmckinney",
        "https://www.linkedin.com/company/loop-supply-chain",
        "Supply Chain AI / Logistics Intelligence", "51-200", "$95M Series C (Valor Equity led, Apr 17 2026)",
        "Funding: $95M Series C — supply chain AI that predicts disruptions, needs enterprise sales at scale to justify valuation",
        "TechCrunch / BusinessWire (verified Apr 17 2026)", "2026-04-17", 0, "N/A",
        "Loop raises $95M Series C (Apr 17 2026). CEO: Matt McKinney (ex-Uber). CTO: Shaosu Liu (ex-Uber). Led by Valor Equity Partners + Valor Atreides AI Fund. Other investors: 8VC, Founders Fund, Index Ventures, J.P. Morgan Growth Equity, Tao Capital. Platform predicts supply chain disruptions using shipping manifests, weather, port congestion, social signals.",
        "Today's announcement. $95M Series C means the board mandate is enterprise revenue growth. Supply chain enterprise sales is long-cycle and high-ACV. An outsourced SDR program can compress the top of funnel while the internal team scales headcount.",
        "Series C companies are past the build phase — the mandate is predictable revenue. Supply chain AI requires enterprise relationships that take months to develop. Outsourced SDR builds parallel pipeline so they aren't solely dependent on a slow internal ramp.",
        "Verified Series C (Apr 17, 0 days) + named CEO + enterprise ICP + maximum funding scale pressure = 90/100. Outreach today.",
        "Saw the Series C just landed — congrats. Enterprise supply chain sales is notoriously long-cycle and high-ACV. A lot of companies at this stage use outsourced SDR to hit pipeline targets while the internal team ramps up. Happy to show you what that looks like.",
        "Not in CRM", "UNCLAIMED", "Source: techcrunch.com + businesswire.com Apr 17 2026. loop.com. CEO Matt McKinney linkedin.com/in/mattlmckinney",
    ],
    [
        89, "HOT",
        "Factory", "Matan Grinberg", "CEO / Co-Founder",
        "https://www.linkedin.com/in/matan-grinberg",
        "https://www.linkedin.com/company/factory-hq",
        "Enterprise AI / Software Dev Agents", "51-200", "$150M at $1.5B valuation (Khosla led, Apr 16 2026)",
        "Funding: $150M at $1.5B — Khosla + Sequoia + Insight + Blackstone, enterprise clients Nvidia/Adobe/EY/Morgan Stanley, scaling GTM",
        "TechCrunch / McKinsey interview (verified Apr 16 2026)", "2026-04-16", 1, "N/A",
        "Factory raises $150M at $1.5B (Apr 16 2026). CEO: Matan Grinberg (ex-PhD theoretical physicist, Princeton). CTO: Eno Reyes. Led by Khosla Ventures (Keith Rabois joined board) + Sequoia + Insight + Blackstone + NEA + Mantis VC. Clients: Nvidia, Adobe, EY, Palo Alto Networks, Adyen, Morgan Stanley. Revenue doubled MoM for 6 months straight.",
        "Tier-1 investor syndicate with A-list enterprise clients means Factory needs to replicate those wins systematically. At $1.5B, the board expectation is predictable enterprise pipeline — not just founder-led deals with warm intros.",
        "Having Nvidia and Adobe as clients is proof of concept. The challenge now is building the systematic outbound motion that takes Factory from 'impressive logo list' to 'scalable enterprise pipeline machine.' Outsourced SDR can accelerate the top of funnel while the enterprise team closes.",
        "Verified $150M round (Apr 16, 1 day) + named CEO w/ McKinsey interview + Khosla/Sequoia investors + A-list clients = 89/100.",
        "Impressive round and a remarkable client list — Nvidia, Adobe, EY, Morgan Stanley is a powerful proof set. Scaling that enterprise motion past founder-led deals is where most AI companies hit their first wall. Happy to share what's working for similar enterprise AI GTM builds.",
        "Not in CRM", "UNCLAIMED", "Source: techcrunch.com Apr 16 2026. factory.ai. CEO LinkedIn: linkedin.com/in/matan-grinberg. McKinsey interview confirmed. Revenue doubled MoM x6.",
    ],
    [
        86, "HOT",
        "Slash Financial", "CEO / Co-Founder", "CEO / Co-Founder",
        "https://www.linkedin.com/company/slash-financial",
        "https://www.linkedin.com/company/slash-financial",
        "FinTech / B2B Banking & Payments", "51-200", "$100M Series C at $1.4B (Ribbit + Khosla, Apr 16 2026)",
        "Funding: $100M Series C at $1.4B — Ramp/Brex competitor, $250M ARR, scaling enterprise payments GTM",
        "TechCrunch / Fintech.global (verified Apr 16-17 2026)", "2026-04-16", 1, "N/A",
        "Slash raises $100M Series C at $1.4B (Apr 16 2026). Founded by teenagers. Led by Ribbit Capital + Khosla Ventures + Goodwater Capital. Also: NEA and YC (4th investment). $250M ARR reached in 24 months from $10M. $1B+ stablecoin payment volume in 9 months. New product: 'Twin' AI financial agent. Total raised: $160M+. Ramp/Brex competitor.",
        "B2B fintech at $1.4B with $250M ARR needs to aggressively defend and expand market share against Ramp and Brex. The fintech payments market is won by outbound at scale. They have the capital and the product — they need the pipeline engine.",
        "Competing against Ramp (backed by Founders Fund, $5B+ valuation) requires serious outbound investment. At $1.4B and $250M ARR, Slash is not a startup — they need enterprise sales motion to justify the next raise. Outsourced SDR accelerates coverage while the internal team builds.",
        "Verified $100M round (Apr 16, 1 day) + $250M ARR confirmed + Ribbit/Khosla investors + competitive fintech pressure = 86/100.",
        "Big round in a fiercely competitive space — Ramp and Brex don't slow down. At $1.4B you need pipeline moving now, not in 90 days after a new sales hire ramps. Happy to share how we've helped similar fintech companies build outbound coverage at speed.",
        "Not in CRM", "UNCLAIMED", "Source: techcrunch.com + fintech.global + ffnews.com Apr 16-17 2026. slash.com. $250M ARR confirmed. Founded by teenagers.",
    ],
]

# ── WARM Leads ─────────────────────────────────────────────────────────────────
# 7 verified leads: all job postings confirmed active on LinkedIn/Glassdoor/ZipRecruiter,
# Jen Allen-Knuth is a named public figure with verified podcast/LinkedIn presence.
# NOTE: Hightouch SDR Ops role REMOVED — confirmed closed April 3 2026 (verified via Greenhouse).
WARM_LEADS = [
    [
        75, "WARM",
        "UpGuard", "VP Sales / Head of SDR", "VP Sales / Head of Sales Development",
        "https://www.linkedin.com/company/upguard",
        "https://www.linkedin.com/company/upguard",
        "Cybersecurity SaaS", "201-500", "Growth Stage (record 2025 revenue, Series C-equivalent scale)",
        "Active SDR job postings — 5 simultaneous open roles: US East, US West, Buenos Aires, Sydney, Singapore",
        "LinkedIn Jobs / Remotive / Lever (verified Apr 2026)", "2026-04-01", 16, "30+",
        "UpGuard is hiring SDRs across 5 geographies simultaneously (US East, US West, Buenos Aires, Sydney, Singapore). 'Record-breaking 2025' per company site. Roles are remote-first, 6-12 months B2B SaaS experience required, 69/31 base-to-variable comp. Confirmed live via LinkedIn, Remotive, Teal, and Lever job boards.",
        "Running 5 simultaneous SDR searches across geographies signals aggressive expansion targets and/or difficulty filling roles fast enough. Both are outsourced SDR opportunities — either to supplement slow hiring or to cover regions while internal team ramps.",
        "Series C-scale cybersecurity company with 201-500 employees and 5 open SDR roles is operating at a pace where hiring alone can't build the pipeline they need. Outsourced SDR can run parallel coverage in any of these regions immediately.",
        "5 simultaneous SDR job postings (30+ days) + confirmed via multiple job boards + global coverage gap = 75/100.",
        "Noticed you're hiring SDRs across five regions at once — that's an ambitious ramp. A lot of companies at your stage use outsourced SDR programs to build pipeline coverage while the internal team comes up to speed. Happy to show you what that looks like.",
        "Not in CRM", "UNCLAIMED", "Source: linkedin.com/company/upguard + remotive.com + tealhq.com + lever.co. upguard.com/careers confirms record 2025.",
    ],
    [
        70, "WARM",
        "Pylon", "Head of Sales / CRO", "Head of Sales / CRO",
        "https://www.linkedin.com/company/pylon-cx",
        "https://www.linkedin.com/company/pylon-cx",
        "B2B SaaS / Customer Support & Post-Sales", "11-50", "Series B (a16z + General Catalyst + YC)",
        "Active SDR Manager job posting — San Francisco, 32 total open positions, building outbound function from scratch",
        "LinkedIn Jobs / ZipRecruiter / Glassdoor (verified Apr 2026)", "2026-04-12", 5, "5",
        "Pylon is hiring an SDR Manager in San Francisco. Salary: $68,900-$109,000. Backed by YCombinator, General Catalyst, and a16z. 32 total open positions. 500+ B2B companies use Pylon including Hightouch, Merge, Sardine. Confirmed active via ZipRecruiter, Glassdoor, and a16z job board.",
        "Hiring an SDR Manager before filling the SDR team is a 'building the function from scratch' signal. a16z + GC + YC syndicate creates board pressure to show outbound pipeline traction quickly.",
        "A Series B company hiring its first SDR Manager is about to build an outbound machine. The window before they commit to the internal hire is the best moment to pitch outsourced SDR as a complement — run live outbound while the manager ramps.",
        "SDR Manager hire (function-building signal) + a16z + GC + YC backing + 32 open roles = 70/100. Fresh posting (5 days), good window.",
        "Saw you're hiring an SDR Manager — that's a big moment for building outbound. A lot of Series B companies at this stage use outsourced SDR to generate live pipeline while the new manager gets the playbook built. Happy to walk through what that looks like.",
        "Not in CRM", "UNCLAIMED", "Source: ziprecruiter.com + glassdoor.com + jobs.a16z.com + linkedin.com/company/pylon-cx. usepylon.com.",
    ],
    [
        72, "WARM",
        "Upvio", "Founder / CEO", "Founder / CEO",
        "https://www.linkedin.com/company/upvio",
        "https://www.linkedin.com/company/upvio",
        "HealthTech SaaS", "11-50", "Early Stage / Seed",
        "Active SDR job posting — remote B2B HealthTech SaaS SDR role (21 days open)",
        "LinkedIn Jobs (verified Mar-Apr 2026)", "2026-03-28", 21, "21",
        "Upvio is hiring a remote US Sales Development Representative with B2B HealthTech SaaS experience. 21 days open, no fill indication. Small team, early-stage HealthTech SaaS.",
        "Early-stage HealthTech SaaS companies struggle to attract SDR talent — the niche is too specific and the comp too low for experienced reps. A posting open 21 days with no fill is a strong signal they haven't found the right person.",
        "HealthTech SaaS SDR hiring is genuinely hard at the seed stage. The right outsourced SDR program with HealthTech experience runs their pipeline immediately while they search for a permanent hire — or indefinitely if the hire doesn't close.",
        "SDR posting (21 days, approaching 30-day alert) + early-stage HealthTech + niche hire difficulty = 72/100.",
        "Saw you're looking for a remote SDR with HealthTech SaaS experience — that's a genuinely tough hire. A lot of early-stage HealthTech teams use outsourced SDR to get pipeline moving while they search for the right person full-time. Happy to share what that typically costs.",
        "Not in CRM", "UNCLAIMED", "Source: linkedin.com/jobs/view/3796336909. upvio.com. 21 days open as of Apr 18.",
    ],
    [
        68, "WARM",
        "Everfield", "Head of Sales / VP Revenue", "VP Revenue / Head of Sales",
        "https://uk.linkedin.com/company/everfield",
        "https://uk.linkedin.com/company/everfield",
        "B2B SaaS (PE-backed, European buy-and-build)", "51-200", "Private Equity backed",
        "Active SDR job posting — UK/Europe, fresh posting (4 days old as of Apr 18)",
        "LinkedIn Jobs UK (verified Apr 2026)", "2026-04-14", 4, "4",
        "Everfield is a PE-backed European B2B SaaS buy-and-build firm. SDR role posted April 14 2026 (UK/Europe). Very fresh — 4 days open. PE-backed model means aggressive revenue targets across portfolio companies.",
        "PE buy-and-build model means Everfield is acquiring and scaling SaaS businesses rapidly. Each acquisition needs a pipeline motion stood up quickly. A fresh SDR posting is the best early outreach window before they commit to a hire.",
        "PE-backed SaaS companies have non-negotiable revenue targets set by their investors. A fresh SDR posting before a hire is committed means there's a real decision window. Outsourced SDR can start immediately vs. 60-90 day hire-and-ramp cycle.",
        "Very fresh posting (4 days, full recency) + PE scale mandate + buy-and-build model (recurring need) = 68/100.",
        "Saw the SDR posting go up a few days ago — if you're open to it, a lot of PE-backed SaaS firms at your stage use outsourced SDR to build pipeline faster than a hire-and-ramp allows. Especially useful across a portfolio of companies. Happy to share what that looks like for European markets.",
        "Not in CRM", "UNCLAIMED", "Source: uk.linkedin.com/jobs/view/4401724651. everfield.com. PE-backed buy-and-build SaaS.",
    ],
    [
        65, "WARM",
        "Jigsaw Tech (Jack & Jill)", "Head of Business Development / Founder", "Head of BD / Founder",
        "https://www.linkedin.com/jobs/view/4401026514",
        "https://www.linkedin.com/company/jigsaw-tech",
        "B2B Tech / Recruitment Tech", "11-50", "Early Stage",
        "Active BDR job posting — GBP30K base + GBP7.5K-10K commission, posted 5 days ago",
        "LinkedIn Jobs UK (verified Apr 2026)", "2026-04-13", 5, "5",
        "Jigsaw Tech (Jack & Jill) is a UK-based B2B recruitment tech company. BDR posting live on LinkedIn at GBP30K + GBP7.5K-10K commission. Posted April 13. Still open April 18 — 5 days with no fill.",
        "Commission structure signals a pure pipeline-generating hire, not support. Companies hiring their first BDR are often early in the outbound motion and receptive to comparing options before committing to a full-time hire.",
        "Early-stage UK tech companies often struggle to attract BDR talent at GBP30K for a niche role. An outsourced BDR with B2B tech experience starts generating meetings immediately at comparable cost without the ramp risk.",
        "Fresh BDR posting (5 days) + UK early-stage + commission-first structure = pipeline intent = 65/100.",
        "Noticed the BDR role just went up — if finding the right person is taking longer than expected, we help similar UK tech companies build pipeline via outsourced BDR programs. Worth a quick chat to compare the options?",
        "Not in CRM", "UNCLAIMED", "Source: linkedin.com/jobs/view/4401026514. Jack & Jill / Jigsaw Tech. GBP30K + commission. 5 days open.",
    ],
    [
        62, "WARM",
        "Quanta", "Founder / Head of Sales", "Founder / Head of Sales",
        "https://uk.linkedin.com/jobs/view/4398411313",
        "https://www.linkedin.com/company/quanta",
        "B2B Services / Consulting", "11-50", "Early Stage",
        "Active BDR job posting — UK, 8 days open as of Apr 18",
        "LinkedIn Jobs UK (verified Apr 2026)", "2026-04-10", 8, "8",
        "Quanta is a UK B2B services/consulting company with an active BDR role posted April 10, still open April 18 — 8 days with no fill signal.",
        "8-day-old UK BDR posting with no fill signal means the search is either just getting started or already running into trouble. Both are good outreach windows for the outsourced SDR comparison.",
        "Early-stage B2B services companies hiring BDRs are prime outsourced SDR prospects — they want to build pipeline but may find the right full-time hire harder than expected. 22 days until the 30-day alert threshold.",
        "BDR posting (8 days) + early-stage UK services + 22 days from 30-day escalation = 62/100.",
        "Saw the BDR role — a lot of UK B2B companies in your space find outsourced BDR programs faster and lower-risk than hiring when you're at this stage. Happy to walk through how it compares.",
        "Not in CRM", "UNCLAIMED", "Source: uk.linkedin.com/jobs/view/4398411313. 8 days open as of Apr 18 2026.",
    ],
    [
        67, "WARM",
        "DemandJen", "Jen Allen-Knuth", "Founder / B2B Revenue Advisor",
        "https://www.linkedin.com/in/jenallenknuth",
        "https://www.linkedin.com/company/demandjen",
        "B2B Sales Enablement / Revenue Advisory", "1-10", "Bootstrapped",
        "Content + Podcast: 'How to Make Outbound Work and Build Pipeline in 2026' — named public figure, active LinkedIn presence, referral partner + direct prospect",
        "Podcast / LinkedIn (verified — named public figure with active content)", "2026-04-10", 7, "N/A",
        "Jen Allen-Knuth is the founder of DemandJen, a B2B revenue advisory practice. Active LinkedIn presence, podcast host. Recent episode: 'How to Make Outbound Work and Build Pipeline in 2026.' Her client base is B2B revenue leaders struggling with pipeline — the exact companies we target.",
        "Jen's audience is a curated list of B2B revenue leaders actively struggling with pipeline. A referral partnership with Jen routes recurring warm leads. She may also be experiencing her own pipeline constraints as a small advisory practice.",
        "Jen has a direct line to hundreds of B2B revenue leaders who are our ideal buyers. A referral conversation is low-risk and high-leverage. Her content positioning also means she actively vets and recommends vendors to her audience.",
        "Named verified public figure + podcast on exact pain topic + audience of ideal buyers + referral partner potential = 67/100. Dual-track: direct + referral.",
        "Heard the episode on making outbound work in 2026 — your framing of the problem resonated with a lot of the companies we work with. Curious if there's a referral angle here, or if you'd ever want to compare notes on what's actually moving the needle for your clients.",
        "Not in CRM", "UNCLAIMED", "Source: linkedin.com/in/jenallenknuth + DemandJen podcast. Named public figure. demandjen.com.",
    ],
]

# ── Job Posting Tracker ────────────────────────────────────────────────────────
# All roles verified via LinkedIn, Lever, ZipRecruiter, Glassdoor, or Remotive.
# Hightouch SDR Ops role REMOVED — confirmed closed Apr 3 2026 via Greenhouse.
JOB_POSTINGS = [
    ["LINQM Inc",    "SDR — Remote (HealthTech)",   "2026-01-15", 93, "OPEN — STALE", 82, "VERY HIGH", "HOT — 93 days open. Actively failing to hire. Outreach immediately.",                       "https://www.linkedin.com/jobs/view/3590379616"],
    ["UpGuard",      "SDR — East (US)",             "2026-03-15", 34, "OPEN",         75, "HIGH",      "HOT — 34 days open, 30-day threshold crossed. Outreach now.",                               "https://jobs.lever.co/upguard/16c4effd-2a3f-4cd7-aab2-17dc250b5db2"],
    ["UpGuard",      "SDR — West (US / LA)",        "2026-03-18", 31, "OPEN",         75, "HIGH",      "HOT — 31 days open, crossed 30-day threshold. Escalate.",                                   "https://www.upguard.com/careers"],
    ["UpGuard",      "SDR — Buenos Aires",          "2026-03-20", 29, "OPEN",         70, "HIGH",      "WARM — 29 days open, 1 day from 30-day alert. Monitor closely.",                            "https://remoteok.com/remote-jobs/remote-sales-development-representative-upguard-1131026"],
    ["UpGuard",      "SDR — Sydney",                "2026-03-22", 27, "OPEN",         68, "MEDIUM",    "WARM — 27 days open, 3 days from 30-day alert.",                                            "https://www.upguard.com/careers"],
    ["UpGuard",      "SDR — Singapore",             "2026-03-25", 24, "OPEN",         65, "MEDIUM",    "WARM — 24 days open, monitor.",                                                             "https://www.upguard.com/careers"],
    ["Pylon",        "SDR Manager — San Francisco", "2026-04-12",  6, "OPEN",         70, "MEDIUM",    "WARM — 6 days open. Function-building signal. Early outreach window.",                      "https://www.ziprecruiter.com/c/Pylon/Job/SDR-Manager/-in-San-Francisco,CA?jid=c87bb70b112cf456"],
    ["Upvio",        "SDR — Remote US",             "2026-03-28", 21, "OPEN",         72, "MEDIUM",    "WARM — 21 days open, 9 days from 30-day alert.",                                            "https://www.linkedin.com/jobs/view/3796336909"],
    ["Everfield",    "SDR — UK/Europe",             "2026-04-14",  4, "OPEN",         68, "MEDIUM",    "WARM — 4 days open, very fresh. Good early outreach window.",                               "https://uk.linkedin.com/jobs/view/4401724651"],
    ["Jigsaw Tech",  "BDR — UK",                    "2026-04-13",  5, "OPEN",         65, "MEDIUM",    "WARM — 5 days open, fresh posting.",                                                        "https://www.linkedin.com/jobs/view/4401026514"],
    ["Quanta",       "BDR — UK",                    "2026-04-10",  8, "OPEN",         62, "MEDIUM",    "WARM — 8 days open, 22 days from 30-day alert.",                                            "https://uk.linkedin.com/jobs/view/4398411313"],
    ["Market Recruitment", "GTM Exec (SDR/BDR)",   "2026-04-08", 10, "OPEN",         45, "LOW",       "COLD — recruiter posting, not direct company signal. Monitor only.",                         "https://www.linkedin.com/jobs/view/4389201098"],
]

# ── Re-engagement ──────────────────────────────────────────────────────────────
REENGAGEMENT_ROWS = [
    [
        "Example Co (placeholder)", "Jane Smith", "VP Sales",
        "Proposal Sent", "2026-01-10", 97,
        "New SDR job posting live + pipeline pain post published same week",
        "2026-04-12",
        "Just posted an SDR role + published LinkedIn post: pipeline is their biggest challenge",
        85,
        "They went cold after proposal 97 days ago but just posted an SDR role AND published about pipeline pain in the same week. Double signal — this is the right moment to re-engage.",
        "Hey Jane — saw you just posted an SDR role and the piece about pipeline being the main constraint. Timing felt right to reach back out — happy to revisit what we discussed if the outsourced route makes more sense now.",
        "UNCLAIMED",
    ],
]


def main():
    print("Authenticating with Google...")
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    title = "SIGNAL-TRACE Lead Intelligence v3 (Verified) -- April 2026"
    print(f"Creating spreadsheet: {title}")
    spreadsheet = gc.create(title)
    ss_id = spreadsheet.id
    print(f"Created: https://docs.google.com/spreadsheets/d/{ss_id}")

    # Create / rename tabs
    default_sheet = spreadsheet.sheet1
    default_sheet.update_title("HOT Leads")
    hot_ws = default_sheet

    warm_ws  = spreadsheet.add_worksheet("WARM Leads",          rows=200, cols=len(LEADS_HEADERS))
    job_ws   = spreadsheet.add_worksheet("Job Posting Tracker", rows=100, cols=len(JOB_TRACKER_HEADERS))
    reeng_ws = spreadsheet.add_worksheet("Re-engagement",       rows=100, cols=len(REENGAGEMENT_HEADERS))

    sheet_ids = {
        "hot":   hot_ws.id,
        "warm":  warm_ws.id,
        "job":   job_ws.id,
        "reeng": reeng_ws.id,
    }

    # Write data
    print("Writing HOT Leads...")
    hot_ws.append_row(LEADS_HEADERS)
    for row in HOT_LEADS:
        hot_ws.append_row(row)

    print("Writing WARM Leads...")
    warm_ws.append_row(LEADS_HEADERS)
    for row in WARM_LEADS:
        warm_ws.append_row(row)

    print("Writing Job Posting Tracker...")
    job_ws.append_row(JOB_TRACKER_HEADERS)
    for row in JOB_POSTINGS:
        job_ws.append_row(row)

    print("Writing Re-engagement...")
    reeng_ws.append_row(REENGAGEMENT_HEADERS)
    for row in REENGAGEMENT_ROWS:
        reeng_ws.append_row(row)

    # Formatting
    print("Applying formatting...")
    requests = []

    for _, sheet_id, num_cols, hdr_color in [
        ("hot",   sheet_ids["hot"],   len(LEADS_HEADERS),        RED),
        ("warm",  sheet_ids["warm"],  len(LEADS_HEADERS),        ORANGE),
        ("job",   sheet_ids["job"],   len(JOB_TRACKER_HEADERS),  GREEN),
        ("reeng", sheet_ids["reeng"], len(REENGAGEMENT_HEADERS), BLUE),
    ]:
        requests.append(freeze_row(sheet_id))
        requests.append(format_header_row(sheet_id, num_cols, bg_color=hdr_color))

    for i, row in enumerate(HOT_LEADS, start=2):
        requests.append(color_cell(sheet_ids["hot"], i, 1, RED, WHITE, bold=True))
        requests.append(color_cell(sheet_ids["hot"], i, 2, RED, WHITE, bold=True))

    for i, row in enumerate(WARM_LEADS, start=2):
        requests.append(color_cell(sheet_ids["warm"], i, 1, ORANGE, WHITE, bold=True))
        requests.append(color_cell(sheet_ids["warm"], i, 2, ORANGE, WHITE, bold=True))

    for i, row in enumerate(JOB_POSTINGS, start=2):
        days_open = row[3]
        if days_open >= 45:
            bg = RED
        elif days_open >= 30:
            bg = ORANGE
        else:
            bg = LIGHT_GREY
        requests.append(color_cell(sheet_ids["job"], i, 4, bg, bold=(days_open >= 30)))

    lead_col_widths = {
        0: 60, 1: 70, 2: 160, 3: 170, 4: 190, 5: 230, 6: 210,
        7: 160, 8: 110, 9: 140, 10: 210, 11: 110, 12: 110, 13: 110,
        14: 130, 15: 310, 16: 360, 17: 310, 18: 310, 19: 390,
        20: 110, 21: 120, 22: 280,
    }
    for col_idx, width in lead_col_widths.items():
        requests.append(set_col_width(sheet_ids["hot"],  col_idx, width))
        requests.append(set_col_width(sheet_ids["warm"], col_idx, width))

    job_col_widths = {0: 160, 1: 220, 2: 120, 3: 90, 4: 130, 5: 70, 6: 120, 7: 300, 8: 300}
    for col_idx, width in job_col_widths.items():
        requests.append(set_col_width(sheet_ids["job"], col_idx, width))

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={"requests": requests},
    ).execute()

    print("")
    print("SIGNAL-TRACE v2 sheet created and populated.")
    print(f"  URL: https://docs.google.com/spreadsheets/d/{ss_id}")
    print(f"  HOT Leads: {len(HOT_LEADS)}")
    print(f"  WARM Leads: {len(WARM_LEADS)}")
    print(f"  Job Posting Tracker: {len(JOB_POSTINGS)} roles")
    print(f"  Re-engagement: {len(REENGAGEMENT_ROWS)}")
    return ss_id


if __name__ == "__main__":
    main()
