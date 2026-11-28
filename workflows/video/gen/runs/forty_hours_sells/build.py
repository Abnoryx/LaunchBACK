"""forty_hours on the SELLS group: the 23 scenes, exact windows, original order. Per scene: extract.aep_template apply
(texts from slots.json, accent red, greens/cyans/blues -> red, ease from config, third-party imagery swapped), then a Kaggle manifest.
usage (from workflows/video): python3 gen/runs/forty_hours_sells/build.py [preview|final] -> work/manifest.json for kgl.render_multi"""
import json, os, re, subprocess, sys, glob
from PIL import Image
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True)
TPL = '/home/user/tpl/lib/sells'; A = os.path.join(VID, 'library', 'assets'); REAL = os.path.join(HERE, '..', 'forty_hours', 'assets_real')
EASE = json.load(open(os.path.join(VID, 'gen', 'config.json'))).get('ease', 'quad_out')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'preview'
EXTRA = '--samples 1 --preview 540' if OUT == 'preview' else '--samples 4'
MARK = os.path.join(A, 'launchback_mark.png')
# third-party people, books, logos, film stills, platform UI -> our assets in the same animated slots (never blank)
SWAP = {'1429': os.path.join(A, 'fh_alarm_clock.png'),          # Seth Godin photo -> real alarm clock (Wikimedia, CC BY-SA 4.0)
        '1409': os.path.join(A, 'fh_reel_card.png'),            # his book cover -> our '00:08 clean part' card
        '1663': os.path.join(REAL, 'alarm_clock_src.jpg'),      # Moneyball film stills -> real alarm clock photo
        '1690': os.path.join(REAL, 'alarm_clock_src.jpg'), '1674': os.path.join(REAL, 'alarm_clock_src.jpg'),
        '805': os.path.join(A, 'fh_versions_doc.png'),          # vimeo player screenshot -> our version list
        '544': MARK, '534': MARK, '532': MARK, '530': MARK, '536': MARK, '538': MARK, '542': MARK, '2385': MARK,   # spotify/google/gemini icons
        '1914': MARK, '1969': MARK,                             # creator logo
        # stock portraits / film stills of people (KlickPin pins) -> our real photo + our version/waveform documents
        '959': os.path.join(A, 'fh_versions_doc.png'), '1692': os.path.join(A, 'fh_versions_doc.png'), '1686': os.path.join(A, 'fh_versions_doc.png'),
        '1696': os.path.join(A, 'fh_wave_chart.png'), '1694': os.path.join(REAL, 'alarm_face.jpg'), '1656': os.path.join(REAL, 'alarm_face.jpg')}
RED = os.path.join(W, 'red'); os.makedirs(RED, exist_ok=True)
def to_red(im):
    a = im.convert('RGBA'); hsv = np.array(a.convert('RGB').convert('HSV')); h = hsv[..., 0].astype(float) * 360 / 255
    m = (hsv[..., 1] > 64) & (h >= 45) & (h <= 320); hsv[..., 0][m] = 251
    o = Image.fromarray(hsv, 'HSV').convert('RGB').convert('RGBA'); o.putalpha(a.getchannel('A')); return o
def inband(p):
    im = Image.open(p).convert('RGBA'); im.thumbnail((120, 120)); hsv = np.array(im.convert('RGB').convert('HSV')); m = np.array(im.getchannel('A')) > 50
    if not m.any(): return 0
    h = hsv[..., 0].astype(float) * 360 / 255; return float(((hsv[..., 1] > 64) & (h >= 45) & (h <= 320))[m].mean())
def kodak_free(p, fid):   # film frame photo with KODAK PORTRA print on its black side bands -> bands painted black
    o = os.path.join(RED, f'frame_{fid}.png')
    if not os.path.exists(o):
        im = Image.open(p).convert('RGB'); a = np.array(im); h, w = a.shape[:2]; b = int(w * 0.11)
        a[:, :b] = 8; a[:, w - b:] = 8; Image.fromarray(a).save(o)
    return o
def winder_free(p):   # film-strip frame with 'KODAK PORTRA 400' printed at three spots -> 'LAUNCH.BACK 400'
    from PIL import ImageDraw, ImageFont
    o = os.path.join(RED, 'winder.png')
    if not os.path.exists(o):
        im = Image.open(p).convert('RGB'); d = ImageDraw.Draw(im); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
        for x0, y0, x1, y1 in ((10, 122, 190, 148), (325, 122, 500, 148), (270, 1140, 452, 1166)):
            d.rectangle([x0, y0, x1, y1], fill=(0, 0, 0)); d.text((x0 + 4, y0 + 3), 'LAUNCH.BACK 400', font=f, fill=(235, 235, 235))
        im.save(o)
    return o
