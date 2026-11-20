"""/rescene orchestrator: reel -> runs/<name>/ (info, measure, ocr, breakdown.json, storyboard.jpg, score.json).
usage: python3 -m extract.run <video> <name> [--no-text] [--gt extract/gt/<name>.json]
Stages already done for a run are reused (delete the file to redo it)."""
import argparse, json, os, time
import numpy as np
from .ingest import ingest
from .measure import measure
from .eases import curve_to_keys
from . import score as SC

HERE = os.path.dirname(os.path.abspath(__file__))


def camera_keys(shot):
    c = shot['cam']; out = {}
    for k, v in (('x', c['x']), ('y', c['y']), ('zoom', c['zoom']), ('roll', c['roll'])):
        v = np.asarray(v)
        if k == 'zoom': v = 100 * v
        thr = {'x': 8, 'y': 8, 'zoom': 2, 'roll': 1.5}[k]
        if np.ptp(v) < thr: continue
        keys = curve_to_keys(v)
        out[k] = [dict(frame=q['frame'] + shot['start'], value=round(q['value'], 2), ease=q['ease_name'] or q['ease']) for q in keys]
    return out


def breakdown(info, m, words):
    shots = []
    for s in m['shots']:
        sw = [w for w in words if w['shot'] == s['index']] if words else []
        shots.append(dict(shot=s['index'], start=s['start'], end=s['end'], frames=s['frames'], seconds=round(s['frames'] / info['fps'], 2),
                          transition_in=s['trans_in'], camera=camera_keys(s),
                          camera_confidence=round(float(np.mean(s['cam']['inliers'][1:])) if s['frames'] > 1 else 0, 2),
                          words=[dict(text=w['text'], first=w['first'], last=w['last'], at=w['at'], moves=w['moves']) for w in sw],
                          luma=round(float(np.mean(m['signals']['luma'][s['start']:s['end'] + 1])), 1)))
    return dict(source=info, cuts=m['cuts'], shots=shots, archetype=None)


def storyboard(fr, bd, path, per=6, tw=108):
    from PIL import Image, ImageDraw
    th = int(fr.shape[1] * tw / fr.shape[2])
    rows = bd['shots']
    sheet = Image.new('RGB', (per * tw + 150, len(rows) * (th + 4)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for r, s in enumerate(rows):
        idx = np.linspace(s['start'], s['end'], per).astype(int)
        for j, i in enumerate(idx):
            sheet.paste(Image.fromarray(fr[i]).resize((tw, th)), (j * tw, r * (th + 4)))
            d.text((j * tw + 2, r * (th + 4) + 2), str(i), fill=(255, 0, 0))
        txt = f"S{s['shot']} f{s['start']}-{s['end']}\n{','.join(s['transition_in'])}\ncam:{','.join(s['camera']) or '-'}\n" + \
              '\n'.join(w['text'] for w in s['words'][:6])
        d.text((per * tw + 4, r * (th + 4) + 2), txt, fill=(230, 230, 230))
    sheet.save(path, quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('name')
    ap.add_argument('--no-text', action='store_true'); ap.add_argument('--gt', default=None)
    a = ap.parse_args()
    out = os.path.join(HERE, 'runs', a.name); os.makedirs(out, exist_ok=True)
    T = {}
    t = time.time()
    if os.path.exists(f'{out}/frames.npy'):
        info, fr = json.load(open(f'{out}/info.json')), np.load(f'{out}/frames.npy')
    else:
        info, fr = ingest(a.video, out); info = {k: v for k, v in info.items() if k != 'pts'}
    T['ingest'] = round(time.time() - t, 1); t = time.time()
    if os.path.exists(f'{out}/measure.json'): m = json.load(open(f'{out}/measure.json'))
    else: m = measure(fr, info['scale_to_1080']); json.dump(m, open(f'{out}/measure.json', 'w'))
    T['measure'] = round(time.time() - t, 1); t = time.time()
    words = []
    if not a.no_text:
        from .text import ocr_frames, track_words
        if os.path.exists(f'{out}/ocr.json'): o = {int(k): v for k, v in json.load(open(f'{out}/ocr.json')).items()}
        else:
            o = ocr_frames(a.video, m['signals']['mad'], m['cuts'])
            json.dump(o, open(f'{out}/ocr.json', 'w'), default=float)
        words = track_words(o, m['cuts'], len(fr))
    T['text'] = round(time.time() - t, 1)
    bd = breakdown(info, m, words); bd['timing_s'] = T
    json.dump(bd, open(f'{out}/breakdown.json', 'w'), indent=1)
    storyboard(fr, bd, f'{out}/storyboard.jpg')
    gt = a.gt or os.path.join(HERE, 'gt', f'{a.name}.json')
    if os.path.exists(gt):
        sc = SC.score(bd, m, json.load(open(gt)))
        json.dump(sc, open(f'{out}/score.json', 'w'), indent=1); print(json.dumps(sc, indent=1))
    print(out, T)


if __name__ == '__main__':
    main()
