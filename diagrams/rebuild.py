import json

STEP_X = 190
STEP_W = 280
STEP_H = 70
SPINE_X = 162
ANN_X = 500
ANN_W = 440   # ends at 940 — clear of code boxes
EV_X = 970    # starts at 970 — 30px gap after annotations
EV_W = 260

Y = {
    's1': 300,
    's2': 560,
    's3': 820,
    's3b': 1080,
    's4': 1360,
    's5': 1640,
    'end': 1880,
}

def seed(s): return abs(hash(s)) % 800000 + 100000

def make_dot(sid, cy, color):
    return {
        "type": "ellipse", "id": f"{sid}_dot",
        "x": SPINE_X - 9, "y": cy - 9,
        "width": 18, "height": 18,
        "strokeColor": color, "backgroundColor": color,
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "angle": 0,
        "seed": seed(sid+"d"), "version": 1, "versionNonce": seed(sid+"dn"),
        "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False
    }

def make_box(sid, cy, label, fill, stroke):
    bx, by = STEP_X, cy - STEP_H // 2
    fs = 16
    ty = by + (STEP_H - fs * 1.4) / 2
    return [
        {
            "type": "rectangle", "id": f"{sid}_box",
            "x": bx, "y": by, "width": STEP_W, "height": STEP_H,
            "strokeColor": stroke, "backgroundColor": fill,
            "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
            "roughness": 1, "opacity": 100, "angle": 0,
            "seed": seed(sid+"b"), "version": 1, "versionNonce": seed(sid+"bn"),
            "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
            "roundness": {"type": 3}
        },
        {
            # Use full box width + textAlign center so Excalidraw centers the text exactly
            "type": "text", "id": f"{sid}_lbl",
            "x": bx, "y": ty, "width": STEP_W, "height": fs * 1.4,
            "text": label, "originalText": label,
            "fontSize": fs, "fontFamily": 3,
            "textAlign": "center", "verticalAlign": "middle",
            "strokeColor": stroke, "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "angle": 0,
            "seed": seed(sid+"l"), "version": 1, "versionNonce": seed(sid+"ln"),
            "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
            "containerId": None, "lineHeight": 1.25
        }
    ]

def make_ann(sid, cy, lines):
    els = []
    line_h = 22
    total_h = len(lines) * line_h
    start_y = cy - total_h / 2
    colors = ["#374151", "#64748b", "#94a3b8"]
    for i, line in enumerate(lines):
        els.append({
            "type": "text", "id": f"{sid}_ann{i}",
            "x": ANN_X, "y": start_y + i * line_h,
            "width": ANN_W, "height": 20,
            "text": line, "originalText": line,
            "fontSize": 13, "fontFamily": 3,
            "textAlign": "left", "verticalAlign": "top",
            "strokeColor": colors[min(i, 2)], "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "angle": 0,
            "seed": seed(sid+f"a{i}"), "version": 1, "versionNonce": seed(sid+f"an{i}"),
            "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
            "containerId": None, "lineHeight": 1.25
        })
    return els

def make_code_box(sid, cy, lines):
    line_h = 18
    pad = 12
    bh = len(lines) * line_h + pad * 2
    by = cy - bh / 2
    els = [{
        "type": "rectangle", "id": f"{sid}_evbox",
        "x": EV_X, "y": by, "width": EV_W, "height": bh,
        "strokeColor": "#374151", "backgroundColor": "#1e293b",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "angle": 0,
        "seed": seed(sid+"ev"), "version": 1, "versionNonce": seed(sid+"evn"),
        "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
        "roundness": {"type": 3}
    }]
    for i, line in enumerate(lines):
        els.append({
            "type": "text", "id": f"{sid}_ev{i}",
            "x": EV_X + pad, "y": by + pad + i * line_h,
            "width": EV_W - pad * 2, "height": line_h,
            "text": line, "originalText": line,
            "fontSize": 12, "fontFamily": 3,
            "textAlign": "left", "verticalAlign": "top",
            "strokeColor": "#22c55e", "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "angle": 0,
            "seed": seed(sid+f"et{i}"), "version": 1, "versionNonce": seed(sid+f"etn{i}"),
            "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
            "containerId": None, "lineHeight": 1.4
        })
    return els

