# BOB Startup Lead Engine — Design

**Date:** 2026-08-26
**Owner:** Richmond Taylor
**Status:** Approved design, pending spec review
**Location:** `~/.claude/bob-startup-leads/`

## 1. Purpose

Produce roughly 1,000 US small businesses that are plausibly past $500K in
revenue, scored 0-100, with contact data good enough to run outbound for BOB
(joinbob.ai). Delivered as one Google Sheet. One-off build, not a recurring
service.

This is a vertical-agnostic list. It deliberately does not restrict to BOB's
six-vertical launch cohort. Any US business past the revenue floor qualifies.

## 2. Constraints

| Constraint | Value |
|---|---|
| Target volume | ~1,000 companies on Master |
| Deep-enriched tier | top 20% by score, ~200 rows |
| Geography | US-wide |
| Apify budget | up to $10 without asking; cheap actors only |
| Paid APIs | Hunter and Apollo keys already present; stay inside existing quota |
| Delivery | one Google Sheet, four tabs |
| Out of scope | sending, Attio push, scheduled refresh |

Standing rules that apply: Apify is a last-resort layer and only cheap actors
(`code_crafter~leads-finder`, small `fetch_count`). Python runs through `uv`
with PEP 723 headers, never bare pip or venv. Phone numbers are list-only;
any SMS or voice use stays gated behind consent elsewhere in the stack.

## 3. The central problem

No free source publishes SMB revenue. The entire design is a proxy stack. The
list is only as good as the proxies, so proxies are layered rather than
trusted individually, and every company is scored on how many independent
proxies agree.

## 4. Architecture

Three seed lanes converge into one company table, which then passes through a
single scoring pass, a single cost-ordered enrichment waterfall, a QA gate, and
an upload.

```
Lane 1 (intent)    job posts ─┐
Lane 2a (footprint) maps ─────┼─→ dedupe ─→ site scrape ─→ signals ─→ score
Lane 2b (financial) SBA data ─┘                                        │
                                                                       ▼
        upload ←─ QA gate ←─ hooks (Tier 1) ←─ enrichment waterfall ←─ tier
```

Each stage reads and writes JSONL in `data/`, so any stage can be rerun in
isolation without repeating the ones before it. This mirrors the working
structure of `bob-miami-150/`.

## 5. Stages

| File | Input | Output | Job |
|---|---|---|---|
| `config.py` | — | — | metros, category basket, job-title basket, score weights, thresholds |
| `seed_jobs.py` | config | `seed_jobs.jsonl` | Lane 1: finance and admin job posts |
| `seed_maps.py` | config | `seed_maps.jsonl` | Lane 2a: Google Maps sweep |
| `seed_sba.py` | config | `seed_sba.jsonl` | Lane 2b: SBA and PPP bulk data |
| `dedupe.py` | all seeds | `companies.jsonl` | normalize and merge to one record per company |
| `site_scrape.py` | companies | `sites.jsonl` | contact data, JSON-LD, tech fingerprint |
| `signals.py` | companies, sites | `signals.jsonl` | headcount, reviews, registry age, press |
| `score.py` | signals | `scored.jsonl` | 0-100, floor, rank, tier assignment |
| `enrich_tier1.py` | scored | `enriched.jsonl` | waterfall to named contact and verified email |
| `hooks.py` | enriched | `hooks.jsonl` | one-line outreach angle per Tier 1 row |
| `qa.py` | enriched, hooks | `qa_report.json` | gates and hand-review sample |
| `upload_sheet.py` | all | Google Sheet | four tabs |

## 6. Seed lanes

### Lane 1 — intent (highest precision)

Companies actively hiring a finance or admin role. A business paying for a
bookkeeper is almost certainly past $500K, and BOB's own GTM material names
the bookkeeper job posting as the single best outbound trigger. The post
doubles as a free, specific outreach hook.

Title basket: bookkeeper, staff accountant, controller, accounts payable,
accounts receivable, office manager, billing specialist, business manager.

