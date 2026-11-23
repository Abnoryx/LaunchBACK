"""Library auto-discovery: every run scans the whole library, so anything added later is usable with no registering.
Everything found is approved. Nothing here reads scores, status or approval stats (they must not bias shot choice).
Shots:  library/templates/*.py (ours), library/catalog.json templates, bought .aep scenes
        /home/user/tpl/lib/<reel>/templates/shot_NN.json (id <reel>/sNN, private: use, never commit).
Assets: library/assets/** and /home/user/tpl/lib/**/assets/** (private).
usage: python3 -m gen.library            (list every shot + whether it has a preview)
       python3 -m gen.library --assets tyre book   (search every asset by name/notes)"""
import glob, importlib, json, os, re, sys
VID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, VID)
CAT = os.path.join(VID, 'library', 'catalog.json')
TPL = '/home/user/tpl'
PREV = os.path.join(VID, 'library', 'previews')      # ours (committed)
PREV_PRIVATE = os.path.join(TPL, 'previews')          # bought scenes (private Kaggle backup only)
ASSET_ROOTS = [os.path.join(VID, 'library', 'assets')] + sorted(glob.glob(os.path.join(TPL, 'lib', '*', 'assets')))
EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.glb', '.gltf', '.mp4', '.mov', '.webm', '.svg')
NUMERIC = re.compile(r'counter|number|year|calendar|count\b', re.I)   # in notes; digits count only in on-screen words


def _catalog():
    return json.load(open(CAT)) if os.path.exists(CAT) else {}


def _ours(name):
    """A hand-built template module: on-screen words from its DEFAULTS, description from its docstring."""
    try: m = importlib.import_module(f'library.templates.{name}')
    except Exception as e: return dict(words=[], notes=f'(import failed: {e})', prop=False, hero=False)
    D = getattr(m, 'DEFAULTS', {}) or {}; W = D.get('words', {}) if isinstance(D.get('words'), dict) else {}
    words = [str(v) for v in W.values() if str(v).strip()] + ([D['mark']] if isinstance(D.get('mark'), str) else [])
    doc = ' '.join((m.__doc__ or '').split())
    return dict(words=words, notes=doc, prop=any(k in D for k in ('prop', 'model', 'props')),
                hero=any(k in W for k in ('hero', 'big')) or bool(re.search(r'giant|hero word', doc, re.I)))


def _bought(path):
    """A bought .aep scene template (extract.aep_template): its own texts, sizes and footage."""
    t = json.load(open(path)).get('template', {}); p = t.get('params', {})
    texts = list(dict.fromkeys(x['text'].strip() for x in p.get('texts', []) if x.get('text', '').strip()))
    big = [x for x in p.get('texts', []) if x.get('size', 0) >= 200 and len(x.get('text', '').split()) <= 1]
    media = [f for f in p.get('footage', []) if not f.get('name', '').lower().endswith(('.mp3', '.wav'))]
    return dict(words=texts, notes=f"{t.get('source', '')}", prop=bool(media), hero=bool(big), window=t.get('window'))


def shots():
    """id -> {id, kind, file, private, words, notes, prop, hero, numeric, capacity, buildable, preview}."""
    C = _catalog().get('templates', {}); S = {}
    for f in sorted(glob.glob(os.path.join(VID, 'library', 'templates', '*.py'))):
        n = os.path.splitext(os.path.basename(f))[0]
        if n.startswith('_'): continue
        S[n] = dict(id=n, kind='template', file=os.path.relpath(f, VID), private=False, **_ours(n))
    for f in sorted(glob.glob(os.path.join(TPL, 'lib', '*', 'templates', 'shot_*.json'))):
        reel = f.split(os.sep)[-3]; k = f"{reel}/s{re.search(r'shot_(\d+)', f).group(1)}"
        S[k] = dict(id=k, kind='aep_scene', file=f, private=True, reel=reel, **_bought(f))
    for k, t in C.items():   # catalog entries add their notes; entries whose files aren't here are still listed
        e = S.setdefault(k, dict(id=k, kind=t.get('kind', 'template'), file=t.get('file', ''), private=str(t.get('file', '')).startswith('tpl:'),
                                 words=[], notes='', prop=False, hero=False, window=t.get('window')))
        if k.count('/') == 1 and t.get('kind') == 'aep_scene': e.setdefault('reel', k.split('/')[0])
        extra = ' '.join(x for x in (t.get('notes', ''), (t.get('gen') or {}).get('use', ''), t.get('source', '')) if x)
        if extra and extra not in e['notes']: e['notes'] = (e['notes'] + ' ' + extra).strip()
    for e in S.values():
        e['numeric'] = any(ch.isdigit() for w in e['words'] for ch in w) or bool(NUMERIC.search(e['notes']))
        e['capacity'] = sum(len(w.split()) for w in e['words'])
        e['preview'] = preview(e['id'], e['private'])
    return S


