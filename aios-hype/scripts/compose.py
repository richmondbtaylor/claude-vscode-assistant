"""Compose the vertical 1080x1920 hype short: cards top, face strip bottom,
one-word captions, voice at -23 LUFS over the ducked lofi bed, fades."""
import pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
B = ROOT / "build"
DUR = 41.354
WINDOWS = [  # card id, in, out on the spliced timeline
    ("c1_hook", 0.0, 13.65),
    ("c2_build", 13.65, 21.22),
    ("c3_demo", 21.22, 27.52),
    ("c4_cta", 27.52, 41.354),
]

cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(B / "spliced.mp4")]
for cid, _, _ in WINDOWS:
    cmd += ["-i", str(B / f"{cid}.mp4")]
cmd += ["-i", str(B / "music_bed.mp3")]

# S1 (0-13.65) and S4 (21.22-27.52) are screen recordings: show them full-width
# on the cream canvas. S3/S5/S6 are talking head: center-crop face strip.
FACE_EN = "between(t,13.65,21.22)+between(t,27.52,41.354)"
WIDE_EN = "between(t,0,13.65)+between(t,21.22,27.52)"
fc = [
    f"color=c=0xF9F6F0:s=1080x1920:d={DUR}:r=30[bg]",
    "[0:v]split[sa][sb]",
    "[sa]crop=1620:1440:420:0,scale=1080:960[face]",
    "[sb]scale=1080:608[wide]",
    f"[bg][face]overlay=0:960:shortest=1:enable='{FACE_EN}'[vA]",
    f"[vA][wide]overlay=0:1136:enable='{WIDE_EN}'[v0]",
]
prev = "v0"
for i, (cid, tin, tout) in enumerate(WINDOWS, start=1):
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{tin}/TB[c{i}]")
    fc.append(f"[{prev}][c{i}]overlay=0:0:enable='between(t,{tin},{tout})':eof_action=pass[v{i}]")
    prev = f"v{i}"
fc.append(f"[{prev}]ass=captions.ass,fade=t=out:st={DUR-0.4}:d=0.4[vf]")
fc.append("[0:a]loudnorm=I=-23:TP=-1.5:LRA=11[voice]")
fc.append(f"[{len(WINDOWS)+1}:a]atrim=0:{DUR}[bed]")
fc.append(f"[voice][bed]amix=inputs=2:duration=first:normalize=0,afade=t=in:d=0.2,afade=t=out:st={DUR-0.6}:d=0.6[af]")

cmd += ["-filter_complex", ";".join(fc), "-map", "[vf]", "-map", "[af]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", str(DUR),
        str(B / "final.mp4")]
subprocess.run(cmd, check=True, cwd=str(B))
print("composed:", B / "final.mp4")
