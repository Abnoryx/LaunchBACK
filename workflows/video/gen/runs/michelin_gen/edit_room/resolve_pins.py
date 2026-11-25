"""Resolve Edit Room pins (Auto = the exact layer under the pin, Precise = the point, Frame = the whole frame, plus pins at the cut between scenes).
How Auto works: the render engine's serve mode can show only chosen layers (`only`), so 'which layer owns this pixel' is exact, not guessed: for each candidate
layer (top-most first) render the scene with only that layer (and its precomp parents) and test the pixel's alpha; recurse into precomps.
usage: python3 edit_room/resolve_pins.py <dir with pins/<scene>.json and pins/reel.json (ArtifactData out_dir)> [--out resolved.json]
pin = {id, t (seconds in that clip; for the reel, in the reel), x, y (0..1 of the frame), mode: auto|precise|frame, note, target?}"""
import base64, glob, json, os, re, subprocess, sys, time, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.dirname(HERE); VID = os.path.abspath(os.path.join(RUN, '..', '..', '..')); sys.path.insert(0, VID)
W = os.path.join(RUN, 'work'); PORT = 8765; SZ = (270, 480); CUT_EPS = 0.35; COVER = 0.8
FOOT = ','.join([os.path.join(VID, 'library/assets'), '/home/user/tpl/lib/gen/assets', os.path.join(W, 'footage_red2'), os.path.join(RUN, 'assets_gen', 'out')])


class Engine:
    """one warm engine process per scene project"""
    def __init__(s, n, root, proj=None):
        s.cams = {c['name']: [l['i'] for l in c['layers'] if l.get('type') == 'CameraLayer'] for c in (proj or {}).get('comps', [])}
        s.log = open('/tmp/pick_serve.log', 'w')
        s.p = subprocess.Popen(['node', 'engine/render.mjs', '--project', os.path.join(W, f'proj_{n}.json'), '--footage', FOOT, '--comp', root, '--luts',
                                '/home/user/tpl/lib/gen/assets/luts_red.json', '--serve', str(PORT)], cwd=VID, stdout=s.log, stderr=subprocess.STDOUT); s.root = root
        for _ in range(60):
            if 'serving' in open('/tmp/pick_serve.log').read(): return
            time.sleep(2)
        raise RuntimeError('engine serve did not start')
    def post(s, q):
        r = urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{PORT}/render', json.dumps(q).encode(), {'Content-Type': 'application/json'}), timeout=300); return json.loads(r.read())
    def isolate(s, path, comp, idx):   # path = [(comp name, layer index), ...] of parents that stay on; then only `idx` of `comp`
        s.post({'comp': s.root, 'times': [], 'only': None})
        for c, i in path: s.post({'comp': s.root, 'times': [], 'only': [i] + s.cams.get(c, []), 'only_comp': c})   # cameras stay on: 3D layers need them
        s.post({'comp': s.root, 'times': [], 'only': list(idx) + s.cams.get(comp, []), 'only_comp': comp})
    def mask(s, path, comp, idx, t):   # one render per (layer, time), shared by every pin at that time
        k = (tuple(path), comp, tuple(idx), round(t, 3)); c = s.__dict__.setdefault('cache', {})
        if k not in c: s.isolate(list(path), comp, idx); c[k] = s.alpha(t)
        return c[k]
    def alpha(s, t): return np.frombuffer(base64.b64decode(s.post({'comp': s.root, 'times': [t], 'w': SZ[0], 'h': SZ[1]})['frames'][0]), np.uint8).reshape(SZ[1], SZ[0], 4)[..., 3] > 48
    def close(s): s.post({'comp': s.root, 'times': [], 'only': None}); s.p.kill(); s.p.wait(); time.sleep(1)


def candidates(comp):
    return sorted([l for l in comp['layers'] if l.get('enabled') is True and not l.get('adjustment_layer') and l.get('type') != 'CameraLayer'
                   and not l['name'].lower().startswith(('null', 'primary null'))], key=lambda l: l['i'])


def chain_of(comp, l):   # the layer plus its parent chain (parents carry its transform)
    by = {x['i']: x for x in comp['layers']}; out = [l['i']]; p = l.get('parent')
    while p is not None and p in by and p not in out: out.append(p); p = by[p].get('parent')
    return out


