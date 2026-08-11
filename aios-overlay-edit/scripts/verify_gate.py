import json, pathlib, subprocess, sys
from io import BytesIO
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4"
DST = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup - overlays.mp4"
SRC_DURATION = 542.650998
FPS = 30
REPORT = ROOT / "build" / "verify_report"
REPORT.mkdir(parents=True, exist_ok=True)

BEATS = {  # absolute seconds, from the plan's card table
    "buildables": [141.2, 142.0, 142.8, 143.6, 144.4, 145.2, 148.6],
    "diagram": [163.2 + d for d in (0.6, 3.9, 9.0, 13.3, 16.6)],
    "tips": [441.6 + d for d in (0.05, 3.4, 12.6, 28.5, 40.3)],
    "cta": [526.4 + d for d in (0.05, 2.0, 10.5)],
}

checks = []


def thumb(video, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video,
                        "-frames:v", "1", "-vf", "scale=128:72", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def card_thumb(cid, local_t):
    f = ROOT / "build" / f"frames_{cid}" / f"f{round(local_t * FPS):05d}.png"
    return Image.open(f).convert("RGB").resize((128, 72))


def diff(a, b):
    pa, pb = list(a.getdata()), list(b.getdata())
    return sum(abs(x[c] - y[c]) for x, y in zip(pa, pb) for c in range(3)) / (len(pa) * 3)


def check(name, ok, detail):
    checks.append((name, ok, detail))
    print(("PASS " if ok else "FAIL "), name, "-", detail, flush=True)


# 1. duration
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", DST], capture_output=True, text=True).stdout)
check("duration", abs(d - SRC_DURATION) <= 0.05, f"{d:.3f} vs {SRC_DURATION:.3f}")

# 2. audio stream md5 identical to source
def amd5(v):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-map", "0:a", "-c", "copy",
                        "-f", "md5", "-"], capture_output=True, text=True)
    return r.stdout.strip()
m_src, m_dst = amd5(SRC), amd5(DST)
check("audio-md5", m_src == m_dst and m_src != "", f"{m_src} vs {m_dst}")

# 3. boundaries: output matches card inside window, differs outside
cards = json.load(open(ROOT / "build" / "boundaries.json"))["cards"]
for c in cards:
    cid, tin, tout = c["id"], c["in"], c["out"]
    for label, t_abs, t_local, want_card in [
        ("in+0.5", tin + 0.5, 0.5, True),
        ("out-0.5", tout - 0.5, tout - tin - 0.5, True),
        ("in-0.5", tin - 0.5, 0.5, False),
        ("out+0.5", tout + 0.5, tout - tin - 0.5, False),
    ]:
        if t_abs >= SRC_DURATION - 0.05:
            continue
        out_f = thumb(DST, t_abs)
        card_f = card_thumb(cid, t_local)
        dv = diff(out_f, card_f)
        ok = (dv < 10) if want_card else (dv > 20)
        out_f.resize((640, 360)).save(REPORT / f"{cid}_{label.replace('+','p').replace('-','m')}.png")
        check(f"{cid} {label}", ok, f"diff {dv:.1f} ({'card expected' if want_card else 'no card expected'})")

# 4. beats: the output must preserve the visual change the card itself makes.
# Ground truth = the card's own rendered frames: if the card mutates by X across
# the beat, the output must show at least half of X (and the card must actually
# mutate, catching dead beats in the card design too).
for cid, beats in BEATS.items():
    b = next(x for x in cards if x["id"] == cid)
    for t in beats:
        lo = max(t - 0.4, b["in"] + 0.02)
        hi = min(t + 0.4, b["out"] - 0.02)
        card_dv = diff(card_thumb(cid, lo - b["in"]), card_thumb(cid, hi - b["in"]))
        out_dv = diff(thumb(DST, lo), thumb(DST, hi))
        ok = card_dv > 0.1 and out_dv >= 0.5 * card_dv
        check(f"{cid} beat@{t:.1f}", ok,
              f"output diff {out_dv:.2f} vs card diff {card_dv:.2f}")

fails = [c for c in checks if not c[1]]
print(f"\n{'GATE PASS' if not fails else 'GATE FAIL'}: {len(checks) - len(fails)}/{len(checks)} checks passed")
sys.exit(1 if fails else 0)
