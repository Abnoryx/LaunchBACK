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
# bands=[[45, 320]]: greens, cyans, blues, purples -> the red accent; yellow/orange stay (user: 'make it red coloured')
NEW = os.path.join(HERE, 'assets_gen', 'out')   # Higgsfield-generated / made assets, in the exact slots the original animates (user 2026-11-25: no og assets, never blank)
SWAP = {'1181': 'chef_sticker.png', '1116': 'broll_chef.mp4', '1120': 'tyre_icon.png', '493': 'phone_black.png', '1429': 'broll_road.mp4', '126': 'avatar.png',
        '1899': 'avatar.png', '120': 'ui_profile.jpg', '1895': 'ui_post.jpg', '1971': 'tick_red.jpg', '573': 'badge_tyre.png', '553': 'badge_book.png',
        '2320': 'sticker_book.png', '824': 'desktop_icons.png', '718': 'wallpaper.png', '396': 'sticker_toque.png', '365': 'sticker_tyre.png'}
SWAP = {k: os.path.join(NEW, v) if v != 'wallpaper.png' else os.path.join(HERE, 'assets_gen', 'wallpaper.png') for k, v in SWAP.items()}
BRAND = re.compile(r'iphone|micheal jordan|saquon|nike|whatsapp|vecteezy|instagram|earnera|IMG_0264|Untitled design|icons\.png|blue tick|^e7650458|d81203|windows xp|clippy', re.I)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'preview'
EXTRA = '--samples 1 --preview 540' if OUT == 'preview' else '--samples 4'
from PIL import Image, ImageSequence
import numpy as np
RED = os.path.join(W, 'footage_red2'); os.makedirs(RED, exist_ok=True)
def to_red(im):   # greens/cyans/blues/purples (hue 75-320, saturation > 0.25) -> red hue; lightness, saturation, alpha kept
    a = im.convert('RGBA'); hsv = np.array(a.convert('RGB').convert('HSV')); h = hsv[..., 0].astype(float) * 360 / 255
    m = (hsv[..., 1] > 64) & (h >= 45) & (h <= 320); hsv[..., 0][m] = 251
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
    h = hsv[..., 0].astype(float) * 360 / 255; return float(((hsv[..., 1] > 64) & (h >= 45) & (h <= 320))[m].mean())
def wallpaper_inject(path):
    """The hero collage ('scene 3', also the phone lock screen) has a white solid at the bottom and a recoloured paper above it: make the solid the Eiffel
    wallpaper and multiply the red paper over it, so a red-tinted iconic wallpaper shows behind the stickers (user: 'there's no wallpaper')."""
    d = json.load(open(path)); c = next((c for c in d['comps'] if c['name'] == 'scene 3'), None)
    if not c: return
    solid = next((l for l in c['layers'] if l['name'] == 'White Solid 3'), None); paper = next((l for l in c['layers'] if l['name'].startswith('Texturelabs_Paper')), None)
    if not solid or not paper: return
    users = [l for cc in d['comps'] for l in cc['layers'] if l.get('src_id') == solid['src_id'] and l.get('src_type') == 'FootageItem']
    assert len(users) == 1, 'solid is shared'
    f = next(f for f in d['footage'] if f['id'] == solid['src_id'])
    f.update(name='wallpaper_1080.png', source_type='FileSource', file=os.path.join(NEW, 'wallpaper_1080.png'), is_still=True); f.pop('color', None)
    paper['blending_mode'] = 5216   # MULTIPLY
    json.dump(d, open(path, 'w'))

# ---- round 3 edits (user's Edit Lab pins, 2026-11-27): project-level patches, applied after extract.aep_template ----
def _flat(ps, out=None, pre=''):
    out = out if out is not None else {}
    for q in ps:
        out[pre + q['n']] = q
        if q.get('c'): _flat(q['c'], out, pre + q['n'] + '/')
    return out
def _layers(d, comp, pred):
    return [l for c in d['comps'] if c['name'] == comp for l in c['layers'] if pred(l)]
