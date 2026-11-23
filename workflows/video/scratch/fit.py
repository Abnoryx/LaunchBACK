"""Auto-fitter: nudge element groups (position x/y in world units, scale factor) to maximise SSIM vs the reel.
usage: python3 -I fit.py <scene.json> <comp> <tweaks.json> <port> <frames...>   (render server must be running)
Groups are layer-name prefixes. Tweaks are applied on top of the hand-written scene (see apply())."""
import base64, copy, json, subprocess, sys, urllib.request
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as sw

W, H = 180, 320
REEL = '/home/user/tpl/reels/r1.mp4'


def apply(project, tweaks):
    """tweaks: {group_prefix: {'x': dx, 'y': dy, 's': scale_mult}} applied to every layer whose name starts with prefix."""
    p = copy.deepcopy(project)
    for c in p['comps']:
        for L in c['layers']:
            for g, tw in tweaks.items():
                if not L['name'].startswith(g):
                    continue
                tg = next((q for q in L['props'] if q['m'] == 'ADBE Transform Group'), None)
                if not tg:
                    continue
                for q in tg.get('c', []):
                    if q['m'] == 'ADBE Position':
                        def mv(v): return [v[0] + tw.get('x', 0), v[1] + tw.get('y', 0)] + v[2:]
                        if 'k' in q:
                            for k in q['k']: k['v'] = mv(k['v'])
                            q['v'] = q['k'][0]['v']
                        else:
                            q['v'] = mv(q['v'])
                    if q['m'] == 'ADBE Scale' and tw.get('s', 1) != 1:
                        def sc(v): return [v[0] * tw['s'], v[1] * tw['s']] + v[2:]
                        if 'k' in q:
                            for k in q['k']: k['v'] = sc(k['v'])
                            q['v'] = q['k'][0]['v']
                        else:
                            q['v'] = sc(q['v'])
                if tw.get('s', 1) != 1 and not any(q['m'] == 'ADBE Scale' for q in tg.get('c', [])):
                    tg['c'].append({'n': 'Scale', 'm': 'ADBE Scale', 'v': [100 * tw['s'], 100 * tw['s'], 100]})
    return p


def ssim(x, y):
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    X, Y = sw(x, (7, 7))[::2, ::2], sw(y, (7, 7))[::2, ::2]
    mx, my = X.mean((-1, -2)), Y.mean((-1, -2))
    vx, vy = X.var((-1, -2)), Y.var((-1, -2))
    cxy = ((X - mx[..., None, None]) * (Y - my[..., None, None])).mean((-1, -2))
    return float((((2 * mx * my + C1) * (2 * cxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (vx + vy + C2))).mean())


def reel_frames(ns):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', REEL, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    R = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)
    return [R[n] for n in ns]


def render(port, project, comp, times):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/render', data=json.dumps({'project': project, 'comp': comp, 'times': times, 'w': W, 'h': H}).encode(),
                                 headers={'Content-Type': 'application/json'})
    out = json.loads(urllib.request.urlopen(req, timeout=900).read())
    fr = []
    for b in out['frames']:
        a = np.frombuffer(base64.b64decode(b), np.uint8).reshape(H, W, 4).astype(float)
        fr.append(a[..., :3] @ [0.2126, 0.7152, 0.0722])
    return fr


def main():
    scene, comp, tw_path, port = sys.argv[1:5]
    ns = [int(x) for x in sys.argv[5:]]
    base = json.load(open(scene))
    groups = json.load(open(tw_path)) if tw_path.endswith('.json') and __import__('os').path.exists(tw_path) else {}
    targets = groups.pop('_groups', None) or ['?B', '?A', 'ever', 'WONDER', 'why', 'test drive', 'work so', 'well', 'car.png']
    tweaks = {g: groups.get(g, {'x': 0, 'y': 0, 's': 1}) for g in targets}
    R = reel_frames(ns)
    times = [n / 30 for n in ns]

    def score(tw):
        E = render(port, apply(base, tw), comp, times)
        return float(np.mean([ssim(e, r) for e, r in zip(E, R)]))

    best = score(tweaks)
    print('start', round(best, 4), flush=True)
    steps = {'x': 40.0, 'y': 40.0, 's': 0.08}
    for rnd in range(4):
        improved = False
        for g in targets:
            for prm in ('x', 'y', 's'):
                for sgn in (1, -1):
                    cand = copy.deepcopy(tweaks)
                    cand[g][prm] = cand[g][prm] + sgn * steps[prm]
                    s = score(cand)
                    if s > best + 1e-4:
                        best, tweaks, improved = s, cand, True
                        print(f'r{rnd} {g} {prm}{"+" if sgn > 0 else "-"} -> {best:.4f}', flush=True)
                        json.dump(tweaks, open(tw_path, 'w'), indent=1)
                        break
        for k in steps: steps[k] /= 2
        print('round', rnd, 'best', round(best, 4), 'steps', steps, flush=True)
    json.dump(tweaks, open(tw_path, 'w'), indent=1)
    print('done', round(best, 4))


if __name__ == '__main__':
    main()