def greens_to_red(node):   # dark/desaturated greens the accent band skips (s < 0.45 or l < 0.08): swap R and G
    if isinstance(node, list):
        if len(node) in (3, 4) and all(isinstance(v, (int, float)) for v in node) and all(0 <= v <= 1 for v in node[:3]) and node[1] > node[0] + 0.04 and node[1] >= node[2]:
            node[0], node[1] = node[1], node[0]; return 1
        return sum(greens_to_red(v) for v in node)
    if isinstance(node, dict):
        if node.get('_gradient'):   # gradient stops [pos, mid, r, g, b]
            n = 0
            for st in node.get('colors', []):
                if len(st) == 5 and st[3] > st[2] + 0.04 and st[3] >= st[4]: st[2], st[3] = st[3], st[2]; n += 1
            return n
        return sum(greens_to_red(v) for v in node.values())
    return 0
# LUTs (Colorama, measured): green-dominant entries -> red (swap R and G)
lut = json.load(open(f'{TPL}/luts.json'))
for k, v in lut.items():
    d = v['data']
    for i in range(0, len(d) - 2, 3):
        if d[i + 1] > d[i] + 8: d[i], d[i + 1] = d[i + 1], d[i]
json.dump(lut, open(os.path.join(RED, 'luts_red.json'), 'w'))
slots = json.load(open(os.path.join(HERE, 'slots.json'))); entries = []; unmapped = {}
for f in sorted(glob.glob(f'{TPL}/templates/shot_*.json')):
    n = int(re.search(r'shot_(\d+)', f).group(1)); t = json.load(open(f))['template']; texts = {}
    for x in t['params']['texts']:
        k = x['text'].strip()
        if k in slots: texts[x['id']] = x['text'].replace(k, slots[k])
        elif any(len(q) > 30 and k.startswith(q[:30]) for q in slots): texts[x['id']] = slots[next(q for q in slots if len(q) > 30 and k.startswith(q[:30]))]   # long fine print, other line breaks
        else: texts[x['id']] = ' '; unmapped.setdefault(n, set()).add(k[:40])
    foot = {}
    for x in t['params']['footage']:
        fid = str(x['id']); pth = os.path.join(TPL, 'assets', x['name'])
        if fid in SWAP: foot[fid] = SWAP[fid]
        elif re.search(r'earnera|spotify|google|gemini|gmail|seth', x['name'], re.I): foot[fid] = MARK
        elif fid == '689':   # 'Emerald depth' palette screenshot: dark greens the hue test misses -> forced red copy
            o = os.path.join(RED, 'red_689.png')
            if not os.path.exists(o):
                a = np.array(Image.open(pth).convert('RGBA')); a[..., [0, 1]] = a[..., [1, 0]]; Image.fromarray(a).save(o)
            foot[fid] = o
        elif x['name'].startswith('7b5fa151'): foot[fid] = kodak_free(pth, fid)
        elif x['name'] == 'camera winder frame.jpg': foot[fid] = winder_free(pth)
        elif os.path.exists(pth) and x['name'].lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png') and inband(pth) > 0.05:
            o = os.path.join(RED, f'red_{fid}.png')
            if not os.path.exists(o): to_red(Image.open(pth)).save(o)
            foot[fid] = o
    pj = os.path.join(W, f'params_{n:02d}.json'); json.dump(dict(texts=texts, accent='#E10600', bands=[[45, 320]], ease=EASE, footage=foot), open(pj, 'w'))
    out = os.path.join(W, f'proj_{n:02d}.json')
    r = subprocess.run([sys.executable, '-m', 'extract.aep_template', 'apply', f, pj, out], cwd=VID, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)
    pd = json.load(open(out)); greens_to_red(pd['comps']); greens_to_red([f.get('color') for f in pd['footage'] if f.get('color')])
    open(out, 'w').write(json.dumps(pd).replace('KODAK PORTRA 400', 'LAUNCH.BACK 400'))
    a, b = t['window']; entries.append(dict(project=out, comp=t['root'], **{'from': a, 'to': b}, label=f'{n:02d}', footage=['sells', 'red'],
                                            extra=f'{EXTRA} --luts footage/red/luts_red.json'))
json.dump(dict(footage={'sells': f'{TPL}/assets', 'red': RED}, entries=entries, fps=30), open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
print(len(entries), 'scenes', round(sum(e['to'] - e['from'] for e in entries), 1), 's; blanked (unlisted):', {k: sorted(v) for k, v in unmapped.items()})
