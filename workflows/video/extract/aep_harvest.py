"""Route A step 3: gather every asset a dumped project uses into /home/user/tpl/lib/<name>/assets + manifest.json.
usage: python3 -m extract.aep_harvest <dump.json> <footage_dir> <name>
Footage is hard-linked (no extra disk; the zip in tpl/zips stays the backup). Fonts are checked against the engine's
font map: a font that falls back to the generic stand-in is listed as missing. Nothing is silently substituted."""
import sys, os, re, json, hashlib, unicodedata, subprocess, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, '..', 'engine')


def sha1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def fonts_mapped(names):
    js = ("import {mapFont} from './text.js'; const xs = JSON.parse((await import('fs')).default.readFileSync(0,'utf8'));"
          "process.stdout.write(JSON.stringify(xs.map((x) => mapFont(x))));")
    r = subprocess.run(['node', '--input-type=module', '-e', js], input=json.dumps(names), capture_output=True, text=True, cwd=ENGINE)
    if r.returncode: raise SystemExit(r.stderr)
    return json.loads(r.stdout)


def main(dump, footage_dir, name):
    d = json.load(open(dump))
    out = f'/home/user/tpl/lib/{name}'; os.makedirs(f'{out}/assets', exist_ok=True)
    files = {}
    for root, _, fs in os.walk(footage_dir):
        for f in fs:   # zip tools store non-ASCII names as #UXXXX, and astral ones (emoji) as #LXXXXXX
            k = re.sub(r'#L([0-9A-Fa-f]{6})', lambda m: chr(int(m.group(1), 16)), f)
            k = unicodedata.normalize('NFC', re.sub(r'#U([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), k))
            files.setdefault(k, os.path.join(root, f))
    # which comps use each footage item (directly)
    used = collections.defaultdict(set)
    for c in d['comps']:
        for l in c['layers']:
            if l.get('src_type') == 'FootageItem' and l.get('enabled') is True: used[l['src_id']].add(c['name'])
    items, missing = [], []
    for f in d['footage']:
        if not f.get('file'): continue   # solids, placeholders
        base = unicodedata.normalize('NFC', os.path.basename(f['file'].replace('\\', '/')))
        src = files.get(base)
        rec = {'id': f['id'], 'name': f['name'], 'file': base, 'used_by': sorted(used.get(f['id'], [])), 'type': os.path.splitext(base)[1].lower()}
        if not src:
            (missing if rec['used_by'] else items).append({**rec, 'status': 'missing' if rec['used_by'] else 'missing (unused)'}); continue
        dst = f'{out}/assets/{base}'
        if not os.path.exists(dst):
            try: os.link(src, dst)
            except OSError: import shutil; shutil.copy2(src, dst)
        items.append({**rec, 'path': dst, 'bytes': os.path.getsize(dst), 'sha1': sha1(dst)})
    fonts = collections.defaultdict(set)
    for c in d['comps']:
        for l in c['layers']:
            t = l.get('text')
            if not t or l.get('enabled') is not True: continue
            for fn in {t.get('font')} | {r.get('font') for r in t.get('runs', [])}:
                if fn: fonts[fn].add(c['name'])
    names = sorted(fonts); mapped = fonts_mapped(names)
    font_rec = [{'font': n, 'engine_family': m['family'], 'weight': m.get('weight'), 'used_by': sorted(fonts[n]),
                 'status': 'stand-in (missing)' if m['family'] == 'Inter Variable' and 'Inter' not in n else 'mapped'} for n, m in zip(names, mapped)]
    man = {'project': name, 'dump': dump, 'footage': items, 'missing_footage': missing, 'fonts': font_rec}
    json.dump(man, open(f'{out}/manifest.json', 'w'), indent=1)
    print(f'footage: {len(items)} linked, {len(missing)} missing (used)')
    for m in missing: print('  MISSING', m['file'], '<-', ', '.join(m['used_by'][:4]))
    print(f'fonts: {len(font_rec)}')
    for f in font_rec: print(f"  {f['status']:<20} {f['font']:<34} -> {f['engine_family']}  ({len(f['used_by'])} comps)")


if __name__ == '__main__':
    main(*sys.argv[1:4])
