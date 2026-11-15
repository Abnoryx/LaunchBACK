"""Score engine frames of the OG project against the posted reel, per shot.
usage: python3 -I parity.py <frames_dir> <reel.mp4> <fps_of_frames_naming=30> <out_dir> [label]
Frames are named f%05d.png with the frame number at 30 fps (as render.mjs writes them).
Writes <out_dir>/<label>.md (per-shot SSIM / mean abs diff / histogram distance) and side-by-side sheets."""
import glob, io, os, subprocess, sys
import numpy as np
from PIL import Image

frames_dir, reel, fps, out_dir = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
label = sys.argv[5] if len(sys.argv) > 5 else "scores"
os.makedirs(out_dir, exist_ok=True)
CUTS = [0, 97, 141, 249, 345, 455, 547, 636, 713, 774, 845, 934, 992]
NAMES = ["S1", "S1b", "S2", "S3", "S4", "S5", "S6", "S7", "S8a", "S8b", "S9", "S10"]
PAPER = {"S1", "S1b", "S3", "S4", "S6", "S8a", "S10"}
W, H = 360, 640

# whole reel decoded once, BT.709, at 360x640
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", reel, "-vf", f"scale={W}:{H}:in_color_matrix=bt709",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
R = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def luma(a):
    return a.astype(np.float64) @ [0.2126, 0.7152, 0.0722]


def ssim(x, y):
    from numpy.lib.stride_tricks import sliding_window_view as sw
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    X, Y = sw(x, (7, 7))[::2, ::2], sw(y, (7, 7))[::2, ::2]
    mx, my = X.mean((-1, -2)), Y.mean((-1, -2))
    vx, vy = X.var((-1, -2)), Y.var((-1, -2))
    cxy = ((X - mx[..., None, None]) * (Y - my[..., None, None])).mean((-1, -2))
    return float((((2 * mx * my + C1) * (2 * cxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (vx + vy + C2))).mean())


def hist_dist(a, b):
    d = 0
    for c in range(3):
        ha, _ = np.histogram(a[..., c], 32, (0, 256)); hb, _ = np.histogram(b[..., c], 32, (0, 256))
        d += 0.5 * np.abs(ha / ha.sum() - hb / hb.sum()).sum()
    return d / 3


rows, per = [], {n: [] for n in NAMES}
for f in sorted(glob.glob(f"{frames_dir}/f*.png")):
    n = int(os.path.basename(f)[1:-4])
    if n >= len(R) or n >= 992:
        continue
    e = np.asarray(Image.open(f).convert("RGB").resize((W, H), Image.BILINEAR))
    r = R[n]
    shot = NAMES[max(i for i in range(12) if CUTS[i] <= n)]
    s, m, h = ssim(luma(e), luma(r)), float(np.abs(e.astype(int) - r.astype(int)).mean()), hist_dist(e, r)
    per[shot].append((n, s, m, h, e, r))

lines = [f"# Parity: {label}", "", "| shot | type | frames | SSIM | target | mean abs diff | hist dist | pass |", "|---|---|---|---|---|---|---|---|"]
allp = []
for name in NAMES:
    v = per[name]
    if not v:
        continue
    s = np.mean([x[1] for x in v]); m = np.mean([x[2] for x in v]); h = np.mean([x[3] for x in v])
    tgt = 0.80 if name in PAPER else 0.70
    allp.append(s)
    lines.append(f"| {name} | {'paper' if name in PAPER else 'dark'} | {len(v)} | {s:.3f} | {tgt:.2f} | {m:.1f} | {h:.3f} | {'yes' if s >= tgt else 'no'} |")
    # side-by-side sheet: up to 8 pairs, reel left / engine right
    pick = v[:: max(1, len(v) // 8)][:8]
    tiles = [np.concatenate([x[5], x[4]], 1) for x in pick]
    sheet = np.concatenate([np.concatenate(tiles[i:i + 4], 1) if len(tiles[i:i + 4]) == 4 else np.concatenate(tiles[i:i + 4] + [np.zeros_like(tiles[0])] * (4 - len(tiles[i:i + 4])), 1) for i in range(0, len(tiles), 4)], 0)
    Image.fromarray(sheet).resize((sheet.shape[1] // 2, sheet.shape[0] // 2)).save(f"{out_dir}/{label}_{name}.jpg", quality=85)
lines.append(f"\nMean SSIM over shots: {np.mean(allp):.3f}")
open(f"{out_dir}/{label}.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
