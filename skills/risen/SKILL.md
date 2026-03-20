---
name: risen
description: "Guides you through designing, building, and deploying the RISEN Framework — an autonomous inbound sales agent that monitors website traffic in real-time and initiates phone calls to qualified decision-makers. Use this skill whenever the user wants to: set up an AI sales agent, configure automated calling from web traffic, build a visitor-to-call pipeline, implement the RISEN framework, integrate RB2B with a telephony platform (Vapi, Bland.ai, Twilio), connect Apify for lead enrichment, automate Calendly booking from calls, log outcomes to Google Sheets, send Slack alerts on bookings, or create HubSpot follow-up tasks. Also trigger when the user says things like 'I want to call visitors on my site', 'set up speed-to-lead calling', 'automate outbound calls from website traffic', 'build a sales agent that calls leads', 'hook up RB2B to phone calls', 'AI SDR', 'autonomous sales development rep', 'inbound calling automation', or 'website visitor calling workflow' — even if they don't use the words RISEN or skill."
---

# RISEN Framework — Autonomous Inbound Sales Agent

You are helping the user design and implement a real-time website-to-call pipeline. A visitor lands on a high-intent page → the system identifies them → enriches their contact info → calls them within minutes. Your job is to help them configure, build, and deploy this system end-to-end.

## What RISEN stands for

| Letter | Layer |
|--------|-------|
| **R** | Runtime — Agent behavior, triggers, constraints |
| **I** | Integration — The tool stack that powers it |
| **S** | Sequence — The 25-step operating procedure |
| **E** | Error-handling — Failure modes and fallbacks |
| **N** | Notification — Logging, alerts, follow-up tasks |

---

## Start here: Clarify the user's setup

Before jumping into architecture, ask the user to confirm:

1. **What platform is their site on?** (Webflow, WordPress, custom — affects RB2B installation)
2. **Which telephony platform?** Vapi (best for voice AI), Bland.ai (simpler), or Twilio (most flexible/DIY)
3. **Do they have RB2B or a similar de-anonymization tool?** If not, help them sign up — this is the entry point.
4. **What's their CRM?** (This implementation defaults to Google Sheets; HubSpot for tasks)
5. **What does their company do?** The opening line and value prop must be customized — the placeholder in the script is not enough.
6. **What are their target industries?** Needed to filter visitor companies.
7. **Do they have a Calendly link?** The booking flow depends on this.

If the user already has answers, skip straight to the relevant section.

---

## R — Runtime: Agent Behavior

The agent operates continuously with event-driven triggers. It only dials during business hours (9am–6pm) in the **prospect's local timezone**, not the user's. Outside those hours, leads queue for next-day processing.

### Trigger conditions (all must be true to proceed)
- Visitor company has 50+ employees
- Visitor viewed a high-intent page (pricing, demo request, case studies) OR spent 2+ minutes on site
- Company is in a target industry (user defines this list)
- Visitor is identifiable as director-level or above (Director, VP, C-suite)
- Company is US or Canada based

### Hard constraints
- Maximum 2 call attempts per lead, spread over 3 days
- If multiple visitors from the same company, call only the most senior person
- Never call unverified contacts or generic company numbers
- TCPA and Canadian CASL compliance always — this means:
  - No calls to numbers on the National DNC Registry
  - Identify as a business call, not a personal one
  - Honor opt-outs immediately and permanently
- Check suppression list before every call attempt

---

## I — Integration: The Tool Stack

| # | Service | Role | Notes |
|---|---------|------|-------|
| 1 | **RB2B** (or Clearbit/Demandbase) | De-anonymizes site visitors, identifies company | Installs as a JS snippet; fires webhook on qualified visit |
| 2 | **Apify + Apollo scraper** | Enriches company name → decision-maker name, title, direct phone, LinkedIn | Requires high-confidence match + verified phone before proceeding |
| 3 | **Vapi / Bland.ai / Twilio** | Places the call, handles conversation, captures recording + transcript | Vapi recommended for voice AI; Twilio for full custom control |
| 4 | **Calendly** | Offers time slots, sends calendar invites | Sync to Google Calendar; use Calendly API to fetch available slots |
| 5 | **Google Sheets** | CRM — logs every call attempt and outcome | Use Google Sheets API or Zapier/Make to write rows |
| 6 | **Slack webhook** | Instant alert when meeting books | Also used for DNC alerts and daily summary |
| 7 | **HubSpot** | Creates follow-up tasks for warm leads | Use HubSpot Tasks API |

