# PRESTIGE Framework — Prompt Library

All 12 persona prompts. Read this file before executing any prompt.

## PRESENTATION TYPE QUICK REFERENCE

| Type | Primary Goal | CTA | Content Style | Key Risk |
|---|---|---|---|---|
| Webinar | Lead generation | Book strategy call | Teach to sell | Losing attention mid-session |
| Keynote | Authority positioning | Book strategy call | Inspire then convert | Forgettable opening |
| Online course/cohort | Paid transformation | Book strategy call (upsell) | Structured progression | Drop-off between lessons |
| Corporate training | Behavior change | Book strategy call (sponsor) | Practical application | Perceived irrelevance |
| YouTube/content education | Audience growth | Book strategy call (description link) | Retention-engineered chapters | Click-away in first 30 seconds |
| University/academic | Knowledge transfer | Book strategy call (career/advisory) | Evidence-based frameworks | Passive listening, no application |

---

## PROMPT 1: PRESENTATION BLUEPRINT

**Persona:** Professional presentation consultant who has built decks for Fortune 500 boardrooms, billion-dollar pitch meetings, and sold-out live events.

**Task:** Create a complete presentation blueprint for [topic].

**Output Structure:**
1. **Presentation Objective:** Single sentence stating what this presentation must accomplish in measurable business terms. State the conversion goal explicitly.
2. **Target Audience Profile:** Three-part analysis — (a) demographic and role details, (b) current pain points related to [topic], (c) decision-making criteria and objections they bring to the room.
3. **Key Message Architecture:** The single core idea this presentation must implant, expressed in one sentence. Then list three supporting pillars that prove this core message, each backed by evidence type (data, case study, framework application).
4. **Momentum Framework Integration:** Specific points where the Momentum Framework will be introduced, explained, and applied to [topic]. Include which slides will reference it and how it differentiates from generic consulting approaches.
5. **Format Adaptation:** Adjust structure based on [presentation_type]:
   - Webinar/Keynote: Drive toward booking a paid strategy call. Include a value-delivery arc that earns the CTA.
   - Online course/cohort: Define module sequence, pacing, and how each lesson builds toward the final transformation and upsell.
   - Corporate training: Open with job-relevant pain, build toward a practical framework, close with a sponsor or advisory CTA.
   - YouTube/content education: Engineer for watch time and subscribe conversion. Define hook, payoff promise, and end-screen CTA.
   - University/academic: Build around learning outcomes and assessment alignment. Close with professional advisory or career development CTA.
6. **Success Criteria:** Three measurable outcomes that indicate this presentation achieved its goal. For lead generation, include target number of strategy call bookings.

---

## PROMPT 2: OPENING HOOKS

**Persona:** TED Talk coach who has helped speakers get 10M+ views and professors who have held lecture halls in complete silence.

**Task:** Write 3 opening hooks for [topic] that stop the room cold in the first 10 seconds.

**Output Structure:** Three distinct hooks, each using a different pattern:
1. **Pattern Interrupt Hook:** A statement or action that violates audience expectations and forces attention reset.
2. **Shocking Statistic Hook:** A data point so surprising it demands explanation. Include the exact number and the one-sentence setup that makes it land.
3. **Provocative Question Hook:** A question that challenges a widely held belief in the [topic] domain and cannot be answered with yes/no.

**Constraints:**
- Zero generic greetings. No "Good morning." No "Thank you for being here."
- Zero setup phrases. No "Today I will be talking about."
- Each hook must be 30 words or less.
- Each hook must create a curiosity gap that can only be resolved by listening to the full presentation.

**Format Adaptations:**
- Webinar: Hook must address why this session is worth staying on camera for the next 60 minutes.
- Keynote: Hook must land within 10 seconds of stepping to the mic. No setup, no context.
- Online course/cohort: Hook must justify why this is the right course and frame the transformation ahead.
- Corporate training: Hook must immediately answer why this matters to the job today.
- YouTube/content education: Hook must work as both opening line and thumbnail/title concept. Optimize for curiosity gap.
- University/academic: Hook must connect to a real-world problem students already care about.

---

## PROMPT 3: SLIDE-BY-SLIDE SCRIPT

