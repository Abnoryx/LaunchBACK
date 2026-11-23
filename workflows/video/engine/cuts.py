"""Check that every cut lands within +-1 frame of the reel, and build the side-by-side MP4 (reel | engine).
usage: python3 -I cuts.py <frames_dir (f%05d.png at 30 fps)> <reel.mp4> <out_dir> [sbs.mp4]
For each cut, finds the frame with the largest frame-to-frame change inside a +-6 frame strip, in both videos."""
import glob, os, subprocess, sys
import numpy as np
from PIL import Image

frames_dir, reel, out_dir = sys.argv[1:4]
sbs = sys.argv[4] if len(sys.argv) > 4 else None
CUTS = [97, 141, 249, 345, 455, 547, 636, 713, 774, 845, 934]
W, H = 180, 320
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", reel, "-vf", f"scale={W}:{H}:in_color_matrix=bt709",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
R = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float64)


def eng(n):
    p = f"{frames_dir}/f{n:05d}.png"
    return np.asarray(Image.open(p).convert("RGB").resize((W, H), Image.BILINEAR), np.float64) if os.path.exists(p) else None


lines = ["| cut (reel frame) | reel detected | engine detected | delta | ok |", "|---|---|---|---|---|"]
ok_all = True
for c in CUTS:
    rng = range(c - 6, c + 7)
    rd = {n: np.abs(R[n] - R[n - 1]).mean() for n in rng}
    E = {n: eng(n) for n in range(c - 7, c + 7)}
    if any(v is None for v in E.values()):
        lines.append(f"| {c} | | missing frames | | |"); ok_all = False; continue
    ed = {n: np.abs(E[n] - E[n - 1]).mean() for n in rng}
    rc, ec = max(rd, key=rd.get), max(ed, key=ed.get)
    ok = abs(rc - ec) <= 1
    ok_all &= ok
    lines.append(f"| {c} | {rc} | {ec} | {ec - rc:+d} | {'yes' if ok else 'NO'} |")
lines.append(f"\nAll cuts within +-1 frame: {'yes' if ok_all else 'no'}")
open(f"{out_dir}/cuts.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

if sbs:  # reel left, engine right, 720x640 per side, 30 fps, reel audio
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", reel, "-framerate", "30", "-start_number", "0", "-i", f"{frames_dir}/f%05d.png",
                    "-filter_complex", "[0:v]scale=720:1280,setsar=1[a];[1:v]scale=720:1280,setsar=1[b];[a][b]hstack=inputs=2[v]",
                    "-map", "[v]", "-map", "0:a?", "-shortest", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", sbs], check=True)
    print("side-by-side ->", sbs)