### Integration architecture options

**Option A: n8n or Make (recommended for most users)**
- n8n workflow triggered by RB2B webhook
- Each integration is a node; Claude API handles conversation logic
- Easier to debug and modify; no code deployment needed

**Option B: Claude Skill + MCP integrations**
- Event-driven skill with MCP connections to each service
- Better for users comfortable with Claude Code and MCP servers
- See the mcp-skill for how to build MCP servers if needed

**Option C: Custom Node.js/Python app**
- Full control; best for high call volume or complex routing
- Requires hosting (Railway, Fly.io, etc.)

---

## S — Sequence: The 25-Step Operating Procedure

```
1.  RB2B webhook fires → extract company name, employee count, industry, page visited
2.  Validate: 50+ employees AND target industry AND high-intent page/2min dwell
3.  If validation fails → stop (do not queue; this company doesn't meet criteria)
4.  Query Apify Apollo scraper with company name → fetch decision-maker candidates
5.  Filter to director-level or above; require verified direct phone number
6.  If no verified contact found → add to manual research queue → stop
7.  If multiple contacts, select most senior by title hierarchy (C-suite > VP > Director)
8.  Pull LinkedIn URL and recent company news for call personalization
9.  Detect prospect's timezone from company HQ location
10. Check current time in prospect's timezone — is it 9am–6pm, Mon–Fri?
11. If outside hours → queue lead with timestamp for next business day → stop
12. Check suppression list AND deduplicate against call attempts in last 3 days
13. If on suppression list or 2+ attempts already made → stop
14. Initiate call via telephony platform
15. OPENING: "Hi [Name], this is [Your Name] — I noticed your company was exploring
    solutions like ours and wanted to see if it's worth a quick conversation."
16. VALUE PROP (10 seconds): [USER MUST CUSTOMIZE — what specific pain does your
    product solve, and for whom? Do not leave this generic.]
17. LIGHT QUALIFICATION: Confirm they're evaluating solutions; confirm authority.
    Do not interrogate — one or two questions max.
18. OBJECTION HANDLING — see references/objections.md for full rebuttal scripts
19. If qualified and interested → offer 2-3 Calendly slots
20. Book meeting → send calendar invite immediately
21. If voicemail → leave short message + send follow-up email within 5 minutes:
    "Hi [Name], noticed your team was on our site earlier — wanted to connect quickly.
    I'll follow up via email."
22. If prospect requests email only → send templated email within 5 minutes →
    log as "email requested"
23. If call drops mid-conversation → wait 2 minutes → call back once:
    "Sorry, we got disconnected."
24. If DNC request → confirm removal, add to suppression list, log, alert compliance
25. Log full outcome to Google Sheets (see N — Notification for fields)
```

---

## E — Error-Handling: Failure Modes and Fallbacks

| Scenario | Action |
|----------|--------|
| Low-confidence Apify match | Do not call. Queue for manual research with reason. |
| No verified direct phone | Do not call. Queue for manual research. |
| Telephony platform down | Log error, retry once after 15 min, then queue for manual outreach. |
| Calendly API unavailable during booking | Capture preferred time manually, create HubSpot task for human to send invite. |
| Google Sheets write failure | Buffer locally, retry every 5 minutes until successful. |
| Timezone detection failure | Default to Eastern Time, flag for human review. |
| No employee count from RB2B | Proceed only if other signals suggest enterprise size (domain, news, known brand). |
| Multiple decision-makers at same company | Select most senior. Never call multiple people from same company simultaneously. |
| Call drops mid-conversation | Wait 2 min, call back once. |
| Cannot determine qualification level | Default to booking meeting rather than disqualifying. |
| Invalid phone number format | Validate before dialing. Skip and log error if invalid. |
| Duplicate lead in queue | Deduplicate, process once. |
| Prospect asks "How did you get my number?" | "We noticed your team exploring our site and used standard business contact databases to reach the right person — happy to explain our approach." |
| Repeated API failures | Alert ops team via Slack. |
| Daily call limit reached | Pause queue, alert ops team. |