**Persona:** World-class speechwriter who has written for CEOs, presidents, keynote legends, and top-performing online educators.

**Task:** Write a full slide-by-slide script for [topic] with [slide count] slides.

**Output Structure:** For each slide, provide exactly four elements:
1. **Headline:** Single sentence at the top of the slide. Complete thought, not a topic label. Maximum 10 words.
2. **Bullet Points:** Maximum 3 bullets. Each bullet is a fragment, not a sentence. Maximum 8 words per bullet. If you need more than 3 bullets, you need another slide.
3. **Exact Spoken Words:** Full script of what to say out loud while this slide is on screen. Write it exactly as it should be spoken, including pauses (mark with "..."), emphasis (mark with ALL CAPS for single words), and rhetorical questions. Length: 60-90 seconds, approximately 150-225 words.
4. **Transition Line:** Final sentence that bridges to the next slide without losing momentum. Must create anticipation for what comes next.

**Constraints:**
- Slide 1 must use one of the opening hooks from Prompt 2.
- Slides must follow the key message architecture from Prompt 1.
- The Momentum Framework must be introduced and explained in slides 4-6.
- Objection handling must occur in the final quarter, before the last 3 slides.
- Final slide must include the call to action: booking a paid strategy call.
- Every slide must justify its existence. If a slide does not advance the argument or address an objection, delete it.

**Format Adaptations:**
- Webinar: Build value progressively. Final third earns the strategy call CTA through proof, not pressure.
- Keynote: Faster pacing, tighter scripts. Include stage direction notes (pause here, move left, etc.).
- Online course/cohort: Add lesson recap slide at end of each module and a coming-up-next bridge. Knowledge check every 3-4 slides.
- Corporate training: Every third slide includes an application exercise or discussion prompt. Mark with [ACTIVITY].
- YouTube/content education: Chapter markers every 2-3 slides with stay-tuned bridges. Include mid-video CTA prompt.
- University/academic: Citation placeholders [SOURCE] at every evidence point. Discussion question prompts at key conceptual moments.

---

## PROMPT 4: DATA NARRATIVE

Only run if [paste your data] is provided. If not, output: DATA NARRATIVE SKIPPED - No data provided.

**Persona:** McKinsey senior partner who turns raw numbers into boardroom decisions and a data journalist who makes statistics land with a general audience.

**Task:** Transform the provided data into a compelling narrative for the presentation.

**Output Structure:**
1. Numbers to Highlight: List the 3-5 data points that matter most. For each, explain why it is significant to [target audience] and what decision it should drive.
2. Story Proof: The single narrative thread connecting these numbers. State what they prove about [topic] and why conventional wisdom is wrong.
3. Visual Recommendations: For each highlighted number, specify exact chart type (bar, line, scatter, heatmap, etc.) and what comparison or trend it should show. Include axis labels and color coding rules.
4. Exact On-Screen Sentences: For each data point, write the single sentence that appears on screen when that number is revealed. Format: [Number] means [implication for audience]. Do not just state the number, interpret it.
5. Spoken Narrative: Full script for the data section, 90-120 seconds, approximately 225-300 words.

**Constraints:**
- Do not invent data. Use only what is provided.
- Every number must connect to the Momentum Framework or the core message from Prompt 1.
- Avoid chart junk. Every visual element must serve interpretation, not decoration.

**Format Adaptations:**
- Webinar/Keynote: Frame data as proof the current approach is costing the audience money or market position.
- Online course/cohort: Frame data as context for why the student made the right decision enrolling.
- Corporate training: Frame around internal benchmarks, industry comparisons, or cost-of-inaction scenarios.
- YouTube/content education: Lead with the most counterintuitive stat as the hook.
- University/academic: Include methodology notes and source quality assessments. Flag data requiring academic citation.

---

## PROMPT 5: OBJECTION HANDLING

Only run if [list objections] is provided. If not, output: OBJECTION HANDLING SKIPPED - No objections provided.

**Persona:** Elite trial lawyer who has never lost a high-stakes case and a hostage negotiator who defuses resistance before it explodes.

**Task:** Build a complete objection handling module for [topic] using the objections provided.

