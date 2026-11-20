"""Regression gate: re-score the ease benchmark, every run with ground truth, and every run with user corrections.
A change to extract/ is kept only if nothing got worse than the stored baseline (extract/baseline.json).
usage: python3 -m extract.check            (compare to baseline)
       python3 -m extract.check --accept   (store the current numbers as the new baseline)
Note: re-scoring reuses each run's measure.json; delete it (or pass --remeasure) to re-run the stages."""
import json, os, sys
import numpy as np
from . import bench_eases, score as SC
from .measure import measure

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, 'runs')
HIGHER = ('cut_recall', 'cut_precision', 'transition_tag_hit', 'ease_acc', 'key_within_1f')
LOWER = ('camera_px_err_median', 'camera_moving_frames_err_median', 'zoom_err_median_pct', 'key_err_mean')


def current(remeasure=False):
    res = {'eases@0.3': bench_eases.run(150, 0.3), 'eases@1.0': bench_eases.run(150, 1.0)}
    for r in res.values(): r.pop('confusion', None)
    for name in sorted(os.listdir(RUNS)) if os.path.isdir(RUNS) else []:
        d = os.path.join(RUNS, name); gt = os.path.join(HERE, 'gt', f'{name}.json')
        if not os.path.exists(os.path.join(d, 'breakdown.json')): continue
        bd = json.load(open(os.path.join(d, 'breakdown.json')))
        if remeasure and os.path.exists(os.path.join(d, 'frames.npy')):
            m = measure(np.load(os.path.join(d, 'frames.npy')), bd['source']['scale_to_1080'])
        else:
            m = json.load(open(os.path.join(d, 'measure.json')))
        if os.path.exists(gt): res[f'gt:{name}'] = SC.score(bd, m, json.load(open(gt)))
        c = SC.check_corrections(name, RUNS)
        if c is not None: res[f'corrections:{name}'] = c
    return res


def compare(base, cur):
    worse = []
    for k, r in cur.items():
        b = base.get(k, {})
        for m, v in r.items():
            if m not in b or v is None or b[m] is None: continue
            if m in HIGHER and v < b[m] - 1e-9: worse.append(f'{k}.{m}: {b[m]} -> {v}')
            if m in LOWER and v > b[m] * 1.05 + 1e-6: worse.append(f'{k}.{m}: {b[m]} -> {v}')
            if isinstance(v, bool) and b[m] is True and v is False: worse.append(f'{k}.{m}: was passing, now failing')
    return worse


if __name__ == '__main__':
    cur = current('--remeasure' in sys.argv)
    bp = os.path.join(HERE, 'baseline.json')
    if '--accept' in sys.argv or not os.path.exists(bp):
        json.dump(cur, open(bp, 'w'), indent=1); print('baseline stored'); print(json.dumps(cur, indent=1)); sys.exit(0)
    worse = compare(json.load(open(bp)), cur)
    print(json.dumps(cur, indent=1))
    print('WORSE:\n' + '\n'.join(worse) if worse else 'OK: nothing got worse than the baseline')
    sys.exit(1 if worse else 0)
