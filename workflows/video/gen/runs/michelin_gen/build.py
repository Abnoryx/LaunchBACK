"""Michelin reel from the Generation Effect group (gen): the 19 scenes, exact windows, original order. Per scene:
extract.aep_template apply (texts from slots.json, accent red, ease quad_out, third-party imagery -> neutral), then a Kaggle manifest.
usage: python3 gen/runs/michelin_gen/build.py [preview|final]   -> work/manifest.json for kgl.render_multi"""
import json, os, re, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.abspath(os.path.join(HERE, '..', '..', '..')); sys.path.insert(0, VID)
W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True)
TPL = '/home/user/tpl/lib/gen'; ASSETS = os.path.join(VID, 'library', 'assets'); BLANK = os.path.join(ASSETS, 'blank.png')
LED = f'{TPL}/assets/led.jpg'   # neutral grey gradient, stands in for photos/wallpapers
cfg = json.load(open(os.path.join(VID, 'gen', 'config.json'))); EASE = cfg.get('ease', 'quad_out')
# third-party marks, mascots, people, platform UI: swapped for neutral assets (brand care). Matched on footage name.
BRAND = re.compile(r'iphone|micheal jordan|saquon|nike|whatsapp|vecteezy|instagram|earnera|IMG_0264|Untitled design|icons\.png|blue tick|^e7650458|d81203|windows xp|clippy', re.I)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'preview'
EXTRA = '--samples 1 --preview 540' if OUT == 'preview' else '--samples 4'
slots = json.load(open(os.path.join(HERE, 'slots.json'))); entries = []; unmapped = {}
for f in sorted(glob.glob(f'{TPL}/templates/shot_*.json')):
    n = int(re.search(r'shot_(\d+)', f).group(1)); sid = f'gen/s{n:02d}'; t = json.load(open(f))['template']; m = slots[sid]; texts = {}
    for x in t['params']['texts']:
        k = x['text'].strip()
        if k in m: texts[x['id']] = x['text'].replace(k, m[k]) if k else x['text']
        else: texts[x['id']] = ' '; unmapped.setdefault(sid, set()).add(k[:40])   # fine print / unlisted slot: blanked
    foot = {str(x['id']): (LED if re.search(r'wallpaper', x['name'], re.I) else BLANK) for x in t['params']['footage'] if BRAND.search(x['name'])}
    pj = os.path.join(W, f'params_{n:02d}.json'); json.dump(dict(texts=texts, accent='#E10600', ease=EASE, footage=foot), open(pj, 'w'))
    out = os.path.join(W, f'proj_{n:02d}.json')
    r = subprocess.run([sys.executable, '-m', 'extract.aep_template', 'apply', f, pj, out], cwd=VID, capture_output=True, text=True); print(sid, r.stdout.strip().split('\n')[0][:90])
    a, b = t['window']; entries.append(dict(project=out, comp=t['root'], **{'from': a, 'to': b}, label=f'{n:02d}', footage=['gen'], extra=f"{EXTRA} --luts footage/gen/luts.json"))
json.dump(dict(footage={'gen': f'{TPL}/assets'}, entries=entries, fps=30), open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
print(len(entries), 'scenes', round(sum(e['to'] - e['from'] for e in entries), 1), 's;', 'blanked (fine print/unlisted):', {k: sorted(v) for k, v in unmapped.items()})