elements = []

# Title
elements.append({
    "type": "text", "id": "title",
    "x": 80, "y": 30, "width": 800, "height": 40,
    "text": "Claude Code + VS Code  -  Setup Guide",
    "originalText": "Claude Code + VS Code  -  Setup Guide",
    "fontSize": 28, "fontFamily": 3,
    "textAlign": "left", "verticalAlign": "top",
    "strokeColor": "#1e40af", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
    "roughness": 0, "opacity": 100, "angle": 0,
    "seed": 11, "version": 1, "versionNonce": 12,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "containerId": None, "lineHeight": 1.25
})
elements.append({
    "type": "text", "id": "subtitle",
    "x": 80, "y": 72, "width": 700, "height": 24,
    "text": "Install 3 free tools  |  add one skill file  |  build unlimited skills",
    "originalText": "Install 3 free tools  |  add one skill file  |  build unlimited skills",
    "fontSize": 15, "fontFamily": 3,
    "textAlign": "left", "verticalAlign": "top",
    "strokeColor": "#3b82f6", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
    "roughness": 0, "opacity": 100, "angle": 0,
    "seed": 13, "version": 1, "versionNonce": 14,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "containerId": None, "lineHeight": 1.25
})

# Spine
spine_top = Y['s1'] - 70
spine_bot = Y['s5'] + 70
elements.append({
    "type": "line", "id": "spine",
    "x": SPINE_X, "y": spine_top, "width": 0, "height": spine_bot - spine_top,
    "strokeColor": "#cbd5e1", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 3, "strokeStyle": "solid",
    "roughness": 0, "opacity": 100, "angle": 0,
    "seed": 20, "version": 1, "versionNonce": 21,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "points": [[0, 0], [0, spine_bot - spine_top]]
})

# Step 1 - VS Code
elements.append(make_dot('s1', Y['s1'], "#c2410c"))
elements += make_box('s1', Y['s1'], "01  Install VS Code", "#fed7aa", "#c2410c")
elements += make_ann('s1', Y['s1'], [
    "Free editor by Microsoft - your home base",
    "code.visualstudio.com -> Download -> Install",
    "All default options are correct"
])

# Step 2 - Node.js
elements.append(make_dot('s2', Y['s2'], "#1e3a5f"))
elements += make_box('s2', Y['s2'], "02  Install Node.js", "#60a5fa", "#1e3a5f")
elements += make_ann('s2', Y['s2'], [
    "The runtime Claude Code needs - install once",
    "nodejs.org -> LTS version -> Install",
    "Verify install worked (need v18+)"
])
elements += make_code_box('s2', Y['s2'], ["node --version", "-> v20.11.0  OK"])

# Step 3 - Claude Code
elements.append(make_dot('s3', Y['s3'], "#6d28d9"))
elements += make_box('s3', Y['s3'], "03  Install Claude Code", "#ddd6fe", "#6d28d9")
elements += make_ann('s3', Y['s3'], [
    "VS Code extension by Anthropic - not the website",
    "Extensions (Ctrl+Shift+X) -> search Claude Code",
    "Sign in with claude.ai  |  Pro/Max or API key"
])

# Step 3b - Python
elements.append(make_dot('s3b', Y['s3b'], "#1e3a5f"))
elements += make_box('s3b', Y['s3b'], "03b  Python Extension", "#93c5fd", "#1e3a5f")
elements += make_ann('s3b', Y['s3b'], [
    "By Microsoft - needed for skills that run scripts",
    "Extensions -> Python (Microsoft) -> Install",
    "Command Palette -> Python: Select Interpreter"
])
elements += make_code_box('s3b', Y['s3b'], ['print("hello")', "-> hello  OK"])

