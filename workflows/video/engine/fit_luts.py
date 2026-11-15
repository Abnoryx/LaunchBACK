"""Fit one 3D LUT per Magic Bullet Looks layer from (engine frame without Looks, reel frame) pixel pairs.
usage: python3 -I fit_luts.py <project.json> <frames_dir> <reel.mp4> <out luts.json> [root comp=transition]
Frames are f%05d.png at 30 fps numbering (render.mjs). Engine frames must be rendered WITHOUT luts.
Model: affine RGB fit + binned residual on a 17^3 grid (only bins with enough samples), lightly smoothed."""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image

proj, frames_dir, reel, out = sys.argv[1:5]
ROOT = sys.argv[5] if len(sys.argv) > 5 else "transition"
N, W, H = 17, 180, 320
d = json.load(open(proj))
comps = {c["id"]: c for c in d["comps"]}
byname = {c["name"]: c for c in d["comps"]}


def intervals(comp, a, b, off, acc, depth=0):
    """Root-time intervals during which each comp is shown: acc[name] += [(r0, r1, root->local offset)]."""
    acc.setdefault(comp["name"], []).append((a, b, off))
    if depth > 8:
        return
    for L in comp["layers"]:
        sub = comps.get(L.get("src_id"))
        if not sub or not L.get("enabled", True):
            continue
        # times here are root times; layer times are local: local = root + off
        lo, hi = max(a, L["in_point"] - off), min(b, L["out_point"] - off)
        if hi > lo:
            intervals(sub, lo, hi, off - L.get("start_time", 0), acc, depth + 1)


acc = {}
root = byname[ROOT]
intervals(root, 0, root["dur"], 0, acc)

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", reel, "-vf", f"scale={W}:{H}:in_color_matrix=bt709,boxblur=1",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
R = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
frames = {int(os.path.basename(f)[1:-4]): f for f in glob.glob(f"{frames_dir}/f*.png")}

luts = {}
for c in d["comps"]:
    for L in c["layers"]:
        fx = [e for p in L.get("props", []) if p["m"] == "ADBE Effect Parade" for e in p.get("c", [])]
        if not any(e["m"] == "MB LookSuite3" and not e.get("off") for e in fx) or not L.get("enabled", True):
            continue
        E, Rr = [], []
        for a, b, off in acc.get(c["name"], []):
            r0, r1 = max(a, L["in_point"] - off), min(b, L["out_point"] - off)
            for n, f in frames.items():
                t = n / 30
                if r0 + 0.05 <= t < r1 - 0.05 and n < len(R):
                    e = np.asarray(Image.open(f).convert("RGB").resize((W, H), Image.BILINEAR)).astype(np.float64)
                    E.append(e.reshape(-1, 3)); Rr.append(R[n].reshape(-1, 3).astype(np.float64))
        key = f"{c['name']}|{L['i']}"
        if not E:
            print(key, "no frames"); continue
        E, Rr = np.concatenate(E) / 255, np.concatenate(Rr) / 255
        X = np.c_[E, np.ones(len(E))]
        A, *_ = np.linalg.lstsq(X, Rr, rcond=None)
        res = Rr - X @ A
        idx = np.clip(np.rint(E * (N - 1)).astype(int), 0, N - 1)
        flat = (idx[:, 2] * N + idx[:, 1]) * N + idx[:, 0]
        cnt = np.bincount(flat, minlength=N ** 3)
        rs = np.stack([np.bincount(flat, res[:, k], N ** 3) for k in range(3)], 1)
        mean = np.where(cnt[:, None] >= 30, rs / np.maximum(cnt, 1)[:, None], 0) * np.minimum(1, cnt / 200)[:, None]
        g = np.stack(np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij"), -1)[..., ::-1].reshape(-1, 3) / (N - 1)
        # g rows ordered b-major: index ((b*N)+g)*N+r with columns (r,g,b)
        lut = np.c_[g, np.ones(len(g))] @ A + mean
        lut = np.clip(lut, 0, 1)
        mae0 = np.abs(E - Rr).mean() * 255
        fit = np.clip(X @ A + mean[flat], 0, 1)
        print(f"{key}: {len(E) // (W * H)} frames, mean abs diff {mae0:.1f} -> {np.abs(fit - Rr).mean() * 255:.1f}")
        luts[key] = {"n": N, "data": [int(round(v * 255)) for v in lut.reshape(-1)]}
json.dump(luts, open(out, "w"))
print(len(luts), "luts ->", out)
