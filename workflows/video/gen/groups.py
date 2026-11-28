"""Scene GROUPS (user rule, 2026-11-24): each group is ONE rescened video. /gen builds a reel from ONE group, using most (>=80%) if not
all of its scenes, the exact shots, in the original order, so the original's cuts and handoffs/transitions between them come along for
free (mixing scenes from different videos made bad transitions and cuts). Only the content changes (text, accent, props) and every bezier
ease becomes the one graph set in gen/config.json `ease` (quad_out) so scenes look like one creator's work.
Groups: each bought reel with private scene templates (/home/user/tpl/lib/<reel>/templates/shot_NN.json) + 'psych' (our code templates
from the Psychology Trick reel, original order S1..S10).
usage: python3 -m gen.groups                         list groups (scenes, seconds, text capacity, previews)
       python3 -m gen.groups <script.txt> [--group G] [--out plan.json]   rank groups for the script, plan the best (or G)"""
import glob, json, os, re, sys
from . import library as LIB, usage as USE
HERE = os.path.dirname(os.path.abspath(__file__)); TPL = LIB.TPL


def scene_info(path):
    t = json.load(open(path))['template']; a, b = t['window']; seen, strings = set(), []
    for x in t['params']['texts']:
        s = x['text'].strip()
        if len(s) > 80 or not s or s in seen: continue   # long fine print / blanks are not content slots
        seen.add(s); strings.append(s)
    return dict(root=t['root'], window=[a, b], seconds=round(b - a, 2), strings=strings, words=sum(len(s.split()) for s in strings))


def groups():
    G = {}
    for d in sorted(glob.glob(f'{TPL}/lib/*/templates')):
        reel = d.split('/')[-2]; sc = []
        for f in sorted(glob.glob(f'{d}/shot_*.json')):
            n = int(re.search(r'shot_(\d+)', f).group(1)); i = scene_info(f); i.update(id=f'{reel}/s{n:02d}', n=n, file=f); sc.append(i)
        if sc: G[reel] = sc
    ours = []
    for sid, e in LIB.shots().items():
        m = re.search(r'reel S(\d+)([ab]?)', e.get('notes', ''))
        if e['kind'] == 'template' and m and not e.get('private'):
            fr = re.search(r'(\d+) frames', e.get('notes', ''))
            ours.append(dict(id=sid, n=int(m.group(1)) * 10 + (ord(m.group(2)) - 96 if m.group(2) else 0), seconds=round(int(fr.group(1)) / 30, 2) if fr else None, strings=[str(w) for w in e.get('words', [])],
                             words=len(' '.join(map(str, e.get('words', []))).split())))
    if ours: G['psych'] = sorted(ours, key=lambda x: x['n'])
    return G


def has_prev(g, sid): return LIB.has_preview(LIB.shots()[sid]) if sid in LIB.shots() else False


def plan(script, G, name):
    words = script.split(); sc = G[name]; C = sum(s['words'] for s in sc) or 1; r = len(words) / C
    out, pos, acc = [], 0, 0.0
    for s in sc:   # allot script words in proportion to each scene's text capacity, snapping to phrase ends
        acc += s['words'] * r; end = min(len(words), int(round(acc))) if s is not sc[-1] else len(words)
        for k in range(end, min(len(words), end + 3)):   # prefer to end a scene on punctuation within +3 words
            if re.search(r'[.:;,?!]$', words[k - 1]): end = k; break
        out.append(dict(scene=s['id'], seconds=s['seconds'], original=s['strings'], text=' '.join(words[pos:end]))); pos = end
    return out


def main(a):
    G = groups(); cfg = json.load(open(os.path.join(HERE, 'config.json')))
    if not a or a[0].startswith('--'):
        for k, sc in G.items(): print(f"{k:8s} {len(sc):3d} scenes  {sum(s['seconds'] or 0 for s in sc):6.1f}s  text capacity {sum(s['words'] for s in sc):4d} words  previews {sum(has_prev(k, s['id']) for s in sc)}/{len(sc)}")
        return
    script = open(a[0]).read(); W = len(script.split()); force = a[a.index('--group') + 1] if '--group' in a else None
    import math; secs = W / cfg.get('words_per_second', 2.6)   # spoken length of the script
    def dist(k):   # 0 = perfect: text capacity matches the script AND the group's runtime matches the speaking time
        cap = max(1, sum(x['words'] for x in G[k])); gs = sum(x['seconds'] or 0 for x in G[k])
        P = plan(script, G, k); fast = sum(1 for q in P if q['seconds'] and len(q['text'].split()) / q['seconds'] > 4) / len(P)   # share of scenes too dense to read
        return 0.5 * abs(math.log(W / cap)) + (abs(math.log(secs / gs)) if gs else 0.5) + fast
    held = {} if '--ignore-cooldown' in a else USE.blocked(); rank = sorted((k for k in G if k not in held), key=dist) or sorted(G, key=dist)
    if held: print(f'cooldown: {", ".join(f"{k} (free again {v})" for k, v in held.items())} not used (same reel twice in a row; user rule 2026-11-28, --ignore-cooldown to override)')
    print(f'script: {W} words = {secs:.0f}s spoken'); [print(f"  {k:8s} {len(G[k]):2d} scenes {sum(x['seconds'] or 0 for x in G[k]):5.1f}s capacity {sum(x['words'] for x in G[k]):4d} words  distance {dist(k):.2f}") for k in rank]
    if force in held: print(f'WARNING: {force} was used recently (free again {held[force]}): the user asked not to reuse a reel twice in a row')
    pick = force or rank[0]; P = plan(script, G, pick)
    res = dict(group=pick, ease=cfg.get('ease', 'quad_out'), keep_original_handoffs=True, scenes=P)
    out = a[a.index('--out') + 1] if '--out' in a else None
    if out: json.dump(res, open(out, 'w'), indent=1)
    print(f'PICK {pick}: {len(P)} scenes, ease {res["ease"]}')
    for p in P:
        wps = len(p['text'].split()) / p['seconds'] if p['seconds'] else 0
        print(f"  {p['scene']:10s} {p['seconds']}s  {p['text'][:62]}" + (f"   <- {wps:.1f} words/s: too fast to read" if wps > 4 else ''))


if __name__ == '__main__': main(sys.argv[1:])
