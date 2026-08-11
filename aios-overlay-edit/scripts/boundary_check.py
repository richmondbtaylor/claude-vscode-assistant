import json, subprocess, sys
from PIL import Image
from io import BytesIO

SRC = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4"
# NOTE: a "promise" card (12.7-22.6) was planned but dropped after measurement:
# the face-to-screen cut lands at 12.75s and that window shows the course's own
# branded outcome slides, which already visualize the promise beats.
SPEC = [  # id, in, out, snap_in_rule, snap_out_rule
    ("buildables", 141.2, 157.6, "after_talk", None),
    ("diagram",    163.2, 184.0, None,         "before_screen"),
    ("tips",       441.6, 491.2, None,         "before_talk"),
    ("cta",        526.4, 542.65, None,        None),
]
ZONES = [(8, 26), (135, 190), (435, 500), (518, 542)]


def warmth(t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC,
                        "-frames:v", "1", "-vf", "scale=48:27", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True)
    im = Image.open(BytesIO(r.stdout)).convert("RGB")
    px = list(im.getdata())
    return sum(p[0] for p in px) / len(px) - sum(p[2] for p in px) / len(px)


def classify(t):
    return "talk" if warmth(t) > 15 else "screen"


labels = {}
for a, b in ZONES:
    for t in range(a, b + 1):
        labels[t] = classify(t)

transitions = []  # (time, from, to): time = first instant of `to`, 0.25s precision
for a, b in ZONES:
    for t in range(a, b):
        if labels[t] != labels[t + 1]:
            lo, hi = float(t), float(t + 1)
            while hi - lo > 0.25:
                mid = (lo + hi) / 2
                if classify(mid) == labels[t]:
                    lo = mid
                else:
                    hi = mid
            transitions.append((round(hi, 2), labels[t], labels[t + 1]))
print("transitions:", transitions)


def nearest(kind, near):
    c = [tr for tr in transitions if tr[2] == kind]
    return min(c, key=lambda tr: abs(tr[0] - near))[0] if c else None


out = {"cards": []}
for cid, tin, tout, snap_in, snap_out in SPEC:
    if snap_in == "after_talk":
        tt = nearest("talk", tin)
        if tt is not None and tt > tin:
            tin = tt
    if snap_out == "before_screen":
        ts = nearest("screen", tout)
        if ts is not None and abs(ts - tout) < 2.0 and ts < tout:
            tout = ts
    if snap_out == "before_talk":
        tt = nearest("talk", tout)
        if tt is not None and abs(tt - tout) < 2.0 and tt < tout:
            tout = tt
    out["cards"].append({"id": cid, "in": round(tin, 2), "out": round(tout, 2)})

dest = sys.argv[1] if len(sys.argv) > 1 else "build/boundaries.json"
json.dump(out, open(dest, "w"), indent=1)
print(json.dumps(out))
