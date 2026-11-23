"""Stage 4: tracked curve -> keyframes -> cubic-bezier eases (snapped to our library when close).

A curve is a 1-D array of values per frame (camera x, a word's y, a scale...). We find where it moves (segments
between holds / direction or speed changes), fit a cubic bezier ease to each segment on normalised time, and snap it
to a named library ease when the fit is nearly as good. Output keys are in aeb.K(...) form: (frame, value, ease).
"""
import numpy as np
from scipy.optimize import least_squares

LIB = {  # name -> (x1, y1, x2, y2); ours (library/style.py) + standard CSS/Penner approximations
    'linear': (0.0, 0.0, 1.0, 1.0),
    'quad_out': (1 / 3, 2 / 3, 2 / 3, 1.0), 'quad_in': (1 / 3, 0.0, 2 / 3, 1 / 3),
    'cubic_out': (1 / 3, 1.0, 2 / 3, 1.0), 'cubic_in': (1 / 3, 0.0, 2 / 3, 0.0),
    'quad_inout': (0.45, 0.0, 0.55, 1.0), 'cubic_inout': (0.65, 0.0, 0.35, 1.0),
    'quart_out': (0.25, 1.0, 0.5, 1.0), 'expo_out': (0.16, 1.0, 0.3, 1.0), 'expo_inout': (0.87, 0.0, 0.13, 1.0),
    'ae_easy': (1 / 3, 0.0, 2 / 3, 1.0),
    'standard': (0.8, 0.0, 0.2, 1.0), 'out': (0.333, 0.0, 0.0, 1.0), 'snap': (0.0, 0.0, 0.0, 1.0),
    'push': (0.167, 0.0, 0.0, 1.0), 'dolly': (0.9, 0.0, 0.1, 1.0),
    'back_out': (0.34, 1.56, 0.64, 1.0), 'pop': (0.3, 1.5, 0.6, 1.0),
}


def bezier_y(e, x):
    """y(x) of a CSS-style cubic bezier (P0=0,0 P3=1,1); x array in [0,1]."""
    x1, y1, x2, y2 = e
    x = np.clip(np.asarray(x, float), 0, 1)
    t = x.copy()
    for _ in range(8):  # Newton on x(t) = x
        xt = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        dx = 3 * (1 - t) ** 2 * x1 + 6 * (1 - t) * t * (x2 - x1) + 3 * t ** 2 * (1 - x2)
        t = np.clip(t - (xt - x) / np.where(np.abs(dx) < 1e-6, 1e-6, dx), 0, 1)
    lo, hi = np.zeros_like(x), np.ones_like(x)  # a few bisection steps make it robust where dx ~ 0
    for _ in range(20):
        xt = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        lo, hi = np.where(xt < x, t, lo), np.where(xt >= x, t, hi)
        bad = np.abs(xt - x) > 1e-5
        if not bad.any(): break
        t = np.where(bad, (lo + hi) / 2, t)
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3


def fit_segment(y, snap_tol=0.015):
    """y: values on frames f0..f1 inclusive (len >= 3). Returns (ease_tuple, name_or_None, rmse_norm)."""
    y = np.asarray(y, float)
    span = y[-1] - y[0]
    if abs(span) < 1e-9: return LIB['linear'], 'hold', 0.0
    x = np.linspace(0, 1, len(y))
    yn = (y - y[0]) / span
    errs = {k: float(np.sqrt(np.mean((bezier_y(e, x) - yn) ** 2))) for k, e in LIB.items()}
    best_name = min(errs, key=errs.get)
    if len(y) >= 4:
        r = least_squares(lambda p: bezier_y(p, x) - yn, np.array(LIB[best_name]),
                          bounds=([0, -1, 0, -1], [1, 2.5, 1, 2.5]))
        fit, ferr = tuple(float(v) for v in r.x), float(np.sqrt(np.mean(r.fun ** 2)))
    else:
        fit, ferr = LIB[best_name], errs[best_name]
    if errs[best_name] <= ferr + snap_tol: return LIB[best_name], best_name, errs[best_name]
    return fit, None, ferr


def noise_sigma(v):
    """Tracking-noise estimate from second differences (robust; smooth eased motion has tiny 2nd diffs)."""
    d2 = np.diff(np.asarray(v, float), 2)
    return float(np.median(np.abs(d2)) / 0.6745 / np.sqrt(6)) if len(d2) else 0.0


_TAB = {}


def _table(L):
    """(n_eases, L+1) normalised bezier values for a segment of L frames."""
    if L not in _TAB:
        x = np.linspace(0, 1, L + 1)
        _TAB[L] = np.stack([bezier_y(e, x) for e in LIB.values()])
    return _TAB[L]


def segment_dp(v, sigma=None, max_len=120, penalty=None):
    """Optimal keyframes: dynamic programming over all key placements; each segment is drawn with the best library
    ease between its end values (a hold is just a segment with ~0 span). Cost = SSE / sigma^2 + penalty per key."""
    v = np.asarray(v, float); n = len(v)
    sig = max(sigma if sigma is not None else noise_sigma(v), 0.15)
    pen = penalty if penalty is not None else 6.0 * np.log(n)
    names = list(LIB)
    best = np.full(n, np.inf); best[0] = 0.0
    prev = np.zeros(n, int); pick = np.zeros(n, int)
    for b in range(1, n):
        for a in range(max(0, b - max_len), b):
            if best[a] == np.inf: continue
            L = b - a
            curves = v[a] + (v[b] - v[a]) * _table(L)
            sse = ((curves - v[a:b + 1]) ** 2).sum(1)
            k = int(np.argmin(sse))
            c = best[a] + sse[k] / sig ** 2 + pen
            if c < best[b]: best[b], prev[b], pick[b] = c, a, k
    ks, b = [n - 1], n - 1
    segs = []
    while b > 0:
        segs.append((prev[b], b, names[pick[b]])); b = prev[b]; ks.append(b)
    return sorted(ks), segs[::-1], sig


def curve_to_keys(v, sigma=None, snap_tol=0.015, **kw):
    """-> list of dict(frame, value, ease, ease_name, err); the ease belongs to the segment starting at that key.
    Library eases are used as-is; a segment whose residual is well above noise gets a free bezier (ease_name None)."""
    v = np.asarray(v, float)
    ks, segs, sig = segment_dp(v, sigma, **kw)
    keys = []
    for a, b, name in segs:
        span = abs(v[b] - v[a])
        if span < 6 * sig and np.ptp(v[a:b + 1]) < 8 * sig:
            e, nm, err = LIB['linear'], 'hold', 0.0
        else:
            e, nm, err = fit_segment(v[a:b + 1], snap_tol=max(snap_tol, 3 * sig / span))
        keys.append(dict(frame=int(a), value=float(v[a]), ease=[round(c, 3) for c in e], ease_name=nm, err=round(err, 4)))
    keys.append(dict(frame=int(ks[-1]), value=float(v[ks[-1]]), ease=None, ease_name=None, err=0.0))
    return keys


def render_keys(keys, n):
    """Rebuild a per-frame curve from keys (for scoring the fit)."""
    out = np.empty(n)
    for k0, k1 in zip(keys[:-1], keys[1:]):
        a, b = k0['frame'], k1['frame']
        x = np.linspace(0, 1, b - a + 1)
        e = k0['ease'] or LIB['linear']
        out[a:b + 1] = k0['value'] + (k1['value'] - k0['value']) * bezier_y(e, x)
    return out