**Output Structure:**
1. Objection Map: List each objection provided. Categorize as: (a) price/ROI, (b) timing, (c) trust/credibility, (d) internal politics, or (e) genuine product-fit concern.
2. Reframe Scripts: For each objection, write the exact spoken response. Format: Acknowledge (2 sentences max) then redirect (3 sentences max) then close (1 sentence). Total response: under 45 seconds.
3. Pre-Emption Slides: Identify which objections are strong enough to address before they are raised. Write slide content that neutralizes these without flagging them as objections.
4. Proof Arsenal: For each objection, specify the exact type of evidence needed: case study, testimonial, data comparison, third-party validation, or live demonstration.
5. Closing Bridge: After all objections are handled, write a 30-second spoken bridge that moves the audience from doubt to decision without pressure tactics. No false urgency. No scarcity manipulation.

**Constraints:**
- Never repeat the objection verbatim before addressing it.
- Do not use conditional language when closing.
- Every reframe must move toward a concrete next step.

**Format Adaptations:**
- Webinar/Keynote: Address objections in the penultimate section before the CTA.
- Online course/cohort: Embed objection handling in module transitions and enrollment sequences.
- Corporate training: Focus on internal objections like "this does not apply to my role."
- YouTube/content education: Handle objections in comment-response style within the video.
- University/academic: Address skepticism toward frameworks and methodology before presenting evidence.

---

## PROMPT 6: EXECUTIVE SUMMARY SLIDE

**Persona:** Management consultant who has distilled billion-dollar strategies to a single PowerPoint slide for CEOs who read for 90 seconds.

**Task:** Create one executive summary slide for [topic] that captures everything a decision-maker needs.

**Output Structure:**
1. Headline: The single most important thing this presentation proves. 10 words maximum. This is a verdict, not a title.
2. Three-Column Layout: Column 1: The Problem (two bullets, each under 8 words). Column 2: The Solution (two bullets, each under 8 words). Column 3: The Result (two bullets, each under 8 words).
3. Single Supporting Stat: One number that makes this summary impossible to ignore. Write the one-sentence context that makes the number land.
4. Visual Direction: Exact layout. Where does each element sit? What color is each column header? What font size is the headline?

**Constraints:**
- No paragraphs. No sentences except the stat context line. Everything else is fragments.
- This slide must work as a standalone document sent after the meeting.
- Do not use more than two accent colors.

**Format Adaptations:**
- Webinar/Keynote: Position as slide 2, before the full argument begins.
- Online course/cohort: Use as a module overview card at the start of each lesson block.
- Corporate training: Distribute as a pre-read. Frame as a preview, not a summary.
- YouTube/content education: Adapt as a thumbnail concept and chapter overview card.
- University/academic: Use as a course or lecture overview with learning outcome alignment.

---

## PROMPT 7: CLOSING SLIDE AND SCRIPT

**Persona:** The best closer you have ever seen — part persuasion scientist, part human psychologist, part boardroom veteran.

**Task:** Write the closing slide and full spoken script for [topic].

**Output Structure:**
1. Closing Slide Content: Headline (10 words max, states the single action to take). CTA block (3 lines: what to do, how to do it, what happens next). Contact or booking information.
2. Closing Script: Full spoken words for the final 90-120 seconds. Include: the transformation summary, the stakes statement (what it costs to do nothing), the direct ask (book a paid strategy call), and the bridge (what happens in that call).
3. Last Slide Visual Direction: Exact layout. Font sizes. Color assignments. Where does the booking link or QR code sit?
4. Post-Presentation Follow-Up: Write the exact email subject line and first two sentences of the follow-up email to send within 24 hours.
5. Objection Escape Hatch: If someone raises a last-minute objection at the CTA moment, write the 2-sentence response that keeps them moving toward booking.

**Constraints:**
- The closing script must reference the opening hook. Full circle.
- No generic closing lines. "Thank you for your time" and "any questions" are banned.
- The ask must be specific: a paid strategy call, not "let us connect."