def _scale(l, f):      # multiply x/y scale (static values only)
    q = _flat(l['props']).get('Transform/Scale'); assert q is not None and not q.get('k'), 'animated scale'; v = q['v']; q['v'] = [v[0] * f, v[1] * f] + list(v[2:])
def _set(l, key, val):
    q = _flat(l['props'])[key]; assert not q.get('k'), key + ' is animated'; q['v'] = val
def _shadow(dist, soft, op, direction):
    c = lambda n, m, v, syn=False: dict(n=n, m=f'ADBE Drop Shadow-{m}', v=v, **({'syn': True} if syn else {}))
    return dict(n='Drop Shadow', m='ADBE Drop Shadow', c=[c('Shadow Color', '0001', [0.0, 0.0, 0.0, 1.0], True), c('Opacity', '0002', op, True), c('Direction', '0003', direction), c('Distance', '0004', dist), c('Softness', '0005', soft), c('Shadow Only', '0006', 0, True)])
def edits_r10(n, path):
    d = json.load(open(path))
    if n == 1:   # change A: depth and shading on the red shape (Shape Layer 1, bottom-left)
        for l in _layers(d, 'scene 1', lambda l: l['name'] == 'Shape Layer 1' and l['i'] == 28): l['props'].append(dict(n='Effects', m='ADBE Effect Parade', c=[_shadow(54, 46, 150, 200)]))
    if n == 2:   # change C: the monitor 'screen' content (a circle) overflowed the screen -> smaller
        for l in _layers(d, 'pc ', lambda l: l['name'] == 'earnera logo.png'): _scale(l, 0.6)
    if n == 4:   # 'the box thingy smaller': the notification icon boxes
        for l in _layers(d, 'scene 4', lambda l: l.get('src_id') in (573, 553)): _scale(l, 0.78)
    if n == 5:   # wallpaper: the original keeps it inside the Notepad window only (alpha matte). Add an un-matted full-frame copy at the very bottom (user: 'add a good themed wallpaper')
        import copy
        for c in d['comps']:
            if c['name'] != 'scene 5': continue
            src = next(l for l in c['layers'] if l['name'] == 'windows xp wallpaper.jpg'); w, h = 1080, 1920
            fr = copy.deepcopy(next(f for f in d['footage'] if f['id'] == 718)); fr.update(id=99718, name='wallpaper_1080.png', file=os.path.join(NEW, 'wallpaper_1080.png'), width=1080, height=1920); d['footage'].append(fr)   # same file, real portrait dimensions
            cp = copy.deepcopy(src); cp['src_id'] = 99718; cp['i'] = max(l['i'] for l in c['layers']) + 1; cp['track_matte_type'] = 5012; cp['has_track_matte'] = False; cp['matte_layer'] = None; cp['parent'] = None; cp['three_d_layer'] = False; cp['name'] = 'wallpaper full'
            _set(cp, 'Transform/Position', [540.0, 960.0, 0.0]); _set(cp, 'Transform/Anchor Point', [w / 2, h / 2, 0.0]); k = max(1080 / w, 1920 / h) * 100; _set(cp, 'Transform/Scale', [k, k, 100.0])
            c['layers'].append(cp)
        for l in _layers(d, 'scene 5', lambda l: l['name'] == 'led.jpg'): l['enabled'] = False
    if n == 8:   # 'the guy is at a weird angle': straighten and fit the chef sticker
        for l in _layers(d, 'micheal jordan', lambda l: l['name'] == 'micheal jordan.png'): _set(l, 'Transform/Z Rotation', -9.0); _scale(l, 0.86)
    if n == 13:  # the stray original word ' Memories' stays; the other two words are rewritten in slots.json
        pass
    if n == 15:  # 'the photo remove': the grey placeholder photo (BEAN LEAK clip, not shipped) on top of the post
        pass   # footage 2088 is swapped for a white plate in the footage map (below)
    json.dump(d, open(path, 'w'))
