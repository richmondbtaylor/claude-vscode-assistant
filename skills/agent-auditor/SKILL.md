---
name: agent-auditor
description: Audits all Claude Code skills in C:\Users\richm\.claude\skills\ and produces a ranked list of improvement recommendations across clarity, trigger coverage, output quality, framework structure, and agent performance. Use this skill when the user says "audit my agents", "review my skills", "improve my agents", "what skills need work", or "run the agent auditor".
---

# Agent Auditor — Skill Improvement Recommender

Reads every `SKILL.md` file in the skills directory, evaluates each skill against a quality rubric, and produces a prioritized report of actionable improvements Rich can review and approve before applying.

---

## How to Run This Audit

When triggered, execute the following steps in order:

### Step 1 — Discover all skills

List every `SKILL.md` file under `C:\Users\richm\.claude\skills\`:
```
Glob: skills/*/SKILL.md
```

Also check for top-level `.md` skill files (e.g. `skills/expense-classifier.md`) — these are often stubs pointing to a full SKILL.md.

### Step 2 — Read each skill

Read every `SKILL.md` found. For stub files that say "See X for the full skill", follow the reference and read the actual file.

### Step 3 — Score each skill on the AUDIT rubric

Score each skill 1–5 on each dimension:

| Dimension | What to look for |
|---|---|
| **Trigger clarity** | Does the `description` field tell Claude exactly when to use this skill? Are edge cases covered? Would Claude confuse this with another skill? |
| **Output completeness** | Does the skill tell Claude what the final output looks like — format, length, sections? |
| **Failure handling** | Does the skill explain what to do if inputs are missing, ambiguous, or the task can't be completed? |
| **Framework coherence** | If the skill uses a named framework (TAXSORT, CAPTAIN, etc.), is the framework well-defined and consistently referenced? |
| **Action specificity** | Does the skill give Claude specific commands to run, files to read, or APIs to call — or is it too vague? |
| **Recency / staleness** | Are file paths, account names, API endpoints, or thresholds likely still current? Flag anything that looks outdated. |

### Step 4 — Produce the audit report

Output a ranked report in this format:

---

# Agent Audit Report
*Generated: {today's date}*
*Skills audited: {count}*

---

## Priority 1 — High Impact Improvements (score avg < 3.0)

### [Skill Name]
**Overall score:** X.X / 5.0
**Weakest dimension:** {dimension}

**Issue:** {1–2 sentences describing the specific problem}
**Recommendation:** {Concrete, actionable fix — specific enough that Rich can approve it and you can implement it immediately}

---

## Priority 2 — Medium Impact Improvements (score avg 3.0–3.9)

[same format]

---

## Priority 3 — Minor Polish (score avg 4.0+)

[same format, brief]

---

## Skills in Good Shape (score avg 4.5+)

List these with just their name and score — no action needed.

---

## Cross-Skill Issues

Flag any issues that span multiple skills:
- Duplicate trigger conditions (two skills that would both trigger on the same user phrase)
- Missing skills for obvious use cases you've noticed
- Inconsistent conventions (e.g. some skills have troubleshooting tables, others don't)

---

## autoresearch Integration Opportunities

Based on the skills audited, suggest 2–3 specific improvements that could be tested autonomously using the Karpathy autoresearch framework running at `C:\Users\richm\projects\autoresearch`. Focus on prompt engineering hypotheses that could be expressed as modifications to a training objective — e.g. testing different scoring rubrics, reply formats, or filtering logic.

---

### Step 5 — Ask for approval before changing anything

After delivering the report, say:

> "Which of these recommendations would you like me to implement? I can do them one at a time or batch by priority level — just say the word."

**Do NOT modify any skill files until Rich explicitly approves a specific recommendation.**

---

## Evaluation Standards

Use these reference points when scoring:

**Best-in-class example (bishop-research-agent):** Comprehensive architecture diagram, full config table, troubleshooting section, environment variable reference, exact CLI commands. Score this as a 5.0 benchmark.

**Common weaknesses to flag:**
- Skills with only a framework description but no "how to run" steps
- Skills missing a clear output format section
- Skills whose trigger description overlaps heavily with another skill
- Skills that reference files or paths that may no longer exist
- Skills with no error handling guidance

---

## Output Format Rules

- Deliver the full report in a single response — don't paginate
- Use the exact section headers above
- Each recommendation must be specific enough to implement without further clarification
- Flag staleness risks with a ⚠️ symbol
- Keep individual recommendations under 100 words