Sources, in order of preference:
1. Brave Search dorks against public ATS boards. `site:boards.greenhouse.io`,
   `site:jobs.lever.co`, `site:apply.workable.com`, `site:jobs.ashbyhq.com`
   crossed with the title basket. These pages are static, unauthenticated and
   name the employer directly.
2. Indeed via Playwright, headful profile, paced. Employer name, city, post age.
3. LinkedIn Jobs via Playwright using the saved session in `LINKEDIN_COOKIES_FILE`.

Every Lane 1 company enters with a signal flag that floors it into Tier 1
consideration regardless of what the other lanes say.

### Lane 2a — footprint (breadth)

Google Maps sweep, headless Playwright, aria-label parse. This is the approach
that produced 2,669 clean records in `bob-miami-150/maps_scrape.py` and it is
reused with the query basket widened.

Grid: roughly 25 metros crossed with a broad SMB category basket. Because the
list is vertical-agnostic the basket is built for money-moving B2B and B2C
services rather than a named vertical set. Maps yields business name, address,
phone, website, rating and review count at no cost.

Review count and years-live serve as the footprint proxy. They are weak alone,
which is why they carry low weight in the score.

### Lane 2b — financial proof (strongest free proxy)

SBA publishes loan-level bulk data under FOIA, and PPP loan data is public on
`data.sba.gov`. These files name real businesses with address, NAICS code,
reported jobs and loan amount, nationwide.

- SBA 7(a) and 504 FOIA datasets: borrower name, street, city, state, NAICS,
  gross approval amount, jobs supported, approval fiscal year.
- PPP loan data: borrower name and address, NAICS, jobs reported, approval
  amount.

Filter on jobs reported and loan size to isolate businesses plausibly past the
revenue floor, then take the most recent vintages first.

**Verify at build time:** exact current field names, file URLs and vintages
before writing the parser. Treat the field lists above as expected shape, not
as confirmed schema. PPP records are 2020-2021 vintage, so a liveness check
against Maps or the company website is mandatory before any PPP-sourced row
reaches the Master tab.

## 7. Dedupe and identity

Records merge on, in order: normalized registrable domain, then normalized
phone (E.164, last 10 digits), then fuzzy business name plus state.

Name normalization strips legal suffixes (LLC, Inc, Corp, Co, Ltd, PLLC, PA)
and punctuation before comparison. A company keeps the union of fields across
lanes and a `sources` array recording which lanes contributed, since multi-lane
agreement is itself a scoring signal.

## 8. Scoring

Weighted to 0-100 across four families. Weights are the starting point and get
tuned once the first full pass is scored and the distribution is visible.

**Money proof (40)**
- SBA or PPP loan amount and jobs reported
- Payment and finance tech fingerprint found by regex against page source:
  Stripe, Shopify, Square, QuickBooks, Bill.com, Gusto, ADP, Recurly
- Real pricing page or online ordering or booking flow

**Operating scale (25)**
- LinkedIn company page headcount
- Multiple locations
- Maps review count and years live
- Named team or leadership page

**Buying signal (25)**
- Open finance or admin requisition (Lane 1 hit)
- Hiring velocity, more than one open role
- Press, funding or acquisition mentions found via Brave
- Marketplace proof: G2, Capterra, BBB accreditation, Shopify app installs

**Reachability (10)**
- Contact completeness and quality: named person beats role address beats
  generic inbox; direct line beats main line

A hard floor excludes anything that clears too few independent families, so a
company cannot enter on review count alone. Ranked descending; the top 20%
becomes Tier 1.

## 9. Enrichment waterfall

Cost-ordered. Each row exits the waterfall the moment it satisfies its tier's
requirement, so paid steps only ever run on rows the free steps failed.

