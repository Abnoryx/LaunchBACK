"""Stage 3 (text): RapidOCR word boxes on frames where the picture changed, linked into word tracks
(text, first/last frame, box over time) -> keyframes + eases per track. Coordinates in 1080-wide pixels."""
import numpy as np
import cv2
from .eases import curve_to_keys

_OCR = None


def _ocr():
    global _OCR
    if _OCR is None:
        from rapidocr import RapidOCR
        _OCR = RapidOCR()
    return _OCR


def ocr_frames(src, mad, cuts, every_max=4, change=1.5, width=720, min_score=0.6):
    """OCR a frame when it changed enough since the last OCR'd one, at every cut, and at least every `every_max`."""
    cap = cv2.VideoCapture(src); i, last, out = 0, -99, {}
    acc = 0.0; cutset = set(cuts)
    while True:
        ok, f = cap.read()
        if not ok: break
        acc += mad[i] if i < len(mad) else 0
        if i - last >= every_max or acc > change or i in cutset or i == 0:
            h, w = f.shape[:2]; k = width / w
            img = cv2.resize(f, (width, int(h * k))) if k != 1 else f
            r = _ocr()(img, return_word_box=True)
            words = []
            for line in (r.word_results or ()):
                items = [line] if line and isinstance(line[0], str) else line
                for item in items:
                    if not isinstance(item, (tuple, list)) or len(item) != 3: continue
                    txt, sc, box = item
                    if sc < min_score or not txt.strip(): continue
                    b = np.array(box, float) * (1080 / width)
                    words.append(dict(t=txt, s=round(float(sc), 3), x0=b[:, 0].min(), y0=b[:, 1].min(), x1=b[:, 0].max(), y1=b[:, 1].max()))
            out[i] = words; last, acc = i, 0.0
        i += 1
    cap.release()
    return out


def _sim(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def track_words(ocr, cuts, n, max_gap=8, max_jump=0.12, min_obs=3, jitter_px=5.0):
    """Link OCR boxes into word tracks (never across a cut): same place (centre within max_jump of the width) and
    similar text (OCR misreads like WONDER/VONDER/NONDER join one track; the most common reading names it).
    Box jitter of a few px is treated as noise when fitting keys (jitter_px), so a still word gets no fake moves."""
    from collections import Counter
    shot_of = np.searchsorted(np.array(cuts), np.arange(n), side='right')
    tracks, live = [], []
    for f in sorted(ocr):
        used = set()
        for w in ocr[f]:
            cx, cy, hh = (w['x0'] + w['x1']) / 2, (w['y0'] + w['y1']) / 2, w['y1'] - w['y0']
            best = None
            for ti, tr in enumerate(live):
                p = tr['obs'][-1]
                if ti in used or shot_of[p[0]] != shot_of[f] or f - p[0] > max_gap: continue
                dist = np.hypot(cx - p[1], cy - p[2]) / 1080
                sim = max(_sim(w['t'], t) for t in tr['texts'][-3:])
                if dist < max_jump and sim >= 0.5:
                    sc = dist - 0.05 * sim
                    if best is None or sc < best[0]: best = (sc, ti)
            if best:
                tr = live[best[1]]; used.add(best[1])
            else:
                tr = dict(texts=[], obs=[], scores=[]); tracks.append(tr); live.append(tr); used.add(len(live) - 1)
            tr['obs'].append((f, cx, cy, hh)); tr['texts'].append(w['t']); tr['scores'].append(w['s'])
        live = [t for t in live if f - t['obs'][-1][0] <= max_gap]
    out = []
    for tr in tracks:
        if len(tr['obs']) < min_obs: continue
        text = Counter(tr['texts']).most_common(1)[0][0]
        if len(text.strip()) < 2 and np.mean(tr['scores']) < 0.95: continue  # lone glyphs are mostly OCR noise
        o = np.array(tr['obs'], float)
        f0, f1 = int(o[0, 0]), int(o[-1, 0])
        fr = np.arange(f0, f1 + 1)
        curves = {k: np.interp(fr, o[:, 0], o[:, j]) for j, k in ((1, 'x'), (2, 'y'), (3, 'size'))}
        keys = {k: curve_to_keys(v, sigma=jitter_px) for k, v in curves.items() if np.ptp(v) > 4 * jitter_px}
        out.append(dict(text=text, first=f0, last=f1, shot=int(shot_of[f0]), samples=len(o), conf=round(float(np.mean(tr['scores'])), 3),
                        at=dict(x=round(o[0, 1]), y=round(o[0, 2]), size=round(o[0, 3])),
                        moves={k: [dict(frame=kk['frame'] + f0, value=round(kk['value'], 1), ease=kk['ease_name'] or kk['ease']) for kk in v]
                               for k, v in keys.items()}))
    return sorted(out, key=lambda t: (t['first'], t['at']['y']))
