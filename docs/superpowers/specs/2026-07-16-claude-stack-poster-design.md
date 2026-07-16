# .claude Folder Portfolio Poster - Design Spec

Date: 2026-07-16
Status: Approved by Rich (conversation, "go")

## Goal

A single static PNG infographic that maps Rich's entire .claude folder for the AI builder community (LinkedIn/X audience). Peers should walk away thinking "this is a serious, complete operating system built on Claude Code."

## Deliverable

- One PNG, 1080px wide x ~3000px tall (rendered at 2x = 2160px wide), portrait poster format.
- Source: a self-contained HTML file styled in the Bishop AI brand, screenshotted full-page with Playwright at deviceScaleFactor 2.
- Location: `C:\Users\richm\.claude\claude-stack-poster\` (poster.html, render script, final PNG).

## Content rules

- Architecture only: no client names, revenue figures, credentials, or file paths.
- Exactly 71 custom skills (verified: `ls skills/*/SKILL.md | wc -l` = 71; workspace folders and loose .md files are not counted).
- Copy follows Rich's voice rules: no hype words, no em dashes, no AI opener phrases, direct and plain.

## Brand

- Background #FAFBFA (light, per brand rule), ink #1D2333, gold #E0B848, blue #1894C9, warm border #E6E2DE, accents #E05252 / #27a85f.
- Fonts: Poppins 800/900 (headings), Montserrat (labels), Open Sans (body), loaded from Google Fonts at render time.

## Layout (top to bottom, pipeline flow)

1. **Header**: eyebrow "BISHOP AI / SYSTEM MAP", title "Inside my .claude folder", one-line subtitle, stat chips: 71 custom skills / 8 domains / 5 autonomous bots / 1 memory system.
2. **Inputs band**: chips for what triggers the system (a topic, a raw video take, client audit notes, a lead's name, a receipt photo, a WhatsApp message).
3. **Orchestrator bar**: Claude Code + skill router + persistent memory.
4. **Skill map**: all 71 skills as labeled chips inside 8 branded cluster cards in a 2-column grid:
   - Video Engine (15), Image & Design (10), Client Delivery (19), Lead Gen & Research (7), Content & Social (5), Autonomous Bots (5), Back Office (3), Meta & Infra (7).
   - Hero pipelines shown as ordered chip chains inside cards (e.g. scriptforge > hookcraft > vistage > reelforge > captioncraft).
   - Cross-cluster connections drawn as SVG curved arrows between cards, computed by inline JS after layout (data-from/data-to attributes), so positions are always correct regardless of card heights.
5. **Outputs band**: Google Drive + Sheets, YouTube/IG/TikTok/LinkedIn, client deliverables (PDF/HTML/mp4), plus a memory return loop drawn back toward the top ("memory writes back what worked").
6. **Footer**: Rich Taylor / Bishop AI / built on Claude Code.

## Verification

- Render, open the PNG, inspect at full resolution for chip overlap, arrow misalignment, and text truncation. Fix and re-render until clean.
- Cross-check every skill chip name against the actual folder listing.

## V2 (2026-07-16, approved plan: plans/well-my-claude-folder-reactive-swan.md)

V1 undersold the system. V2 (`poster-v2.html` -> `claude-stack-poster-v2.png`, 1080x4079 css at 2x) expands to the whole ecosystem:

- Dual brand framing: Bishop AI x PromptAnything.
- Two verified stat rows: system (71 skills, 23 scripts, 9 bots, 8 MCP connectors, 49 memory rules) and shipped (263 video renders, 319 HTML deliverables, 1,427 images, 37 carousel sets, 14 client engagements). All counted with shell one-liners at build time.
- Runtime band: Claude Code bar + infra rack (plugins, hooks, memory, scripts layer) + MCP connector strip.
- Skill map: same 8 domains, chips now classed framework / pipeline (gold fill) / bot (red dot) with a legend.
- Pipeline anatomy section: vistage 9 phases, reelforge render chain, carousel seamless pano, and the 4-skill audit chain, with real script names in mono type.
- Shared engines grid (Playwright 14 skills, ffmpeg 6, KIE.ai 4, Drive+Sheets 10+, Suno, ElevenLabs, headshot ledger, brand configs).
- Autonomous layer: 6 cards with trigger badges (Atlas daemon, LinkedIn bot daily 1:55 PM, pod watcher, research agents, Instagram sessions, housekeeping incl. 5 AM auto-push and Stop-hook archive).
- Outputs: 6 destinations incl. live deploys (Netlify/Vercel) and WhatsApp reports; red dashed memory loop routed from the Memory card up the right margin into Claude Code.
- render.py now takes a filename arg; v1 files unchanged.
