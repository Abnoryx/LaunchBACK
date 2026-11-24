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
# bands=[[75, 320]]: greens, cyans, blues, purples -> the red accent; yellow/orange stay (user: 'make it red coloured')
BRAND = re.compile(r'iphone|micheal jordan|saquon|nike|whatsapp|vecteezy|instagram|earnera|IMG_0264|Untitled design|icons\.png|blue tick|^e7650458|d81203|windows xp|clippy', re.I)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'preview'
EXTRA = '--samples 1 --preview 540' if OUT == 'preview' else '--samples 4'
from PIL import Image, ImageSequence
import numpy as np
RED = os.path.join(W, 'footage_red'); os.makedirs(RED, exist_ok=True)
def to_red(im):   # greens/cyans/blues/purples (hue 75-320, saturation > 0.25) -> red hue; lightness, saturation, alpha kept
    a = im.convert('RGBA'); hsv = np.array(a.convert('RGB').convert('HSV')); h = hsv[..., 0].astype(float) * 360 / 255
    m = (hsv[..., 1] > 64) & (h >= 75) & (h <= 320); hsv[..., 0][m] = 251
    out = Image.fromarray(hsv, 'HSV').convert('RGB').convert('RGBA'); out.putalpha(a.getchannel('A')); return out
def red_copy(fid, path):
    ext = path.rsplit('.', 1)[-1].lower(); out = os.path.join(RED, f'red_{fid}.{"gif" if ext == "gif" else "png"}')
    if os.path.exists(out): return out
    im = Image.open(path)
    if ext == 'gif':
        fr = [to_red(f.copy()) for f in ImageSequence.Iterator(im)]; fr[0].save(out, save_all=True, append_images=fr[1:], loop=0, duration=im.info.get('duration', 40), disposal=2, transparency=0)
    else: to_red(im).save(out)
    return out
def inband(path):
    im = Image.open(path).convert('RGBA'); im.thumbnail((120, 120)); hsv = np.array(im.convert('RGB').convert('HSV')); m = np.array(im.getchannel('A')) > 50
    if not m.any(): return 0
    h = hsv[..., 0].astype(float) * 360 / 255; return float(((hsv[..., 1] > 64) & (h >= 75) & (h <= 320))[m].mean())
slots = json.load(open(os.path.join(HERE, 'slots.json'))); entries = []; unmapped = {}
for f in sorted(glob.glob(f'{TPL}/templates/shot_*.json')):
    n = int(re.search(r'shot_(\d+)', f).group(1)); sid = f'gen/s{n:02d}'; t = json.load(open(f))['template']; m = slots[sid]; texts = {}
    for x in t['params']['texts']:
        k = x['text'].strip()
        if k in m: texts[x['id']] = x['text'].replace(k, m[k]) if k else x['text']
        else: texts[x['id']] = ' '; unmapped.setdefault(sid, set()).add(k[:40])   # fine print / unlisted slot: blanked
    foot = {str(x['id']): (LED if re.search(r'wallpaper', x['name'], re.I) else BLANK) for x in t['params']['footage'] if BRAND.search(x['name'])}
    for x in t['params']['footage']:   # still images that are mostly green/blue/purple -> red copies (user: make it red coloured)
        pth = os.path.join(TPL, 'assets', x['name'])
        if str(x['id']) not in foot and x['name'].lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'gif') and os.path.exists(pth) and inband(pth) > 0.15: foot[str(x['id'])] = red_copy(x['id'], pth)
    pj = os.path.join(W, f'params_{n:02d}.json'); json.dump(dict(texts=texts, accent='#E10600', bands=[[75, 320]], ease=EASE, footage=foot), open(pj, 'w'))
    out = os.path.join(W, f'proj_{n:02d}.json')
    r = subprocess.run([sys.executable, '-m', 'extract.aep_template', 'apply', f, pj, out], cwd=VID, capture_output=True, text=True); print(sid, r.stdout.strip().split('\n')[0][:90])
    a, b = t['window']; entries.append(dict(project=out, comp=t['root'], **{'from': a, 'to': b}, label=f'{n:02d}', footage=['gen', 'red'], extra=f"{EXTRA} --luts footage/gen/luts_red.json"))
json.dump(dict(footage={'gen': f'{TPL}/assets', 'red': RED}, entries=entries, fps=30), open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
print(len(entries), 'scenes', round(sum(e['to'] - e['from'] for e in entries), 1), 's;', 'blanked (fine print/unlisted):', {k: sorted(v) for k, v in unmapped.items()})
