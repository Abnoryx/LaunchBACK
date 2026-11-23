"""Synthetic benchmark for stage 4 (eases). Random multi-key curves built from library eases + tracking noise.
Scores: key-time error (frames), missed/extra keys, ease-name accuracy. Gate for every change to eases.py.
usage: python3 -m extract.bench_eases [n_curves] [noise_px]"""
import sys, json
import numpy as np
from .eases import LIB, bezier_y, curve_to_keys

NAMES = ['linear', 'quad_out', 'quad_in', 'cubic_out', 'cubic_in', 'cubic_inout', 'expo_out', 'standard', 'pop']


def make_curve(rng, noise):
    v, keys, f = [], [], 0
    val = rng.uniform(-300, 300)
    if rng.random() < 0.5:  # leading hold
        h = int(rng.integers(3, 10)); v += [val] * h; f += h
    for _ in range(int(rng.integers(1, 4))):
        n = int(rng.integers(8, 30)); name = NAMES[int(rng.integers(len(NAMES)))]
        tgt = val + rng.choice([-1, 1]) * rng.uniform(60, 600)
        x = np.linspace(0, 1, n + 1)
        seg = val + (tgt - val) * bezier_y(LIB[name], x)
        keys.append((f if not v else len(v) - 1, name))
        v = v[:-1] + list(seg) if v else list(seg)
        val = tgt; f = len(v) - 1
        if rng.random() < 0.6:
            h = int(rng.integers(3, 10)); v += [val] * h
    keys.append((len(v) - 1, None))
    arr = np.array(v) + rng.normal(0, noise, len(v))
    return arr, keys


def run(n=300, noise=0.3, seed=1):
    rng = np.random.default_rng(seed)
    terr, missed, extra, ok, tot, rms = [], 0, 0, 0, 0, []
    conf = {}
    for _ in range(n):
        v, gt = make_curve(rng, noise)
        got = curve_to_keys(v)
        gf = [k['frame'] for k in got]
        # only moving-segment starts matter for ease scoring; hold starts are free keys
        for (f, name) in gt[:-1]:
            j = int(np.argmin([abs(g - f) for g in gf])); d = abs(gf[j] - f)
            if d > 2: missed += 1; continue
            terr.append(d); tot += 1
            got_name = got[j]['ease_name']
            conf.setdefault(name, {}).setdefault(got_name, 0); conf[name][got_name] += 1
            ok += got_name == name
        moving_gt = len(gt) - 1
        extra += max(0, sum(1 for k in got[:-1] if k['ease_name'] != 'hold') - moving_gt)
    res = dict(curves=n, noise_px=noise, key_err_mean=round(float(np.mean(terr)), 3), key_within_1f=round(float(np.mean(np.array(terr) <= 1)), 3),
               missed=missed, extra_moving_keys=extra, ease_acc=round(ok / max(tot, 1), 3), confusion=conf)
    return res


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    noise = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    print(json.dumps(run(n, noise), indent=1))
