"""Grade scriptforge eval outputs against assertions."""
import json
import re
import os

WORKSPACE = r"C:\Users\richm\.claude\skills\scriptforge-workspace\iteration-1"

EVALS = [
    ("eval-rag-system", "with_skill"),
    ("eval-rag-system", "without_skill"),
    ("eval-automation-mistakes", "with_skill"),
    ("eval-automation-mistakes", "without_skill"),
    ("eval-agent-vs-chatbot", "with_skill"),
    ("eval-agent-vs-chatbot", "without_skill"),
]

def read_script(eval_name, run_type):
    path = os.path.join(WORKSPACE, eval_name, run_type, "outputs", "script.md")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()

def grade(script):
    if script is None:
        return []

    results = []

    # 1. Dual-format structure
    has_shorts = bool(re.search(r'SHORT', script, re.IGNORECASE))
    has_longform = bool(re.search(r'(INTRO|MAIN CONTENT|CHAPTER|long.form)', script, re.IGNORECASE))
    results.append({
        "text": "has_dual_format_structure",
        "passed": has_shorts and has_longform,
        "evidence": f"Shorts section found: {has_shorts}. Long-form markers found: {has_longform}."
    })

    # 2. Timestamps in MM:SS.ms format
    ts_matches = re.findall(r'\d{2}:\d{2}\.\d{3}', script)
    results.append({
        "text": "has_timestamps",
        "passed": len(ts_matches) >= 5,
        "evidence": f"Found {len(ts_matches)} MM:SS.ms timestamps. Sample: {ts_matches[:3]}"
    })

    # 3. Visual cues (at least 3 distinct types)
    cue_types = []
    for cue in ["[VISUAL:", "[B-ROLL:", "[GRAPHIC:", "[CAMERA:", "[TEXT ON-SCREEN:"]:
        if cue in script:
            cue_types.append(cue)
    results.append({
        "text": "has_visual_cues",
        "passed": len(cue_types) >= 3,
        "evidence": f"Found {len(cue_types)} distinct cue types: {cue_types}"
    })

    # 4. Richmond + AI co-host dialogue
    has_richmond = bool(re.search(r'RICHMOND:', script))
    has_ai = bool(re.search(r'(AI CO-HOST:|AI HOST:|^AI:)', script, re.MULTILINE))
    results.append({
        "text": "has_richmond_ai_dialogue",
        "passed": has_richmond and has_ai,
        "evidence": f"RICHMOND: found: {has_richmond}. AI co-host label found: {has_ai}."
    })

    # 5. Shorts reframe (long-form version + short version side by side)
    has_longform_version = bool(re.search(r'(LONG.FORM VERSION|long.form segment|LONG-FORM SEGMENT)', script, re.IGNORECASE))
    has_short_version = bool(re.search(r'(SHORT VERSION|REFRAMED SHORT|SHORT SCRIPT|SHORT #\d)', script, re.IGNORECASE))
    results.append({
        "text": "has_shorts_reframe",
        "passed": has_longform_version or (has_short_version and has_shorts),
        "evidence": f"Long-form version label: {has_longform_version}. Short version label: {has_short_version}."
    })

    # 6. Shorts CTA driving back to full video
    cta_patterns = r'(full video|link below|full tutorial|watch the full|linked below|in the description)'
    has_cta = bool(re.search(cta_patterns, script, re.IGNORECASE))
    results.append({
        "text": "has_shorts_cta",
        "passed": has_cta,
        "evidence": f"CTA language found: {has_cta}. Pattern: '{cta_patterns}'"
    })

    # 7. Script Notes section
    has_notes = bool(re.search(r'(SCRIPT NOTES|Script Notes|CITATION|SOURCE NOTE)', script, re.IGNORECASE))
    results.append({
        "text": "has_script_notes",
        "passed": has_notes,
        "evidence": f"Script Notes section found: {has_notes}."
    })

    # 8. No fabricated URLs
    urls = re.findall(r'https?://\S+', script)
    # Filter out CTAs that just say "link below" etc.
    suspicious_urls = [u for u in urls if not any(x in u for x in ['youtube.com', 'youtu.be'])]
    results.append({
        "text": "no_fabricated_urls",
        "passed": len(suspicious_urls) == 0,
        "evidence": f"Found {len(suspicious_urls)} potentially fabricated URLs: {suspicious_urls[:5]}"
    })

    return results

for eval_name, run_type in EVALS:
    script = read_script(eval_name, run_type)
    grades = grade(script)

    out_path = os.path.join(WORKSPACE, eval_name, run_type, "grading.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"expectations": grades}, f, indent=2)

    passed = sum(1 for g in grades if g["passed"])
    total = len(grades)
    print(f"{eval_name}/{run_type}: {passed}/{total} passed")
    for g in grades:
        status = "PASS" if g["passed"] else "FAIL"
        print(f"  {status} {g['text']}")
