---
name: excalidraw-skill
description: Create Excalidraw diagram JSON files that make visual arguments. Use this skill whenever the user wants to visualize workflows, architectures, concepts, systems, processes, or any ideas that benefit from a diagram. Trigger even if they say "draw", "map out", "chart", "diagram", "visualize", or "show me how X works" — especially for technical architectures, teaching diagrams, or any flowchart-style request.
---

# Colin — Excalidraw Diagram Creator

Generate `.excalidraw` JSON files that **argue visually**, not just display information.

**Setup (first time only):**
```bash
cd C:\Users\richm\.claude\skills\excalidraw-skill\references
uv sync
uv run playwright install chromium
```

## Customization

**All colors live in one file:** `references/color-palette.md`. Read it before generating any diagram — it's the single source of truth for shape fills, strokes, text colors, and evidence artifact backgrounds.

---

## Core Philosophy

**Diagrams should ARGUE, not DISPLAY.**

A diagram isn't formatted text. It's a visual argument that shows relationships, causality, and flow that words alone can't express. The shape should BE the meaning.

**The Isomorphism Test**: If you removed all text, would the structure alone communicate the concept? If not, redesign.

**The Education Test**: Could someone learn something concrete from this diagram, or does it just label boxes? A good diagram teaches — it shows actual formats, real event names, concrete examples.

---

## Depth Assessment (Do This First)

Before designing, determine what level of detail this diagram needs:

### Simple/Conceptual Diagrams
Use abstract shapes when:
- Explaining a mental model or philosophy
- The audience doesn't need technical specifics
- The concept IS the abstraction (e.g., "separation of concerns")

### Comprehensive/Technical Diagrams
Use concrete examples when:
- Diagramming a real system, protocol, or architecture
- The diagram will be used to teach or explain
- The audience needs to understand what things actually look like
- You're showing how multiple technologies integrate

**For technical diagrams, you MUST include evidence artifacts** (see below).

---

## Research Mandate (For Technical Diagrams)

**Before drawing anything technical, research the actual specifications.**

If you're diagramming a protocol, API, or framework:
1. Look up the actual JSON/data formats
2. Find the real event names, method names, or API endpoints
3. Understand how the pieces actually connect
4. Use real terminology, not generic placeholders

Bad: "Protocol" → "Frontend"
Good: "AG-UI streams events (RUN_STARTED, STATE_DELTA, A2UI_UPDATE)" → "CopilotKit renders via createA2UIMessageRenderer()"

---

## Evidence Artifacts

Evidence artifacts are concrete examples that prove accuracy and help viewers learn. Include them in technical diagrams.

| Artifact Type | When to Use | How to Render |
|---------------|-------------|---------------|
| **Code snippets** | APIs, integrations, implementation details | Dark rectangle + syntax-colored text |
| **Data/JSON examples** | Data formats, schemas, payloads | Dark rectangle + green text |
| **Event/step sequences** | Protocols, workflows, lifecycles | Timeline pattern (line + dots + labels) |
| **UI mockups** | Showing actual output/results | Nested rectangles mimicking real UI |
| **Real input content** | Showing what goes IN to a system | Rectangle with sample content visible |
| **API/method names** | Real function calls, endpoints | Use actual names from docs |

---

## Multi-Zoom Architecture

Comprehensive diagrams operate at multiple zoom levels simultaneously:

### Level 1: Summary Flow
A simplified overview showing the full pipeline at a glance. Often placed at top or bottom.

### Level 2: Section Boundaries
Labeled regions grouping related components — visual "rooms" that organize what belongs together.

### Level 3: Detail Inside Sections
Evidence artifacts, code snippets, and concrete examples. This is where educational value lives.

**For comprehensive diagrams, aim to include all three levels.**

---

## Container vs. Free-Floating Text

**Not every piece of text needs a shape around it.** Default to free-floating text. Add containers only when they serve a purpose.

| Use a Container When... | Use Free-Floating Text When... |
|------------------------|-------------------------------|
| It's the focal point of a section | It's a label, description, or annotation |
| Arrows need to connect to it | It describes something nearby |
| The shape itself carries meaning | It's a section title or subtitle |

**The container test**: For each boxed element, ask "Would this work as free-floating text?" If yes, remove the container. Aim for <30% of text elements inside containers.

---

## Design Process (Do This BEFORE Generating JSON)

### Step 0: Assess Depth Required
Determine: **Simple/Conceptual** (abstract shapes, mental models) or **Comprehensive/Technical** (concrete examples, real data, code snippets). If comprehensive, do research first.

### Step 1: Understand Deeply
Read the content. For each concept ask: What does it DO? What relationships exist? What's the core transformation? What would someone need to SEE to understand this?

### Step 2: Map Concepts to Patterns
For each concept, find the visual pattern that mirrors its behavior:

| If the concept... | Use this pattern |
|-------------------|------------------|
| Spawns multiple outputs | **Fan-out** (radial arrows from center) |
| Combines inputs into one | **Convergence** (funnel, arrows merging) |
| Has hierarchy/nesting | **Tree** (lines + free-floating text) |
| Is a sequence of steps | **Timeline** (line + dots + free-floating labels) |
| Loops or improves continuously | **Spiral/Cycle** (arrow returning to start) |
| Is an abstract state or context | **Cloud** (overlapping ellipses) |
| Transforms input to output | **Assembly line** (before → process → after) |
| Compares two things | **Side-by-side** (parallel with contrast) |
| Separates into phases | **Gap/Break** (visual separation) |

