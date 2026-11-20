"""Stages 1-2: per-frame signals, cuts + transition types, per-shot camera (pan/zoom/roll) curves.
All on the small analysis stack; positions reported in 1080-wide pixels."""
import numpy as np
import cv2

DIS = None


def _dis():
    global DIS
    if DIS is None:
        DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return DIS


def frame_signals(fr):
    """-> dict of per-frame arrays (index i compares frame i with i-1; i=0 is 0)."""
    n = len(fr)
    g = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in fr]
    hsv = [cv2.cvtColor(f, cv2.COLOR_RGB2HSV) for f in fr]
    hist = []
    for h in hsv:
        H = cv2.calcHist([h], [0, 1, 2], None, [12, 6, 6], [0, 180, 0, 256, 0, 256]).ravel()
        hist.append(H / (H.sum() + 1e-9))
    S = dict(luma=np.array([x.mean() for x in g]), sharp=np.array([cv2.Laplacian(x, cv2.CV_32F).var() for x in g]),
             sat=np.array([h[..., 1].mean() for h in hsv]), hist_d=np.zeros(n), mad=np.zeros(n), inv=np.zeros(n),
             rgb_split=np.zeros(n))
    for i in range(1, n):
        S['hist_d'][i] = 0.5 * np.abs(hist[i] - hist[i - 1]).sum()
        S['mad'][i] = np.abs(g[i].astype(np.float32) - g[i - 1]).mean()
        S['inv'][i] = np.abs((255 - g[i].astype(np.float32)) - g[i - 1]).mean()  # small = frame is an inverse of the last
    for i in range(n):  # R/B channel misalignment (glitch / chromatic split)
        r, b = fr[i][..., 0].astype(np.float32), fr[i][..., 2].astype(np.float32)
        if r.std() > 4 and b.std() > 4:
            (sx, sy), _ = cv2.phaseCorrelate(r - cv2.blur(r, (9, 9)), b - cv2.blur(b, (9, 9)))
            S['rgb_split'][i] = float(np.hypot(sx, sy))
    return S, g


def camera_step(g0, g1):
    """Similarity transform taking frame g0 to g1 from dense flow on textured pixels.
    -> (dx, dy, scale, rot_deg, inlier_ratio, resid_px) in analysis pixels."""
    flow = _dis().calc(g0, g1, None)
    gy, gx = np.gradient(g0.astype(np.float32))
    tex = np.hypot(gx, gy) > 6
    ys, xs = np.nonzero(tex)
    if len(xs) < 40: return 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    if len(xs) > 4000:
        idx = np.random.default_rng(0).choice(len(xs), 4000, replace=False); ys, xs = ys[idx], xs[idx]
    p0 = np.stack([xs, ys], 1).astype(np.float32)
    p1 = p0 + flow[ys, xs]
    M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=1.0, maxIters=500)
    if M is None: return 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    h, w = g0.shape
    c = np.array([w / 2, h / 2]); cc = M[:, :2] @ c + M[:, 2]  # motion of the frame centre
    m = inl.ravel().astype(bool)
    res = float(np.median(np.linalg.norm((p0[m] @ M[:, :2].T + M[:, 2]) - p1[m], axis=1))) if m.any() else 0.0
    return float(cc[0] - c[0]), float(cc[1] - c[1]), s, rot, float(m.mean()), res


def _hists(fr):
    H = []
    for f in fr:
        h = cv2.calcHist([cv2.cvtColor(f, cv2.COLOR_RGB2HSV)], [0, 1, 2], None, [12, 6, 6], [0, 180, 0, 256, 0, 256]).ravel()
        H.append(h / (h.sum() + 1e-9))
    return np.array(H)


def window_dist(H, i, k=6, g=3):
    """Colour-histogram distance between the shots either side of i (skipping +-g transition frames)."""
    a = H[max(0, i - g - k):max(1, i - g)].mean(0); b = H[min(len(H) - 1, i + g):i + g + k].mean(0)
    return float(0.5 * np.abs(a - b).sum())


