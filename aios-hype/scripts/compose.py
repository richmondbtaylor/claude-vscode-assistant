"""Compose the v2 vertical 1080x1920 hype short.
Layout timeline (spliced):
  0     - 12.70  full-frame talking head + transparent kinetic-words overlay
  12.70 - 22.60  promise card top / slides screen full-width strip bottom
  22.60 - 26.35  no-code card top / screen strip bottom
  26.35 - 33.92  buildables card top / face strip bottom
  33.92 - end    flex+CTA card top / face strip bottom
Audio: voice loudnorm -23 LUFS + ducked lofi bed (-30), fades. No video fade-in
(opens ON the hook overlay)."""
import pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
B = ROOT / "build"
DUR = 47.754
T1, T2, T3, T4 = 12.7, 22.6, 26.35, 33.92
CARDS = [  # id, in, out (top half 1080x960)
    ("c1_hook", T1, T2),
    ("c2_nocode", T2, T3),
    ("c2_build", T3, T4),
    ("c4_cta", T4, DUR),
]

cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(B / "spliced.mp4")]
for cid, _, _ in CARDS:
    cmd += ["-i", str(B / f"{cid}.mp4")]
cmd += ["-framerate", "30", "-i", str(B / "frames_c0_words" / "f%05d.png")]
cmd += ["-i", str(B / "music_bed.mp3")]
N = len(CARDS)
W_IDX, M_IDX = N + 1, N + 2

fc = [
    f"color=c=0xF9F6F0:s=1080x1920:d={DUR}:r=30[bg]",
    "[0:v]split=3[s1][s2][s3]",
    "[s1]crop=810:1440:825:0,scale=1080:1920[full]",       # full-frame talking head
    "[s2]scale=1080:608[wide]",                             # full-width screen strip
    "[s3]crop=1620:1440:420:0,scale=1080:960[face]",        # face strip
    f"[bg][face]overlay=0:960:shortest=1:enable='gte(t,{T3})'[vA]",
    f"[vA][wide]overlay=0:1136:enable='between(t,{T1},{T3})'[vB]",
    f"[vB][full]overlay=0:0:enable='lt(t,{T1})'[v0]",
]
prev = "v0"
for i, (cid, tin, tout) in enumerate(CARDS, start=1):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{tin}/TB[c{i}]")
    fc.append(f"[{prev}][c{i}]overlay=0:0:enable='between(t,{tin},{tout})':eof_action=pass[v{i}]")
    prev = f"v{i}"
fc.append(f"[{W_IDX}:v]format=rgba,setpts=PTS-STARTPTS[w0]")
fc.append(f"[{prev}][w0]overlay=0:0:enable='lt(t,{T1})':eof_action=pass[vw]")
fc.append(f"[vw]ass=captions.ass,fade=t=out:st={DUR-0.4}:d=0.4[vf]")
fc.append("[0:a]loudnorm=I=-23:TP=-1.5:LRA=11[voice]")
fc.append(f"[{M_IDX}:a]atrim=0:{DUR}[bed]")
fc.append(f"[voice][bed]amix=inputs=2:duration=first:normalize=0,afade=t=in:d=0.2,afade=t=out:st={DUR-0.6}:d=0.6[af]")

cmd += ["-filter_complex", ";".join(fc), "-map", "[vf]", "-map", "[af]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", str(DUR),
        str(B / "final.mp4")]
subprocess.run(cmd, check=True, cwd=str(B))
print("composed:", B / "final.mp4")
