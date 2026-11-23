"""Rank library templates and assets for a beat, using features + learned stats (approved shots/props rise,
rejected ones sink, recently used ones are penalised so videos don't repeat).
usage: python3 -m gen.shotlist <beats.json> [--world dark|paper]   (prints top 3 templates per beat)
       python3 -m gen.shotlist --assets tyre book        (search the asset index by tags)"""
import json, os, sys
VID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(VID, 'library', 'catalog.json'); IDX = os.path.join(VID, 'library', 'assets', 'index.json')


def prior(st):   # Laplace-smoothed approval rate, -0.15 per rejection
    return (st.get('approved', 0) + 1) / (st.get('picked', 0) + 2) - 0.15 * st.get('rejected', 0)


def features(k, t):
    """Every catalog entry is usable: tagged ones use their 'gen' features, the rest get features derived from the
    catalog fields (e.g. .aep scenes: text/footage slot counts) so nothing in the library is left out."""
    if t.get('gen'): return t['gen']
    sl = t.get('slots', {}); nt = sl.get('texts', len(sl) if isinstance(sl, list) else 3) if isinstance(sl, dict) else len(sl)
    prop = (sl.get('footage', 0) > 0) if isinstance(sl, dict) else any(w in ' '.join(map(str, sl)) for w in ('prop', 'asset', 'model'))
    return dict(world='any', words=[1, max(2, min(6, nt))], hero=False, prop=prop, use=t.get('source', '') + ' ' + t.get('notes', '')[:80],
                stats=dict(picked=0, approved=0, rejected=0))


def rank_templates(beat, world=None, prev=None):
    T = json.load(open(CAT))['templates']; n = len(beat['text'].split()); out = []
    for k, t in T.items():
        g = features(k, t)
        if k == 'logo_reveal': continue
        s = 0.0
        lo, hi = g['words']; s += 1.0 if lo <= n <= hi else -0.5 * min(abs(n - lo), abs(n - hi))
        if world and g['world'] not in (world, 'any'): s -= 0.6
        if beat.get('role') == 'hook' and k == 'hero_word': s += 2.5
        if any(ch.isdigit() for ch in beat['text']) and k == 'calendar_flip': s += 2.5   # numbers/years -> counter
        if beat.get('prop') and g['prop']: s += 0.5
        if k == prev: s -= 2.0                                   # never the same template twice in a row
        s += prior(g['stats']) + 0.3 * (t.get('score', {}).get('ssim_reel') or 0.6)
        out.append((round(s, 2), k, g['use']))
    return sorted(out, reverse=True)


ROOTS = [os.path.join(VID, 'library', 'assets'), '/home/user/tpl/lib']   # our library + the bought .aep libraries
EXT = ('.png', '.jpg', '.jpeg', '.webp', '.glb', '.gltf', '.mp4', '.mov', '.webm', '.svg')


def sync_index():
    """Add every asset file in the library (recursively, incl. bought .aep libraries) to the index; keep stats."""
    I = json.load(open(IDX)) if os.path.exists(IDX) else {}
    for root in ROOTS:
        for d, _, fs in os.walk(root):
            for f in fs:
                if not f.lower().endswith(EXT): continue
                rel = os.path.relpath(os.path.join(d, f), os.path.join(VID, 'library', 'assets')) if root == ROOTS[0] else os.path.join(d, f)
                if rel in I: continue
                kind = '3d' if f.endswith(('.glb', '.gltf')) else 'video' if f.lower().endswith(('.mp4', '.mov', '.webm')) else 'image'
                tags = [x for x in os.path.splitext(rel)[0].replace('-', '_').replace('/', '_').split('_') if x and x not in ('m', 'z', 'src', 'home', 'user', 'tpl', 'lib')]
                I[rel] = dict(kind=kind, tags=tags, private=root != ROOTS[0], stats=dict(used=0, approved=0, rejected=0))
    json.dump(I, open(IDX, 'w'), indent=1)
    return I


def find_assets(tags):
    I = sync_index(); tags = [t.lower() for t in tags]; hits = []
    for f, e in I.items():
        m = sum(any(t in x.lower() for x in e['tags'] + [f.lower()]) for t in tags)
        if m: hits.append((m + prior(e['stats']), f, e.get('kind'), e.get('cutout')))
    return sorted(hits, reverse=True)


if __name__ == '__main__':
    if sys.argv[1] == '--assets':
        for h in find_assets(sys.argv[2:])[:12]: print(h)
    else:
        world = sys.argv[sys.argv.index('--world') + 1] if '--world' in sys.argv else None
        prev = None
        for b in json.load(open(sys.argv[1])):
            r = rank_templates(b, world, prev); prev = r[0][1]
            print(f"{b['text']!r:40} -> " + ' | '.join(f'{k} ({s})' for s, k, _ in r[:3]))