def preview(sid, private):
    """Base path of a shot's preview (<base>.mp4 + <base>.jpg = 3 key frames side by side)."""
    return os.path.join(PREV_PRIVATE if private else PREV, sid)


def has_preview(e): return os.path.exists(e['preview'] + '.mp4') and os.path.exists(e['preview'] + '.jpg')


def describe(e):
    """The two short captions CLIP embeds for a shot (it matches short captions best): its on-screen words, and its
    notes with bookkeeping (reel/frame/scene references) stripped. Either can be ''."""
    words = ' / '.join(dict.fromkeys(w.replace('\n', ' ').strip() for w in e['words']))[:300]
    n = re.sub(r"Template '[^']*'|\((?:reel|ours)[^)]*\)|\b(?:Stop|Sells|[A-Z]\w*) reel scene \d+|\breel S\w+|\bscene \d+\b|"
               r"\bf\d+(?:-\d+)?\b|\d+ frames|idk[^.]*", ' ', e['notes'])
    notes = ' '.join(n.replace(':', ' ').split()).strip(' .,;-')[:300]
    return words, notes


def assets():
    """rel path -> {kind, tags, private, notes}. Tags come from the path; notes from the catalog when it has any."""
    A = _catalog().get('assets', {}); out = {}
    for root in ASSET_ROOTS:
        private = not root.startswith(VID)
        for d, _, fs in os.walk(root):
            for f in fs:
                if not f.lower().endswith(EXT): continue
                p = os.path.join(d, f); rel = os.path.relpath(p, root) if not private else p
                kind = '3d' if f.endswith(('.glb', '.gltf')) else 'video' if f.lower().endswith(('.mp4', '.mov', '.webm', '.gif')) else 'image'
                tags = [x for x in re.split(r'[-_/ .]+', os.path.splitext(os.path.relpath(p, root))[0].lower()) if len(x) > 1]
                c = A.get(rel) or A.get(f"{p.split(os.sep)[-3]}/{f}" if private else rel) or {}
                c = c if isinstance(c, dict) else dict(use=c)
                out[rel] = dict(kind=kind, tags=tags, private=private, notes=' '.join(str(c.get(k, '')) for k in ('use', 'made_by')).strip())
    return out


def find_assets(tags):
    tags = [t.lower() for t in tags]; hits = []
    for f, e in assets().items():
        hay = ' '.join(e['tags']) + ' ' + f.lower() + ' ' + e['notes'].lower()
        m = sum(t in hay for t in tags)
        if m: hits.append((m, f, e['kind'], 'private' if e['private'] else 'ours'))
    return sorted(hits, key=lambda h: (-h[0], h[1]))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--assets':
        for h in find_assets(sys.argv[2:])[:20]: print(h)
    else:
        S = shots(); n = sum(map(has_preview, S.values()))
        for k, e in S.items():
            print(f"{k:22} {e['kind']:10} {'preview' if has_preview(e) else 'NO PREVIEW':10} cap={e['capacity']:<3} "
                  f"{'hero ' if e['hero'] else ''}{'num ' if e['numeric'] else ''}{'prop' if e['prop'] else ''}")
        print(f'{len(S)} shots, {n} with previews; {len(assets())} assets')
