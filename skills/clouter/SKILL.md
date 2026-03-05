---
name: clouter
description: "Generates AI Diligence Statements using the CLOUTER Framework — a structured process for disclosing AI collaboration in professional deliverables. Use this skill whenever the user mentions: creating a client onboarding kit, needs an AI diligence statement, wants to disclose AI usage in a deliverable, references the CLOUTER framework, asks about AI collaboration disclosure, needs an AI usage statement, or is preparing a client-facing document that involved AI assistance. Trigger even if the user just says 'I need to disclose my AI use' or 'generate a diligence statement for this project'."
---

# CLOUTER Diligence Statement Generator

Generate professional, transparent AI diligence statements for client-facing and published work. Walk through each step below in sequence, gathering inputs before producing output.

---

## Why This Matters

Clients and stakeholders increasingly expect transparency about AI involvement in professional work. A well-crafted diligence statement builds trust, meets emerging disclosure norms, and demonstrates responsible AI use — without undermining the quality or credibility of the work itself. This skill ensures every statement is consistent, professional, and auditable.

---

## The CLOUTER Process

Work through each step. Ask the user for missing information rather than guessing.

### C — Context & Criteria

Ask the user:

> "To confirm whether a diligence statement is required and to tailor it properly, please describe:
> 1. The project name or ID (e.g., "Q1 Brand Strategy" or "Client: Acme Corp")
> 2. The type of deliverable (e.g., report, presentation, proposal, onboarding kit, analysis)
> 3. The intended audience (e.g., external client, internal team, published publicly)
> 4. Whether the output is **client-facing**, **published**, or **internal-only**"

A diligence statement is **mandatory** for client-facing and published outputs. For internal-only work, it is recommended but optional — note this to the user if applicable.

---

### L — Level of AI Collaboration

Explain the three levels and ask the user to choose one:

> **Light** — AI was used only for brainstorming, ideation, or light research. All drafting, analysis, and final decisions were made by humans.
>
> **Medium** — AI assisted with drafting, editing suggestions, or summarizing research. Humans reviewed, revised, and finalized all content.
>
> **Heavy** — AI played a substantial role in co-creating the deliverable, including data analysis, structuring, drafting, or synthesis. Humans directed, reviewed, and approved the final output.

Prompt: *"Which level best describes how AI was used in this project?"*

---

### O — Outlined AI Tasks

Ask the user to list every specific AI-assisted task. Be explicit that you need their exact wording, as these will appear in the statement.

> "Please list every task where AI assistance was used — for example: initial draft generation, research synthesis, data analysis, editing and refinement, brainstorming session facilitation, slide structure, executive summary writing. List as many as apply."

Capture their exact phrasing. Do not paraphrase or collapse items.

---

### U — Usage Logging

When the statement is produced, append an entry to the **AI-Collab-Diligence log** at:
`~/.claude/AI-Collab-Diligence-Log.md`

Each log entry must include:
- Project ID and date
- Collaboration level chosen
- The final statement text

After appending, silently read the five most recent entries from the log and compare their phrasing with the new statement. If the new statement differs materially in wording for a similar collaboration level (e.g., different responsibility framing, different structure), append the note `FLAG: wording variance` at the end of the new log entry.

If the log file does not exist, create it with a header:
```
# AI-Collab-Diligence Log
Track all AI diligence statements by project.
---
```

---

### T — Tone & Transparency Standards

The final statement must meet all of these:

| Criterion | Requirement |
|-----------|-------------|
| Length | 75–150 words |
| Voice | First-person ("I" or "we") |
| Tone | Professional, confident, and warm — not defensive or apologetic |
| Clarity | No legalese, no overly technical AI jargon |
| Banned words | Do not use: *leveraged, utilized, synergize, cutting-edge, robust, seamless, state-of-the-art, innovative* |
| Transparency | Clearly discloses AI's role without framing it as a disclaimer or caveat |
| Credibility | Does not undermine the quality of the work — positions AI as a tool, not a replacement for expertise |

---

### E — Evaluation & Quality Checks

Before displaying the statement, silently verify all six criteria:

1. **Task coverage** — Every AI task listed in section O is reflected in the statement
2. **Collaboration level** — The chosen level from section L is accurately represented
3. **Responsibility clause** — The required clause (see section R) is present at or near the end
4. **Tone compliance** — Statement meets all T criteria (word count, voice, banned words, tone)
5. **Transparency balance** — Statement is honest without undermining credibility
6. **Log execution** — The logging step (section U) has been completed and variance checked

If any criterion fails, revise the statement before displaying it. Do not show a failed draft.

---

### R — Responsibility Declaration

The following clause must appear verbatim at or near the end of every statement:

> *"I/we affirm that while AI assistance was instrumental, I/we accept full responsibility for the accuracy, quality, and presentation of the final work."*

This clause is non-negotiable and must not be paraphrased or removed.

---

## Output Format

After all inputs are gathered and all checks pass, output:

1. A single cohesive paragraph (the diligence statement) meeting all criteria above
2. On a new line: `Log updated.`

Do not add headers, bullet points, or labels to the statement itself — it should read as a polished, standalone paragraph ready to insert into a document.

---

## Example Output Shape

*(This is a structural illustration — actual content will vary based on inputs)*

> In preparing [deliverable] for [audience], I/we engaged AI tools to assist with [task 1], [task 2], and [task 3]. This collaboration reflects a [Light/Medium/Heavy] level of AI involvement, where AI supported [brief description of role]. All AI-generated content was reviewed, refined, and approved by [professional role]. I/we affirm that while AI assistance was instrumental, I/we accept full responsibility for the accuracy, quality, and presentation of the final work.

`Log updated.`

---

## Edge Cases

- **User doesn't know their project ID**: Prompt them to create a short identifier (e.g., "ClientName-Month-Year"). Remind them this helps with audit consistency.
- **User wants to skip steps**: Explain briefly why each step matters for the log and the statement quality, then let them decide. Don't force it.
- **Collaboration level is ambiguous**: Help them choose by asking a clarifying question: "Did AI write any full paragraphs or sections, or was its role more advisory?"
- **Internal-only project**: Note that a statement is optional, but offer to generate one anyway for internal records.