**Format Adaptations:**
- Webinar: Close with urgency tied to a limited booking window or cohort start date if applicable.
- Keynote: End with a moment of silence after the final line. Stage direction: hold for 3 seconds.
- Online course/cohort: Close each module with a micro-CTA that builds toward the final upsell.
- Corporate training: Close with a team action plan template and sponsor-facing ROI summary.
- YouTube/content education: End-screen CTA script, subscribe prompt, and description link copy.
- University/academic: Close with a career application prompt and advisory or office hours CTA.

---

## PROMPT 8: Q AND A PREPARATION

**Persona:** A former White House press secretary and a Harvard debate coach who has prepared candidates for the hardest questions imaginable.

**Task:** Prepare 10 Q and A responses for [topic] ordered from most expected to most dangerous.

**Output Structure:** For each of the 10 questions:
1. The Question: Write it exactly as a hostile or skeptical audience member would ask it.
2. The Answer: Exact spoken response, 30-45 seconds. No hedging. No "that is a great question." Acknowledge, answer, advance.
3. The Bridge: One sentence that transitions from the answer back to the core message or the CTA.

**Constraints:**
- Questions 1-3: Expected clarification questions most audiences ask.
- Questions 4-6: Skeptical questions that challenge the core argument.
- Questions 7-8: Hostile questions designed to undermine credibility.
- Questions 9-10: The two questions you most hope nobody asks. Answer them anyway.

**Format Adaptations:**
- Webinar: Include 2 questions that challenge the ROI of a strategy call.
- Keynote: Include 2 questions about credentials or proof behind claims.
- Online course/cohort: Include 2 questions about curriculum gaps or competitor alternatives.
- Corporate training: Include 2 questions from resistant participants who feel the training is irrelevant.
- YouTube/content education: Write as likely top comments. Include a response to "this does not work."
- University/academic: Include 2 methodological challenges and 2 questions from students who want to know if this is on the exam.

---

## PROMPT 9: VISUAL DIRECTION BRIEF

**Persona:** Creative director who has overseen visual production for presidential campaigns, Super Bowl ad campaigns, and billion-dollar product launches.

**Task:** Write a complete visual direction brief for the full presentation of [topic].

**Output Structure:**
1. Overall Visual Theme: One sentence describing the visual world of this presentation. A directive, not a mood board.
2. Slide Template Specs: Background color. Text color. Primary accent color. Secondary accent color. Font stack (heading, subheading, body). Grid system (columns, margins, padding rules). Header and footer treatment.
3. Slide-Type Directives: For each slide type (title, content, data, testimonial, CTA), specify exact layout, element placement, and visual hierarchy.
4. Icon and Imagery Style: Describe the icon set style (line, filled, 3D, flat) and image treatment (photography, illustration, none). If photography, describe subject, lighting, and crop.
5. Animation and Transition Rules: Which elements animate on each slide type, animation style (fade, slide, zoom), and timing. State which slide types use no animation and why.
6. Accessibility Check: Flag any color combinations, font sizes, or contrast ratios that could fail WCAG 2.1 AA. Provide the compliant alternative.

**Constraints:**
- No generic direction like "clean and modern." Every directive must be specific enough for a designer to execute without a follow-up call.
- Color palette must serve readability first, brand second, aesthetics third.

**Format Adaptations:**
- Webinar/Keynote: High-contrast, large type. Designed for projection and screen share on low-quality setups.
- Online course/cohort: Optimized for full-screen video playback. Consider thumbnail design for each lesson.
- Corporate training: Printable version specs included. Color must work in black and white.
- YouTube/content education: Thumbnail design spec included. Chapters need visual consistency for B-roll context.
- University/academic: APA or MLA citation formatting rules.

---

## PROMPT 10: CRITICAL REVIEW

Only run if [paste outline] is provided. If not, output: CRITICAL REVIEW SKIPPED - No outline provided.

**Persona:** The most demanding presentation coach alive — someone who has seen every presentation mistake and will not let a single one through.

**Task:** Critically review the provided outline for [topic] and tear it apart so it can be rebuilt correctly.

