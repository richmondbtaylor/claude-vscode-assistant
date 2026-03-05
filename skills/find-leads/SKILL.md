---
name: find-leads
description: "Finds, qualifies, and delivers a prioritized list of sales leads for Bishop AI. Use this skill whenever the user says 'find me leads', 'I need prospects', 'build me a pipeline', 'find potential clients', 'who should we be selling to', 'identify targets', 'pull a lead list', 'source leads for [ICP or vertical]', or anything about prospecting, outbound targeting, or building a contact list. Trigger even if the request is vague — if the user wants names, companies, or contacts to reach out to, this skill handles it."
---

# Find Leads

Identify, qualify, and deliver a prioritized lead list aligned to Bishop AI's ICP. Work through each phase in sequence. Ask for missing inputs before generating output.

---

## Why This Matters

Outbound only works when you're talking to the right people. This skill removes guesswork from prospecting — it builds a focused, qualified list of companies and contacts that match Bishop AI's ICP, with enough context for an SDR or AE to act on immediately.

---

## Phase 1 — Define the Hunt

Before searching, lock in targeting criteria. Ask the user:

> "To build the right list, I need a few targeting inputs:
> 1. **Vertical / Industry** — e.g., B2B SaaS, professional services, healthcare tech, logistics
> 2. **Company size** — employee count or revenue range (e.g., 50–500 employees, $5M–$50M ARR)
> 3. **Geography** — North America, specific states, remote-first only, etc.
> 4. **Buyer persona** — job titles to target (e.g., VP of Sales, Head of RevOps, CRO, Founder)
> 5. **Signal or trigger** — any buying signals to prioritize (e.g., recently funded, hiring SDRs, new leadership, expanding GTM team)
> 6. **Volume** — how many leads do you need? (default: 10–25)"

If the user has already provided any of these, pull from context and confirm — don't re-ask.

---

## Phase 2 — Build the ICP Profile

Using the inputs from Phase 1, construct a clear ICP statement before searching:

```
ICP Summary:
- Industry: [vertical]
- Size: [headcount / ARR range]
- Geo: [region]
- Persona: [title(s)]
- Signals: [trigger events]
- Fit rationale: [1-2 sentences on why this profile needs Bishop AI's services]
```

Display this to the user and confirm before proceeding. If something looks off, adjust.

---

## Phase 3 — Source Leads

Search for companies and contacts that match the confirmed ICP. Use available tools and sources in priority order:

### Source Priority

1. **Web search** — query for company lists, recent funding announcements, hiring signals, industry directories
2. **LinkedIn-style signals** — job postings for RevOps, SDR, or GTM roles indicate active pipeline investment
3. **News and press releases** — Series A/B/C funding rounds, executive hires, product launches, acquisitions
4. **Industry directories** — G2, Crunchbase, BuiltWith, ProductHunt, AngelList, relevant trade associations
5. **User-provided data** — if the user pastes a raw list, clean and qualify it against the ICP

### Search Queries to Run (adapt to ICP)

- `"[vertical] company" site:linkedin.com/company hiring "revenue operations"`
- `"[vertical] startup" raised Series [A/B] 2025 OR 2026`
- `"VP of Sales" OR "Head of RevOps" "[vertical]" hiring`
- `[vertical] companies "[city/region]" 50-500 employees`
- `"[vertical]" "go-to-market" OR "outbound sales" team site:crunchbase.com`

Run at minimum 3–5 searches. Cast wide, then qualify down.

---

## Phase 4 — Qualify and Score

For each company found, score it against the ICP using this rubric:

| Criterion | Strong Fit (2pts) | Partial Fit (1pt) | Weak/Unknown (0pts) |
|-----------|------------------|-------------------|---------------------|
| Industry match | Exact vertical | Adjacent vertical | Unrelated |
| Size match | Within range | Near range (±20%) | Outside range |
| Persona reachable | Title confirmed | Role likely exists | Unknown |
| Trigger signal | Clear signal found | Possible signal | No signal |
| Geography | Target region | Adjacent | Outside |

**Score interpretation:**
- 8–10: Priority — lead first
- 5–7: Qualified — include in list
- 0–4: Weak — exclude or flag

Only include leads scoring 5+ in the final output. If fewer than half the candidates qualify, broaden the search and note this to the user.

---

## Phase 5 — Build the Lead List

For each qualified lead, compile:

```
Company: [Name]
Website: [URL]
Industry: [vertical]
Size: [approx. headcount or ARR]
Location: [HQ city, state/country]
ICP Score: [X/10]
Signal: [what triggered inclusion — e.g., "raised $12M Series A Jan 2026", "posted 3 SDR roles"]
Target Contact: [Name if findable, or Title to target]
LinkedIn: [company or contact URL if available]
Outreach Angle: [1 sentence — why Bishop AI is relevant to this company right now]
```

---

## Phase 6 — Deliver Output

Present the final list in a clean table for easy scanning, followed by full detail cards for each lead.

### Summary Table

| # | Company | Industry | Size | Score | Signal |
|---|---------|----------|------|-------|--------|
| 1 | ... | ... | ... | 9/10 | Series B raised |
| 2 | ... | ... | ... | 7/10 | Hiring 4 SDRs |
| ... | | | | | |

### Full Lead Cards

Output one card per lead using the Phase 5 format. Order by ICP score, descending.

### Outreach Note

After the list, include a short paragraph (3–5 sentences) summarizing:
- The common thread across the leads (why this cohort makes sense)
- The strongest 2–3 triggers to lead with in outreach
- Recommended first-touch channel (e.g., LinkedIn DM, cold email, warm intro)

---

## Output Standards

- **No hallucinated data** — if a company name, contact, or detail cannot be verified through search, mark it `[Unverified — confirm before outreach]`
- **No filler** — every lead card must have a specific, usable outreach angle; never write "this company could benefit from AI"
- **Recency matters** — signals older than 18 months are deprioritized; flag any signal older than 12 months with `[Signal age: X months — verify]`
- **Volume discipline** — deliver exactly what was requested; if fewer qualified leads exist, explain why and offer to broaden criteria

---

## Edge Cases

- **User gives no criteria**: Start with Bishop AI's primary ICP (B2B SaaS, 50–300 employees, active GTM build-out, Series A–C, North America) and confirm before searching
- **User pastes a raw list**: Skip Phase 1–3, go straight to Phase 4 qualification and Phase 5 card building
- **User wants a specific company researched**: Treat as a single-lead deep dive — skip scoring, go deep on contact intel and outreach angles
- **No strong leads found**: Report honestly, explain the constraint (too narrow ICP, limited signal in that vertical), and offer 2–3 ICP adjustments to try