EDITED = {1, 2, 4, 5, 8, 13, 15, 19}
slots = json.load(open(os.path.join(HERE, 'slots.json'))); entries = []; unmapped = {}
for f in sorted(glob.glob(f'{TPL}/templates/shot_*.json')):
    n = int(re.search(r'shot_(\d+)', f).group(1)); sid = f'gen/s{n:02d}'; t = json.load(open(f))['template']; m = slots[sid]; texts = {}
    for x in t['params']['texts']:
        k = x['text'].strip()
        if k in m: texts[x['id']] = x['text'].replace(k, m[k]) if k else x['text']
        else: texts[x['id']] = ' '; unmapped.setdefault(sid, set()).add(k[:40])   # fine print / unlisted slot: blanked
        if sid == 'gen/s15' and k.startswith('That’s what makes'): texts[x['id']] = {'text': m[k], 'fill': [0.08, 0.08, 0.08]}
        if sid == 'gen/s06' and k == 'BRAIN': texts[x['id']] = {'text': m[k], 'fill': [0.88, 0.02, 0.0]}   # TYRES in red: the original dark text vanishes on a dark tyre
    foot = {str(x['id']): SWAP.get(str(x['id']), LED if re.search(r'wallpaper', x['name'], re.I) else BLANK) for x in t['params']['footage'] if BRAND.search(x['name']) or str(x['id']) in SWAP}
    if sid == 'gen/s15': foot['2088'] = os.path.join(NEW, 'paper_plate.png')   # the placeholder photo -> plain white plate
    for x in t['params']['footage']:   # still images that are mostly green/blue/purple -> red copies (user: make it red coloured)
        pth = os.path.join(TPL, 'assets', x['name'])
        if str(x['id']) not in foot and x['name'].lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'gif') and os.path.exists(pth) and inband(pth) > 0.05: foot[str(x['id'])] = red_copy(x['id'], pth)
    for x in t['params']['footage']:   # leftovers the hue test misses: the green-screen smoke clip (video) and the pin
        pth = os.path.join(TPL, 'assets', x['name']); fid = str(x['id'])
        if fid in foot or not os.path.exists(pth): continue
        if re.search(r'smoke', x['name'], re.I):   # green background -> red: rotate hue about -115 degrees
            o = os.path.join(RED, f'red_{fid}.mp4')
            if not os.path.exists(o): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pth, '-vf', 'hue=h=-115:s=1.15', '-an', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', o], check=True)
            foot[fid] = o
        elif re.search(r'\bpin\b', x['name'], re.I): foot[fid] = red_copy(x['id'], pth)
    pj = os.path.join(W, f'params_{n:02d}.json'); json.dump(dict(texts=texts, accent='#E10600', bands=[[45, 320]], ease=EASE, footage=foot), open(pj, 'w'))
    out = os.path.join(W, f'proj_{n:02d}.json')
    r = subprocess.run([sys.executable, '-m', 'extract.aep_template', 'apply', f, pj, out], cwd=VID, capture_output=True, text=True); print(sid, r.stdout.strip().split('\n')[0][:90])
    wallpaper_inject(out); edits_r10(n, out)
    a, b = t['window']; entries.append(dict(project=out, comp=t['root'], **{'from': a, 'to': b}, label=f'{n:02d}', footage=['gen', 'red', 'new'], extra=f"{EXTRA.replace('--samples 1', '--samples 3') if n in EDITED else EXTRA} --luts footage/gen/luts_red.json"))
json.dump(dict(footage={'gen': f'{TPL}/assets', 'red': RED, 'new': NEW}, entries=entries, fps=30), open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
json.dump(dict(footage={'gen': f'{TPL}/assets', 'red': RED, 'new': NEW}, entries=[e for e in entries if int(e['label']) in EDITED], fps=30), open(os.path.join(W, 'manifest_r10.json'), 'w'), indent=1)
print(len(entries), 'scenes', round(sum(e['to'] - e['from'] for e in entries), 1), 's;', 'blanked (fine print/unlisted):', {k: sorted(v) for k, v in unmapped.items()})