def detect_cuts(S, H, min_gap=6, win_thr=0.33):
    """Cut = a frame-to-frame histogram jump (local max over an adaptive threshold) where the shots either side
    really differ (window distance). Candidates closer than min_gap keep the strongest. Calibrated on r1."""
    d = S['hist_d']
    med = np.median(d[1:]); mad = np.median(np.abs(d[1:] - med)) + 1e-6
    thr = max(0.2, med + 10 * mad)
    cand = [i for i in range(1, len(d)) if d[i] > thr and d[i] >= d[i - 1] and d[i] >= d[min(len(d) - 1, i + 1)]]
    cand = [(i, window_dist(H, i)) for i in cand]
    cand = [c for c in cand if c[1] >= win_thr]
    cuts = []
    for i, w in cand:
        if cuts and i - cuts[-1][0] < min_gap:
            if w > cuts[-1][1]: cuts[-1] = (i, w)
        else: cuts.append((i, w))
    return [c[0] for c in cuts], thr, {c[0]: round(c[1], 3) for c in cuts}


def classify_transition(S, cam, i, w=4):
    """Label the transition around cut frame i from per-frame signatures, judged against each side's own level."""
    n = len(S['luma']); a, b = max(1, i - w), min(n - 1, i + w)
    L = S['luma']; tags = []
    pre, post = np.median(L[max(0, a - 8):a]) if a > 0 else L[0], np.median(L[b + 1:b + 9]) if b + 1 < n else L[-1]
    win = L[a:b + 1]
    if win.max() > max(pre, post) + 40: tags.append('flash_white')
    if win.min() < min(pre, post) - 40: tags.append('dip_black')
    if (S['inv'][a:b + 1] < 0.35 * S['mad'][a:b + 1] + 1).any() and S['mad'][a:b + 1].max() > 30: tags.append('invert')
    sh = S['sharp']; ref = min(np.median(sh[max(0, a - 8):a]) if a > 0 else sh[0], np.median(sh[b + 1:b + 9]) if b + 1 < n else sh[-1])
    if ref > 0 and np.r_[sh[a:i], sh[i + 1:b + 1]].min() < 0.3 * ref: tags.append('blur')
    side = [j for j in range(a, b + 1) if j != i]  # flow across the cut itself is meaningless
    sp = np.hypot(cam[side, 0], cam[side, 1]); ok = cam[side, 4] > 0.3
    if (sp[ok] > 12).any(): tags.append('whip')  # >12 analysis px/frame = >60 px @1080
    zs = cam[side, 2][ok]
    if len(zs) and (zs.max() > 1.08 or zs.min() < 0.92): tags.append('zoom_punch')
    if S['rgb_split'][a:b + 1].max() > 1.5: tags.append('rgb_split')
    return tags or ['hard_cut']


def measure(fr, scale_to_1080):
    S, g = frame_signals(fr)
    n = len(fr)
    cam = np.zeros((n, 6)); cam[:, 2] = 1.0
    for i in range(1, n):
        cam[i] = camera_step(g[i - 1], g[i])
    H = _hists(fr)
    cuts, thr, wd = detect_cuts(S, H)
    trans = {int(i): classify_transition(S, cam, i) for i in cuts}
    bounds = [0] + cuts + [n]
    shots = []
    for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
        c = cam[a:b].copy(); c[0] = [0, 0, 1, 0, 1, 0]  # no motion across the cut itself
        # content motion -> cumulative position of the content plane (1080 px), log zoom, roll
        x = np.cumsum(c[:, 0]) * scale_to_1080; y = np.cumsum(c[:, 1]) * scale_to_1080
        z = np.cumprod(c[:, 2]); r = np.cumsum(c[:, 3])
        shots.append(dict(index=k, start=int(a), end=int(b - 1), frames=int(b - a), trans_in=trans.get(int(a), ['start']),
                          cam=dict(x=x.tolist(), y=y.tolist(), zoom=z.tolist(), roll=r.tolist(),
                                   inliers=c[:, 4].round(3).tolist(), resid=(c[:, 5] * scale_to_1080).round(2).tolist())))
    sig = {k: v.round(3).tolist() for k, v in S.items()}
    return dict(cuts=[int(c) for c in cuts], cut_threshold=round(float(thr), 3), cut_strength=wd, transitions=trans, shots=shots,
                signals=sig, cam_raw=cam.round(4).tolist())