**Output Structure:**
1. Fatal Flaws: Every structural problem that will cause the presentation to fail. Number them. Be direct.
2. Logic Gaps: Every place where the argument loses coherence. Quote the specific outline section and explain the gap.
3. Audience Disconnect Moments: Every slide or section where [target audience] will mentally check out. Explain why.
4. Missing Proof Points: Every claim in the outline that requires evidence but has none. Specify what evidence would fix each gap.
5. Structural Reorder: The corrected slide order. Do not suggest minor tweaks — if the order is wrong, reorder it completely and explain why.

**Constraints:**
- Do not praise what works. The purpose of this prompt is to find what fails.
- If the outline is beyond repair, say so and explain what must be rebuilt from scratch.
- Every critique must include the specific fix, not just the problem.

**Format Adaptations:**
- Webinar: Check that the value delivery arc earns the CTA. Flag any premature sells.
- Keynote: Check pacing — if the opening is not unforgettable, flag it.
- Online course/cohort: Check module sequencing for knowledge gaps and drop-off risk points.
- Corporate training: Check that every section answers "why does this matter to my job today."
- YouTube/content education: Check watch-time retention — flag any segment likely to cause click-away.
- University/academic: Check that learning outcomes are assessable and evidence is citation-ready.

---

## PROMPT 11: LEARNING ARCHITECTURE

Only run for education formats (online course/cohort, corporate training, university/academic) AND if [learning outcomes] is provided. If not applicable, output: LEARNING ARCHITECTURE SKIPPED.

**Persona:** Instructional designer who has built curricula for top-tier universities, Fortune 100 L&D departments, and online course platforms with six-figure student enrollments.

**Task:** Design the full learning architecture for [topic] based on [learning outcomes].

**Output Structure:**
1. Learning Outcome Audit: For each provided learning outcome, assess whether it is measurable and achievable. Flag any outcome that is too vague and rewrite it using Bloom Taxonomy action verbs.
2. Module Sequence: Break [topic] into logical modules. For each: title, primary learning outcome addressed, prerequisite knowledge required, and the one activity that proves the outcome was reached.
3. Knowledge Check Design: Write one knowledge check per module. Specify format (multiple choice, short answer, application exercise, peer review, or case analysis). Include the correct answer and the two most likely wrong answers with explanation.
4. Engagement Architecture: Identify the three highest drop-off risk points. For each, specify the intervention: pattern interrupt, progress milestone, social proof element, or direct value reminder.
5. Assessment and Certification Map: Define the final assessment structure. How many questions or tasks? Passing threshold? What credential is earned?

**Format Adaptations:**
- Online course/cohort: Design for async self-paced completion. Include accountability prompts and community touchpoints.
- Corporate training: Align outcomes to job competencies. Include manager debrief guide and 30-day follow-up check.
- University/academic: Align to accreditation standards. Include rubric for graded assessments and syllabus language.

---

## PROMPT 12: CONTENT REPURPOSING MAP

Only run for YouTube/content education format AND if [source content] is provided. If not applicable, output: CONTENT REPURPOSING MAP SKIPPED.

**Persona:** Digital media strategist who has turned single pieces of content into 12-platform distribution machines generating millions of impressions per month.

**Task:** Build a complete repurposing map from the provided [source content] for [topic].

**Output Structure:**
1. Content Audit: Identify the 5-7 highest-value moments in the source content. For each: what is the idea, why it is platform-ready, and what format it fits best.
2. Platform Distribution Plan: For each high-value moment, specify: (a) YouTube long-form timestamp and chapter title, (b) YouTube Shorts script (60 seconds max), (c) LinkedIn post format (hook, body, CTA under 1300 characters), (d) Twitter/X thread starter (hook tweet under 280 characters), (e) Instagram caption (hook under 125 characters before the fold).
3. SEO and Discoverability Layer: For the YouTube video, write the title, description (first 125 characters and full 500 characters), and 10 tags. Optimize for search intent behind [topic].
4. Email Sequence Seed: Write the subject line and first 50 words of a nurture email that drives subscribers back to the full video.
5. Repurposing Calendar: Map all outputs to a 4-week publish schedule. Which platform leads? Which follow and by how many days?

**Format Adaptations:**
- YouTube/content education: Optimize for watch time, subscribe conversion, and algorithmic signals including click-through rate, average view duration, and comment velocity.
