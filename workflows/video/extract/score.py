"""Scorecard for a run against ground truth (gt/<name>.json) and user corrections (runs/<name>/corrections.json).
Used after every run and by `python3 -m extract.check` to stop changes that make old runs worse."""
import json, os
import numpy as np


def score(bd, m, gt, tol=2):
    out = {}
    got = np.array(m['cuts']) if m['cuts'] else np.array([-999])
    hits = [g for g in gt['cuts'] if np.min(np.abs(got - g)) <= tol]
    out['cut_recall'] = round(len(hits) / len(gt['cuts']), 3)
    out['cut_precision'] = round(sum(1 for c in m['cuts'] if min(abs(c - g) for g in gt['cuts']) <= tol) / max(1, len(m['cuts'])), 3)
    out['cut_missed'] = [g for g in gt['cuts'] if g not in hits]
    if gt.get('transitions'):
        ok, tot = 0, 0
        for g, tags in gt['transitions'].items():
            g = int(g); tot += 1
            near = [c for c in m['cuts'] if abs(c - g) <= tol]
            tr = {str(a): b for a, b in m['transitions'].items()}
            if near and any(t in tr[str(near[0])] for t in tags): ok += 1
        out['transition_tag_hit'] = round(ok / max(tot, 1), 3)
    if gt.get('camera'):
        cam = np.array(m['cam_raw']); k = bd['source']['scale_to_1080']
        n = min(len(cam), len(gt['camera']['dx']))
        cutset = set()
        for c in gt['cuts']: cutset.update(range(c - 3, c + 4))
        idx = [i for i in range(1, n) if i not in cutset and cam[i, 4] > 0.3]
        dx = cam[idx, 0] * k; dy = cam[idx, 1] * k
        gx = np.array(gt['camera']['dx'])[idx]; gy = np.array(gt['camera']['dy'])[idx]
        s = np.sign(np.sum(dx * gx) + np.sum(dy * gy)) or 1  # sign convention (content vs camera) found from data
        err = np.hypot(s * dx - gx, s * dy - gy)
        out['camera_px_err_median'] = round(float(np.median(err)), 2)
        out['camera_px_err_p90'] = round(float(np.percentile(err, 90)), 2)
        moving = np.hypot(gx, gy) > 2
        out['camera_moving_frames_err_median'] = round(float(np.median(err[moving])), 2) if moving.any() else None
        gz = np.array(gt['camera']['dscale'])[idx]; z = cam[idx, 2]
        out['zoom_err_median_pct'] = round(float(np.median(np.abs(z ** s - gz)) * 100), 3)
    return out


def check_corrections(name, runs_dir):
    """User corrections: {"cuts_add":[..], "cuts_remove":[..], "transitions":{"f":[tags]}, "words":{"text":first}}."""
    p = os.path.join(runs_dir, name, 'corrections.json')
    if not os.path.exists(p): return None
    c = json.load(open(p)); m = json.load(open(os.path.join(runs_dir, name, 'measure.json')))
    res = {}
    if 'cuts_add' in c: res['cuts_add_ok'] = all(min([abs(x - f) for x in m['cuts']] or [99]) <= 2 for f in c['cuts_add'])
    if 'cuts_remove' in c: res['cuts_remove_ok'] = all(min([abs(x - f) for x in m['cuts']] or [99]) > 2 for f in c['cuts_remove'])
    if 'transitions' in c:
        res['transitions_ok'] = all(any(t in m['transitions'].get(str(f), []) for t in tags) for f, tags in c['transitions'].items())
    return res