---

## N — Notification: Logging, Alerts, and Tasks

### Every call → Google Sheets row

| Field | Description |
|-------|-------------|
| Timestamp | ISO 8601 |
| Company name | From RB2B |
| Contact name | From Apify |
| Title | From Apify |
| Phone | Direct number used |
| Outcome | booked / not-interested / callback / voicemail / no-answer / DNC / email-requested |
| Recording URL | From telephony platform |
| Transcript summary | 2-3 sentence AI summary |
| Qualifying info | Notes from conversation |
| Next action | What happens next |

### Meeting booked
- Instant Slack notification to sales channel: prospect name, company, title, meeting time, link to call recording
- Email confirmation to sales team as backup

### Warm lead (interested but didn't book)
- HubSpot task assigned to rep, due within 2 hours
- Full call context included

### Manual research queue
- Task created: company name + reason (no verified contact, low confidence, etc.)

### DNC request
- Log immediately to suppression list
- Alert compliance Slack channel

### Daily summary report (send to Slack each morning)
- Total calls made
- Connection rate
- Meetings booked
- Leads queued
- Errors encountered
- Speed-to-lead average (time from site visit to call attempt; alert if consistently > 5 min)

---

## Implementation Walkthrough

### Step 1: Install RB2B

Add the RB2B tracking snippet to your site's `<head>`. In Webflow, use Project Settings → Custom Code. Configure the webhook to POST to your automation endpoint when a qualified visit occurs.

Webhook payload to expect:
```json
{
  "company_name": "Acme Corp",
  "employee_count": 250,
  "industry": "SaaS",
  "page_visited": "/pricing",
  "dwell_seconds": 180,
  "visitor_ip": "...",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### Step 2: Set up Apify Apollo scraper

Use the `apify/apollo-io-scraper` actor. Query input:
```json
{
  "company_name": "Acme Corp",
  "titles": ["Director", "VP", "Chief", "Head of", "President", "CEO", "CTO", "CMO"],
  "require_phone": true,
  "confidence_threshold": "high"
}
```

Filter results client-side to `direct_phone` or `mobile_phone` only — never call main line numbers.

### Step 3: Configure telephony

**Vapi setup (recommended):**
1. Create an assistant with your system prompt (value prop + objection scripts)
2. Set voice model (e.g., 11Labs ElevenLabs voice clone or stock voice)
3. Configure webhook for call events (answered, ended, transcript ready)
4. Use Vapi's `POST /call/phone` to initiate

**Call script system prompt for Vapi:**
```
You are [Name] from [Company]. You are making a friendly, professional outbound call to [Contact Name] at [Company Name].

Opening: "Hi [Contact Name], this is [Name] from [Company] — I noticed your company was exploring solutions like ours and wanted to see if it's worth a quick conversation."

Value proposition: [USER FILLS IN — be specific about the pain point you solve]

Your goal: Determine if they're evaluating solutions and book a 15-minute discovery call.

Keep it conversational. If they're interested, offer these time slots: [slots from Calendly].

See objection scripts below.
[paste from references/objections.md]
```

### Step 4: Connect Calendly

Use Calendly's API to fetch available slots in real-time during the call:
```
GET /event_type_available_times?event_type={uri}&start_time={now}&end_time={72h_from_now}
```

Present 2-3 options to the prospect. On booking confirmation, use `POST /scheduled_events` or direct the prospect to a Calendly link you pre-generate.

### Step 5: Wire up Google Sheets logging

Create a sheet with the column headers from the N — Notification section. Use Google Sheets API v4 (`spreadsheets.values.append`) to write a new row after each call.

If using n8n: use the Google Sheets node with "Append Row" operation.

### Step 6: Slack + HubSpot notifications

Create a Slack webhook URL and POST to it when meetings book. For HubSpot tasks, use `POST /crm/v3/objects/tasks` with the owner ID of the assigned rep.

---

## Reference files

- `references/objections.md` — Full objection rebuttal scripts for the 5 most common objections
- `references/compliance.md` — TCPA and CASL compliance checklist and suppression list management

Read these when configuring the telephony platform or when the user asks about specific call scenarios.
