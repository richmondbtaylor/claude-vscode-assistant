import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4"
DST = r"C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup - overlays.mp4"

cards = json.load(open(ROOT / "build" / "boundaries.json"))["cards"]
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC]
for c in cards:
    cmd += ["-i", str(ROOT / "build" / f"{c['id']}.mp4")]
fc, prev = [], "0:v"
for i, c in enumerate(cards, start=1):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{c['in']}/TB[c{i}]")
    fc.append(f"[{prev}][c{i}]overlay=enable='between(t,{c['in']},{c['out']})':eof_action=pass[v{i}]")
    prev = f"v{i}"
cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "copy", DST]
subprocess.run(cmd, check=True)
print("done:", DST)