def descend(eng, proj, comp, t, px, py, path=(), depth=0):
    """-> (chain of layers, bbox 0..1) of the top-most layer under (px, py), recursing into precomps"""
    byid = {c['id']: c for c in proj['comps']}; fallback = None
    for l in candidates(comp):
        a = eng.mask(path, comp['name'], tuple(chain_of(comp, l)), t)
        if a.mean() > COVER and l.get('src_type') != 'CompItem':   # paper textures / full-frame backdrops are not what a pin means; remember as fallback
            fallback = fallback or (l, a); continue
        if not a[max(0, py - 1):py + 2, max(0, px - 1):px + 2].any(): continue
        node = {'comp': comp['name'], 'layer': l['i'], 'name': l['name'], 'type': l.get('type')}
        if l.get('text'): node['text'] = l['text']['text']
        if l.get('src_type') == 'FootageItem':
            fo = next((f for f in proj['footage'] if f['id'] == l['src_id']), {}); node['footage'] = {'id': fo.get('id'), 'name': fo.get('name'), 'file': os.path.basename(str(fo.get('file') or ''))}
        ys, xs = np.where(a); bbox = [round(xs.min() / SZ[0], 3), round(ys.min() / SZ[1], 3), round((xs.max() + 1) / SZ[0], 3), round((ys.max() + 1) / SZ[1], 3)]
        if l.get('src_type') == 'CompItem' and depth < 3 and l['src_id'] in byid:
            inner = descend(eng, proj, byid[l['src_id']], t, px, py, tuple(path) + ((comp['name'], l['i']),), depth + 1)
            if inner[0]: return [node] + inner[0], inner[1]
        return [node], bbox
    if fallback and depth > 0:   # only a backdrop is under the pin: name it so the note still has a target
        l, a = fallback; return [{'comp': comp['name'], 'layer': l['i'], 'name': l['name'] + ' (backdrop)', 'type': l.get('type')}], [0, 0, 1, 1]
    return [], None


def scenes():   # one row per rendered scene, from the render manifest: (label, [from, to], root comp, seconds)
    m = json.load(open(os.path.join(W, 'manifest.json')))
    return [(e['label'], (e['from'], e['to']), e['comp'], round(e['to'] - e['from'], 2)) for e in m['entries']]


def locate(reel_t, S):   # reel seconds -> (scene index, local t, between)
    acc = 0.0
    for i, (sid, win, root, sec) in enumerate(S):
        dur = win[1] - win[0]
        if reel_t < acc + dur or i == len(S) - 1:
            local = reel_t - acc; between = None
            if local < CUT_EPS and i > 0: between = (i - 1, i)
            elif dur - local < CUT_EPS and i < len(S) - 1: between = (i, i + 1)
            return i, local, between
        acc += dur


def link(sid, chain):   # layer -> the text slot / footage swap it belongs to
    slots = json.load(open(os.path.join(RUN, 'slots.json'))).get(sid, {}); out = []
    for n in chain:
        if n.get('text') is not None:
            t = n['text'].strip(); out += [f"text slot {k!r} (now {v!r})" for k, v in slots.items() if v.strip() == t][:1]
        if n.get('footage'): out.append(f"footage id {n['footage']['id']} {n['footage']['name']!r} (file {n['footage']['file']})")
    return out


def main(src, out=None):
    S = scenes(); work = {}   # scene index -> [(pin, local t)]
    for f in sorted(glob.glob(os.path.join(src, '**', '*.json'), recursive=True)):
        name = os.path.basename(f)[:-5]; d = json.load(open(f)); d = d.get('data', d)
        for p in d.get('pins') or []:
            if name == 'reel':
                i, local, between = locate(p['t'], S)
            else:
                i = int(re.sub(r'\D', '', name)) - 1; local, between = p['t'], None
            work.setdefault(i, []).append((dict(p, scene=S[i][0], source=name, between=[S[b][0] for b in between] if between else None), local))
    results = []
    for i in sorted(work):
        sid, win, root, _ = S[i]; n = sid; proj = json.load(open(os.path.join(W, f'proj_{n}.json'))); comp = next(c for c in proj['comps'] if c['name'] == root)
        auto = [(p, l) for p, l in work[i] if p.get('mode', 'auto') in ('auto', 'precise')]
        eng = Engine(n, root, proj) if auto else None
        for p, local in work[i]:
            r = {'pin': p['id'], 'scene': sid, 'comp_time': round(win[0] + local, 3), 'mode': p.get('mode', 'auto'), 'note': p.get('note', ''), 'between': p['between'], 'target': p.get('target', ''), 'x': p.get('x'), 'y': p.get('y')}
            if p.get('mode', 'auto') == 'frame': r['selection'] = 'the whole frame'
            else:
                px, py = int(p['x'] * (SZ[0] - 1)), int(p['y'] * (SZ[1] - 1)); chain, bbox = descend(eng, proj, comp, win[0] + local, px, py)
                r['layers'] = [f"{c['comp']}/{c['name']}" for c in chain]; r['links'] = link(sid, chain); r['bbox'] = bbox
                r['selection'] = ('layer ' + chain[-1]['name'] + (f" (text {chain[-1]['text']!r})" if chain and chain[-1].get('text') else '')) if (chain and p.get('mode', 'auto') == 'auto') else (f"point ({p['x']:.2f}, {p['y']:.2f})" + (f" on {chain[-1]['name']}" if chain else ''))
                if not chain and p.get('mode', 'auto') == 'auto': r['selection'] = 'nothing owns this pixel (baked footage): treat as a point'
            results.append(r)
        if eng: eng.close()
    if out: json.dump(results, open(out, 'w'), indent=1, ensure_ascii=False)
    for r in results: print(f"pin {r['pin']} | {r['scene']} @ {r['comp_time']}s | {r['mode']} | {r['selection']}" + (f" | between {r['between'][0]} -> {r['between'][1]}" if r['between'] else '') + (f" | links: {r['links']}" if r.get('links') else '') + f" | note: {r['note']}")
    return results


if __name__ == '__main__':
    a = sys.argv[1:]; main(a[0], a[a.index('--out') + 1] if '--out' in a else None)