# Step 4 - Skill Creator
elements.append(make_dot('s4', Y['s4'], "#1e3a5f"))
elements += make_box('s4', Y['s4'], "04  Install Skill Creator", "#3b82f6", "#1e3a5f")
# White text on dark blue box
for el in elements:
    if el.get("id") == "s4_lbl":
        el["strokeColor"] = "#ffffff"
elements += make_ann('s4', Y['s4'], [
    "Place SKILL.md in .claude/skills/skill-creator/",
    "Then build the Orchestrator Agent",
    "Routes every request to the right skill"
])
elements += make_code_box('s4', Y['s4'], [
    ".claude/",
    "  skills/",
    "    skill-creator/",
    "      SKILL.md",
    "  memory/",
    "  CLAUDE.md"
])

# Step 5 - Build Skills
elements.append(make_dot('s5', Y['s5'], "#047857"))
elements += make_box('s5', Y['s5'], "05  Build Skills", "#a7f3d0", "#047857")
elements += make_ann('s5', Y['s5'], [
    "promptanything.io -> design skill logic first",
    "Bring to Claude Code: 'Turn this into a skill'",
    "Claude builds, tests, opens viewer - give feedback"
])

# End result ellipse
end_y = Y['end']
elements.append({
    "type": "ellipse", "id": "end_el",
    "x": 100, "y": end_y - 40, "width": 400, "height": 80,
    "strokeColor": "#047857", "backgroundColor": "#a7f3d0",
    "fillStyle": "solid", "strokeWidth": 3, "strokeStyle": "solid",
    "roughness": 1, "opacity": 100, "angle": 0,
    "seed": 600, "version": 1, "versionNonce": 601,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False
})
end_label = "Skills Live Permanently"
fs = 18
elements.append({
    "type": "text", "id": "end_lbl",
    "x": 100, "y": end_y - fs * 0.7,
    "width": 400, "height": fs * 1.4,
    "text": end_label, "originalText": end_label,
    "fontSize": fs, "fontFamily": 3,
    "textAlign": "center", "verticalAlign": "middle",
    "strokeColor": "#065f46", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
    "roughness": 0, "opacity": 100, "angle": 0,
    "seed": 602, "version": 1, "versionNonce": 603,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "containerId": None, "lineHeight": 1.25
})
elements.append({
    "type": "text", "id": "end_sub",
    "x": 80, "y": end_y + 54, "width": 620, "height": 20,
    "text": "Claude auto-triggers the right skill every time - no commands needed",
    "originalText": "Claude auto-triggers the right skill every time - no commands needed",
    "fontSize": 13, "fontFamily": 3,
    "textAlign": "left", "verticalAlign": "top",
    "strokeColor": "#64748b", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
    "roughness": 0, "opacity": 100, "angle": 0,
    "seed": 604, "version": 1, "versionNonce": 605,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "containerId": None, "lineHeight": 1.25
})

# Arrow spine to end
elements.append({
    "type": "arrow", "id": "arrow_end",
    "x": SPINE_X, "y": Y['s5'] + 40,
    "width": 0, "height": end_y - Y['s5'] - 80,
    "strokeColor": "#047857", "backgroundColor": "transparent",
    "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
    "roughness": 1, "opacity": 100, "angle": 0,
    "seed": 610, "version": 1, "versionNonce": 611,
    "isDeleted": False, "groupIds": [], "boundElements": None, "link": None, "locked": False,
    "points": [[0, 0], [0, end_y - Y['s5'] - 80]],
    "startBinding": None, "endBinding": None,
    "startArrowhead": None, "endArrowhead": "arrow"
})

data = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
    "files": {}
}

with open('C:/Users/richm/.claude/diagrams/claude-code-setup.excalidraw', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f'Done - {len(elements)} elements')
