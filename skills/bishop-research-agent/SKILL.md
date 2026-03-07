---
name: bishop-research-agent
description: Researches and profiles business leads for Bishop AI's AI automation consulting practice. Use this skill whenever the user asks to research leads, find prospects, identify companies to pitch, do outreach research, build a pipeline, find clients, or discover who Bishop AI should sell to. Also trigger when the user says things like "research leads", "find me prospects", "who should we pitch", "build a lead list", "look up companies for outreach", "find companies that need AI automation", or any variation of finding potential clients or sales targets for Bishop AI. Always use this skill to produce structured, actionable lead profiles — don't just dump a generic web search. This skill is specifically tuned to Bishop AI's ICP (ideal customer profile), brand voice, and pitch style.
---

# Bishop AI — Research Agent

Research and profile potential clients for Bishop AI's AI automation consulting practice. Output structured lead intelligence that the sales team can act on immediately.

---

## Bishop AI's ICP (Ideal Customer Profile)

Bishop AI targets companies that:
- Have **manual, repetitive workflows** eating revenue-generating team time (sales, ops, content, finance)
- Are **growth-stage or scaling** — enough complexity to need automation, not yet locked into enterprise contracts
- Have a **clear ROI argument** — time saved, pipeline accelerated, or cost reduced
- Work in industries where **AI adoption is accelerating but execution is lagging**: creator economy, fintech, healthtech, B2B SaaS, professional services
- Have **decision-makers with budget authority**: founders, COOs, Head of RevOps, VP Sales, CMO

Strong negative signals: companies already locked into expensive enterprise AI contracts, pure-play tech giants with internal AI teams, companies with fewer than 10 employees.

---

## Research Process

### Step 1: Clarify the Brief

If the user hasn't specified, ask:
1. **Target industry or vertical** (e.g., creator economy, fintech, healthcare, B2B SaaS, or open)
2. **Company size preference** (SMB, mid-market, enterprise, or no preference)
3. **Number of leads to find** (default: 5–10)
4. **Any known context** — e.g., "similar to FanBasis", "companies we've already talked to", specific geographies

If the user gives a clear enough brief (e.g., "research leads for creator economy companies"), skip this step and proceed.

---

### Step 2: Research

Use `WebSearch` to find relevant companies. Run 3–5 targeted searches to surface real companies. Good search patterns:

- `"[industry] companies scaling 2025 2026 AI automation"`
- `"[industry] startups growth stage Series A B 2025"`
- `"companies hiring RevOps OR 'head of operations' [industry] 2026"`
- `"[industry] platforms [pain point] manual process"`

For each candidate company, research:
- What they do (1 sentence)
- Estimated size (employees, funding stage if available)
- Key workflow pain point Bishop AI can address
- Decision-maker title(s) to target
- Why now — any recent signal (funding, hiring, expansion, product launch)

Aim for 5–10 qualified leads. Drop candidates that clearly don't fit the ICP.

---

### Step 3: Score and Filter

For each lead, silently score fit (1–3):
- **3 — Strong fit**: Clear workflow pain + budget signal + right stage
- **2 — Potential fit**: Fits industry but pain point less obvious or size uncertain
- **1 — Weak fit**: Interesting but missing key ICP criteria

Only include 3s and 2s in the final output. Explain your reasoning briefly in the profile.

---

### Step 4: Output — Lead Intelligence Report

Output a clean, scannable report. Use Bishop AI brand voice: direct, results-focused, no filler words.

```
# Bishop AI — Lead Intelligence Report
[Date] | [Target Vertical] | [N] leads

---

## [Company Name]
**Website:** [url]
**Size:** [employees or funding stage]
**Industry:** [vertical]
**Fit Score:** ⭐⭐⭐ / ⭐⭐⭐⭐ etc.

**What they do:** [1 sentence]

**Workflow pain point:** [Specific problem Bishop AI can solve — be concrete, not generic]

**Bishop AI pitch angle:** [1–2 sentences on how to open the conversation — reference their specific pain, not generic AI]

**Decision-maker to target:** [Title(s)]

**Why now:** [Recent signal — funding round, hiring spike, product launch, market shift]

---
[repeat for each lead]

---
## Research Notes
[Any patterns noticed across leads, suggested outreach sequence, or flags]
```

---

## Output Standards

- **No buzzwords**: Do not use leverage, synergy, seamless, robust, transformative, cutting-edge, or any term from the banned list in `skills/captivate/references/brand-voice.md`
- **Be specific**: "their SDR team manually enters leads from 3 tools" beats "they have data inefficiencies"
- **Cite signals**: When noting "why now", reference a real event (funding announcement, job posting, press mention) — don't speculate
- **Pitch angle is a hook, not a deck**: One clear opening angle — what problem you lead with, not a full proposal

---

## Edge Cases

- **No industry specified**: Default to creator economy and B2B SaaS — the two verticals where Bishop AI has current portfolio evidence (FanBasis, MeridianFinancial)
- **User wants a specific company researched**: Skip broad search, go deep on that one company — same output format, single profile
- **User provides a company name with no context**: Research them, score them, and note fit clearly — if they're a 1, say so and explain why
- **No strong leads found**: Be honest. Report what was found, explain why the vertical may be thin right now, and suggest a pivot
