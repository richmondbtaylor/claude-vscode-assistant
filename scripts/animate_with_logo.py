import sys, os, subprocess, tempfile
import numpy as np
from PIL import Image

FFMPEG = r"C:\Users\richm\.claude\skills\Client Skills\conquer-social-prospecting\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

def remove_bg(logo_path):
    img = Image.open(logo_path).convert("RGBA")
    arr = np.array(img, dtype=np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    lum = 0.299*r + 0.587*g + 0.114*b
    threshold, feather = 220, 30
    alpha = np.clip((threshold - lum) / feather, 0, 1) * 255
    arr[:,:,3] = alpha
    return Image.fromarray(arr.astype(np.uint8))

def spring(t, overshoot=0.18, settle=0.06):
    if t < 0.6:
        s = t / 0.6
        return s * s * (1.0 + overshoot)
    elif t < 0.8:
        s = (t - 0.6) / 0.2
        return (1.0 + overshoot) - s * (overshoot + settle)
    elif t < 1.0:
        s = (t - 0.8) / 0.2
        return (1.0 - settle) + s * settle
    return 1.0

def composite_logo(slide_arr, logo_rgba, logo_target_w, logo_cx, logo_cy, scale=1.0):
    W = int(logo_target_w * scale)
    if W < 2: return slide_arr
    H = int(logo_rgba.size[1] * W / logo_rgba.size[0])
    logo_resized = logo_rgba.resize((W, H), Image.LANCZOS)
    logo_arr = np.array(logo_resized, dtype=np.float32)
    x0 = logo_cx - W // 2; y0 = logo_cy - H // 2
    x1 = x0 + W; y1 = y0 + H
    sx0 = max(0, x0); sy0 = max(0, y0)
    sx1 = min(slide_arr.shape[1], x1); sy1 = min(slide_arr.shape[0], y1)
    lx0 = sx0 - x0; ly0 = sy0 - y0
    lx1 = lx0 + (sx1 - sx0); ly1 = ly0 + (sy1 - sy0)
    if sx1 <= sx0 or sy1 <= sy0: return slide_arr
    out = slide_arr.copy()
    alpha = logo_arr[ly0:ly1, lx0:lx1, 3:4] / 255.0
    logo_rgb = logo_arr[ly0:ly1, lx0:lx1, :3]
    slide_region = out[sy0:sy1, sx0:sx1].astype(np.float32)
    out[sy0:sy1, sx0:sx1] = (logo_rgb * alpha + slide_region * (1 - alpha)).astype(np.uint8)
    return out

def animate(slide_jpg, output_mp4, logo_rgba, fps=30, total_dur=5.0, logo_dur=1.0):
    slide = Image.open(slide_jpg).convert("RGB")
    W, H = slide.size
    slide_arr = np.array(slide)
    logo_w = int(W * 0.18)
    logo_cx = W // 2
    logo_cy = int(H * 0.10)
    total_frames = int(fps * total_dur)
    logo_frames  = int(fps * logo_dur)
    fade_frames  = int(fps * 0.5)
    zoom_start, zoom_end = 1.0, 1.05
    bg = np.full_like(slide_arr, [245, 240, 232])

    # Use Windows-native temp path so ffmpeg.exe can read it
    frame_dir = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "anim_logo_frames")
    os.makedirs(frame_dir, exist_ok=True)

    for i in range(total_frames):
        kb_t = max(0, (i - logo_frames) / max(1, total_frames - logo_frames))
        kb_ease = kb_t * kb_t * (3 - 2 * kb_t)
        zoom = zoom_start + (zoom_end - zoom_start) * kb_ease
        cw = int(W / zoom); ch = int(H / zoom)
        x0 = (W - cw) // 2; y0 = (H - ch) // 2
        frame = np.array(Image.fromarray(slide_arr[y0:y0+ch, x0:x0+cw]).resize((W, H), Image.LANCZOS))
        if i < fade_frames:
            a = i / fade_frames
            frame = (frame * a + bg * (1 - a)).astype(np.uint8)
        logo_scale = spring(i / logo_frames) if i < logo_frames else 1.0
        if logo_scale > 0.01:
            frame = composite_logo(frame, logo_rgba, logo_w, logo_cx, logo_cy, logo_scale)
        Image.fromarray(frame).save(os.path.join(frame_dir, f"frame_{i:04d}.jpg"), quality=92)

    frame_pattern = os.path.join(frame_dir, "frame_%04d.jpg")
    cmd = [FFMPEG, "-y", "-framerate", str(fps), "-i", frame_pattern,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-movflags", "+faststart", output_mp4]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg error:", result.stderr[-800:])
        sys.exit(1)
    for f in os.listdir(frame_dir):
        os.remove(os.path.join(frame_dir, f))
    print(f"Done: {output_mp4}")

if __name__ == "__main__":
    logo_path, slide_jpg, output_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]
    logo_rgba = remove_bg(logo_path)
    animate(slide_jpg, output_mp4, logo_rgba)
