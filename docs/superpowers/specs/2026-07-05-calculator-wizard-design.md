# Sustainability Calculator: Guided Wizard Design

Date: 2026-07-05
File: `promptanything-sustainability-calculator.html` (single static file, no backend)
Approved by Rich on 2026-07-05.

## Goal

Turn the calculator's entry experience into a guided, personalized wizard so visitors answer a few questions and get a reveal that feels custom-built for them, while keeping the full fixed dashboard underneath for depth. No email gate. Local file for review; deployment decided later.

## Decisions (from brainstorming)

- Guided wizard flow (not a restructured static page, not deploy-first, not report-first)
- Post-wizard: animated big reveal, full existing dashboard below
- No lead capture gate; conversion via existing CTAs
- Deliver as the local file for review

## Approach

Wizard layer added on top of the existing file (approach A). The wizard collects answers, writes them into the existing inputs, calls the existing `calculate()`, then shows a reveal and unhides the dashboard. All 2026-07-04 math/validation/accessibility fixes are reused untouched.

## Experience

1. **Entry:** hero becomes the wizard. Headline + "Build my custom calculator" button. Dashboard hidden until wizard completes (or shared link detected).
2. **Steps (5), one question per screen,** progress indicator, back button, Enter advances, visible skip where optional:
   1. Company or first name (optional, skippable) - powers personalization
   2. Team size (stepper); hourly rate + working days under an "Adjust the fine print" expander
   3. Use cases (existing pills)
   4. Usage profile (existing 4 cards)
   5. Prompting style today (specificity, plain wording); model tier defaults to Balanced
3. **Reveal:** count-up on the net annual savings, headline personalized ("Acme saves $349K per year with better prompting"), three stats (labor recovered, API savings, CO2 avoided), buttons: "See the full breakdown" (scroll to dashboard) and "Start Prompting Free" (promptanything.io).
4. **Dashboard:** existing tabs/charts/report below, inputs panel relabeled "Adjust your numbers", live tweaking as today. "Start over" re-runs the wizard.
5. **Shareable links:** company name joins the URL params. Visiting with params skips the wizard and lands on that company's reveal. sessionStorage prevents wizard replay within a session.

## Constraints

- Single static HTML file, zero backend
- Keyboard and screen-reader operable (focus moves per step, aria-live reveal)
- Mobile-first wizard card; existing breakpoints respected
- Brand: cream base, charcoal, royal blue #0445DC, gold on dark only; Poppins/Montserrat/Open Sans; no em dashes in copy
- All existing fixes preserved (clamping, net-of-subscription math, contrast, aria)

## Testing

Playwright: full wizard path, skip and back paths, keyboard-only completion, shared-link entry, edge inputs, 1440px and 390px viewports, zero console/page errors.