### Step 3: Ensure Variety
For multi-concept diagrams: **each major concept must use a different visual pattern**. No uniform cards or grids.

### Step 4: Sketch the Flow
Mentally trace how the eye moves through the diagram. There should be a clear visual story.

### Step 5: Generate JSON
Only now create the Excalidraw elements. **For large diagrams, build one section at a time.**

### Step 6: Render & Validate (MANDATORY)
After generating JSON, run the render-view-fix loop until the diagram looks right. See **Render & Validate** section below.

---

## Large / Comprehensive Diagram Strategy

**Build JSON one section at a time.** Do NOT attempt to generate the entire file in a single pass — Claude has a ~32,000 token output limit, and comprehensive diagrams easily exceed this.

### The Section-by-Section Workflow

1. **Create the base file** with the JSON wrapper and first section of elements
2. **Add one section per edit** — think carefully about layout and cross-section connections
3. **Use descriptive string IDs** (e.g., `"trigger_rect"`, `"arrow_fan_left"`)
4. **Namespace seeds by section** (section 1 uses 100xxx, section 2 uses 200xxx, etc.)
5. **Update cross-section bindings** as you go

After all sections are in, review the whole, then render & validate.

---

## Visual Pattern Library

**Fan-Out**: Central element with arrows radiating to multiple targets. For sources, hubs, root causes.

**Convergence**: Multiple inputs merging through arrows to single output. For aggregation, funnels.

**Tree**: Parent-child branching with connecting lines and free-floating text (no boxes). Use `line` elements for trunk/branches, free-floating text for labels.

**Spiral/Cycle**: Elements in sequence with arrow returning to start. For feedback loops, iterative processes.

**Cloud**: Overlapping ellipses with varied sizes. For context, memory, abstract states.

**Assembly Line**: Input → Process Box → Output with clear before/after. For transformations.

**Timeline**: Vertical or horizontal line with small dots (10-20px ellipses) at intervals, free-floating labels beside each dot.

**Side-by-Side**: Two parallel structures with visual contrast. For before/after, options, trade-offs.

---

## Shape Meaning

| Concept Type | Shape |
|--------------|-------|
| Labels, descriptions, details | **none** (free-floating text) |
| Section titles, annotations | **none** (free-floating text) |
| Markers on a timeline | small `ellipse` (10-20px) |
| Start, trigger, input | `ellipse` |
| End, output, result | `ellipse` |
| Decision, condition | `diamond` |
| Process, action, step | `rectangle` |
| Abstract state, context | overlapping `ellipse` |

---

## Color as Meaning

Colors encode information, not decoration. Always use colors from `references/color-palette.md`. Each semantic purpose has a specific fill/stroke pair. Do not invent new colors.

---

## Modern Aesthetics

- **Roughness**: `0` for clean/technical (default), `1` for hand-drawn feel
- **Stroke Width**: `1` thin, `2` standard, `3` bold emphasis (use sparingly)
- **Opacity**: Always `100` — use color, size, stroke for hierarchy, not transparency
- **Small Markers**: 10–20px ellipses for timeline dots, bullets, visual anchors

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

See `references/element-templates.md` for copy-paste JSON templates for each element type.
See `references/json-schema.md` for full property reference.

---

## Render & Validate (MANDATORY)

You cannot judge a diagram from JSON alone. After generating or editing, MUST render to PNG, view the image, and fix — loop until right.

### How to Render

```bash
cd C:\Users\richm\.claude\skills\excalidraw-skill\references && uv run python render_excalidraw.py <path-to-file.excalidraw>
```

Then use the **Read tool** on the PNG to view it.

### The Loop

1. **Render & View** — run the script, Read the PNG
2. **Audit vs. your vision** — does the visual structure match what you planned? Is the hierarchy correct? Does the eye flow correctly?
3. **Check for defects**: text clipped, overlapping elements, arrows in wrong places, imbalanced spacing, text too small
4. **Fix** — edit JSON coordinates, widen containers, add arrow waypoints, reposition labels
5. **Re-render & re-view**
6. **Repeat** — typically 2-4 iterations. Stop when the diagram matches the design, no defects, balanced composition.

---

## Quality Checklist

### Depth & Evidence
1. Research done (actual specs, formats, event names)
2. Evidence artifacts included (for technical diagrams)
3. Multi-zoom architecture (summary + sections + detail)
4. Concrete over abstract (real content, not placeholder boxes)
5. Educational value (someone can learn from this)

### Conceptual
6. Isomorphism (visual structure mirrors concept behavior)
7. Argument (diagram shows something text couldn't)
8. Variety (each major concept uses different visual pattern)
9. No uniform containers (no card grids or equal boxes)

### Container Discipline
10. Minimal containers (<30% text elements inside shapes)
11. Lines as structure for tree/timeline patterns
12. Typography hierarchy through font size and color

### Technical
13. All relationships have arrows or lines
14. Clear visual flow path
15. `text` property contains only readable words
16. `fontFamily: 3`, `roughness: 0`, `opacity: 100`

### Visual Validation
17. Rendered to PNG and visually inspected
18. No text overflow or overlapping elements
19. Even spacing, arrows connect correctly
20. Readable at export size, balanced composition