| Step | Source | Cost | Yields |
|---|---|---|---|
| 1 | Site scrape: mailto links, contact and about and team pages, footer, JSON-LD `Organization` | free | email, phone, address, sometimes officer name |
| 2 | Google Maps record | free | phone, address, hours |
| 3 | State registry officer lookup | free | authoritative officer name |
| 4 | LinkedIn company page, saved session | free | headcount, decision-maker name and title |
| 5 | Hunter: domain search and email verification | key on hand | email pattern, verification status |
| 6 | Apollo: people search by domain and title | key on hand | titled contact, work email |
| 7 | Apify `code_crafter~leads-finder`, small `fetch_count` | under $10 total | gap fill only |

Registry note: Florida Sunbiz officer lookup already works via headful Chrome
through Playwright, with the Cloudflare clearance cookie persisting per
context, and is the reference implementation. Other states differ in
availability and gating; treat non-Florida registry lookup as best-effort per
state and fall through to step 4 when a state is closed or hostile.

Quota note: check remaining Hunter and Apollo credits before the Tier 1 pass
and size the batch to fit. Do not assume either plan is unlimited.

## 10. Hooks (Tier 1 only)

One line per Tier 1 row, written from that company's own material: the open
requisition, a recent press hit, a site detail. Lane 1 rows get the requisition
angle by default, which maps directly to BOB's "cancel the req" framing.

Copy rules apply: no AI-tell vocabulary, no mirrored two-beat constructions, no
em dashes, no invented acronyms. Voice is laconic and plain. Hooks pass
`caption_lint.py` at exit 0 before they reach the Sheet.

## 11. QA gates

The upload is blocked unless all of these pass.

1. **Contactability.** Every Master row has an email or a phone. Rows failing
   this move to Rejects with a reason.
2. **Name validation.** Officer and contact names strict-validate against a
   person-name pattern and a stopword list. The Miami build's regex extraction
   produced plausible-looking junk such as "Get Ah" and "Fort Lauderdale", so
   anything that fails validation is discarded rather than shipped uncertain.
3. **Email labelling.** Every email is marked verified, guessed or generic.
   Guessed emails are never presented as verified.
4. **Liveness.** Any PPP-sourced or SBA-sourced row is confirmed still trading
   against Maps or a live website before reaching Master.
5. **Hand sample.** 25 random rows are reviewed by eye and shown to Rich before
   the Sheet is created.

## 12. Output

One Google Sheet, created through the existing Sheets OAuth credential, in the
same Drive folder as the previous target lists.

- **Master** — about 1,000 rows, scored and ranked. Columns: company, domain,
  city, state, phone, email, email status, category, score, tier, signals
  summary, sources, first seen.
- **Tier 1 Deep** — about 200 rows. Master columns plus contact name, contact
  title, contact email, contact email status, hook.
- **Method and Sources** — what ran, when, which sources produced what, Apify
  spend, quota consumed. So the list can be defended and rerun.
- **Rejects** — everything filtered out, with the reason. Rejects are kept
  because they are the spare pool if Master needs topping up later.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| SBA and PPP data is stale, business no longer trading | mandatory liveness check before Master |
| $500K revenue floor is a proxy, not a fact | multi-family scoring floor; the Sheet labels the score as a proxy, never as revenue |
| LinkedIn session expires or rate-limits mid-run | pace requests, checkpoint to JSONL, resume; fall through to Hunter and Apollo |
| Hunter or Apollo quota runs out mid-pass | check remaining credits first, size batch to fit, degrade to company-level contact |
| Apify silently overspends | cost stated before each run, `fetch_count` capped, hard stop at $10 |
| Vertical-agnostic list produces weak hooks | Lane 1 rows carry a specific requisition hook; hook quality is part of the hand sample |
| Junk names shipped as real contacts | strict validation, discard on failure, never ship uncertain |

## 14. Open items to resolve during implementation

1. Confirm current SBA and PPP file URLs, schemas and vintages before writing
   `seed_sba.py`.
2. Confirm remaining Hunter and Apollo credit balances before sizing the
   Tier 1 pass.
3. Choose the final metro list and category basket in `config.py`, then
   sanity-check expected yield against the 1,000 target before running the
   full sweep.
4. Tune score weights after the first scored pass, once the distribution is
   visible.
