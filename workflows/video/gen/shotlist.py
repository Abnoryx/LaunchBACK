"""Rank library templates and assets for a beat, using features + learned stats (approved shots/props rise,
rejected ones sink, recently used ones are penalised so videos don't repeat).
usage: python3 -m gen.shotlist <beats.json> [--world dark|paper]   (prints top 3 templates per beat)
       python3 -m gen.shotlist --assets tyre book        (search the asset index by tags)"""
import json, os, sys
VID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(VID, 'library', 'catalog.json'); IDX = os.path.join(VID, 'library', 'assets', 'index.json')


def prior(st):   # Laplace-smoothed approval rate, -0.15 per rejection
    return (st.get('approved', 0) + 1) / (st.get('picked', 0) + 2) - 0.15 * st.get('rejected', 0)


def rank_templates(beat, world=None, prev=None):
    T = json.load(open(CAT))['templates']; n = len(beat['text'].split()); out = []
    for k, t in T.items():
        g = t.get('gen')
        if not g or k == 'logo_reveal': continue
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


def find_assets(tags):
    I = json.load(open(IDX)); tags = [t.lower() for t in tags]; hits = []
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
