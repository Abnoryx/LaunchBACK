"""Rebuild of the Zeigarnik reel (reference only) as library templates, filled from the /rescene breakdown:
text lines come from the OCR word tracks, camera moves from the measured camera keys, look/props per shot below.
usage: python3 scratch/zeigarnik.py -> scratch/zeigarnik_tpl.json (comps Z0..Z21 + master 'ZEIGARNIK')"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from library.aeb import Project
from library.templates import cine_scene, flare_script, brain_words

BD = json.load(open(os.path.join(HERE, '..', 'extract', 'runs', 'zeigarnik', 'breakdown.json')))
INK, DARK_INK = '#ECEAE6', '#2A2420'
TEAL = '#1F7A86'
# OCR misreads -> the words actually on screen (checked by eye); lines in DROP are prop small print / ghosts
FIX = {'SOUID': 'SQUID', 'Zeigamik': 'Zeigarnik', 'comipleted': 'completed', 'intemupted': 'interrupted', 'betterthan': 'better than',
       'FNDS': 'ENDS', 'Whena': 'When a', 'AN HANGER GE': 'HANGER', 'engagment': 'engagement', 'grap': 'grab', 'Creaters': 'Creators',
       'Yourbrain': 'Your brain', 'Thats': "That's", 'Its': "It's", 'Wel': "We'll", 'aud Feel': 'and Feel', "Don'tjust": "Don't just", 'It find the': 'find the',
       'Brand do.': 'Brands do it'}
DROP = {'Shovour rite', 'Co invisible, precious,', 'ant', 'CALENDER', '01/01/2000', 'Figure1:Brain', 'BOARD', 'animated', 'text,', 'Count Down', "'snoi", 'buny', 'relentless.', 'gal', 'gnrgru .noit .bnrm', 'SLOAEECEOCDZTSAOBEECEOCAAT', 'th', '111', 'Ae'}


def shaft(x0, y0, x1, y1, w0, w1, color=TEAL, op=55):   # a light shaft from (x0,y0) widening to (x1,y1)
    return dict(quad=[[x0 - w0 / 2, y0], [x0 + w0 / 2, y0], [x1 + w1 / 2, y1], [x1 - w1 / 2, y1]], color=color, op=op)


def auto_texts(a, b, font='HelvReal-Bold', hero_font='DidotLTPro-BoldItalic', color=INK, min_size=34, skip=()):
    """Group the OCR word tracks of reel frames a..b into lines: same height band, starting within 10 frames."""
    words = []
    for s in BD['shots']:
        for w in s['words']:
            t = w['text'].strip()
            if not (a <= w['first'] <= b) or w['last'] - w['first'] < 3 or w['at']['size'] < min_size: continue
            if '@' in t or 'Septic' in t or 'Visuals' in t or (len(t) < 2 and t not in 'Ia') or t in skip: continue
            words.append(dict(t=t, f=w['first'] - a, l=w['last'] - a, x=w['at']['x'], y=w['at']['y'], h=w['at']['size']))
    words.sort(key=lambda w: (w['f'], w['x']))
    lines = []
    for w in words:
        for L in lines:
            if abs(L['y'] - w['y']) < 0.45 * L['h'] and abs(L['f'] - w['f']) <= 10 and not any(q['t'] == w['t'] for q in L['w']):
                L['w'].append(w); break
        else:
            lines.append(dict(y=w['y'], h=w['h'], f=w['f'], w=[w]))
    med = sorted(w['h'] for w in words)[len(words) // 2] if words else 60
    out = []
    for L in lines:
        ws = sorted(L['w'], key=lambda q: q['x'])
        txt = ' '.join(FIX.get(q['t'], q['t']) for q in ws); txt = FIX.get(txt, txt)
        if txt in DROP: continue
        h = min(max(q['h'] for q in ws), 260); size = round(h * 0.95)
        left = min(q['x'] - len(q['t']) * 0.27 * q['h'] for q in ws)
        f0 = min(q['f'] for q in ws); l1 = max(q['l'] for q in ws)
        out.append(dict(s=txt, size=size, pos=[round(max(left, 30)), round(L['y'] + 0.33 * h)], font=hero_font if h > 1.5 * med else font,
                        color=color, **{'in': (f0, f0 + 6)}, out=l1 + 2))
    return out


def cam(a, b):
    """Measured camera keys of the reel shot covering a..b, local frames; drop the first 3 frames (whip leakage)."""
    s = next(s for s in BD['shots'] if s['start'] <= a <= s['end'])
    out = {}
    for k, ks in s['camera'].items():
        ks = [(q['frame'] - a, q['value']) for q in ks if a + 3 <= q['frame'] <= b - 4]   # skip whip/flash frames at both ends
        if len(ks) < 2: continue
        v0 = ks[0][1]; base = 100 if k == 'zoom' else 0
        lo, hi = {'x': (-150, 150), 'y': (-150, 150), 'zoom': (97, 135), 'roll': (-6, 6)}[k]
        out[k] = [(0, base)] + [(f, min(max(base + (v - v0), lo), hi)) for f, v in ks]
    return out


P = dict  # prop
SHOTS = [   # name, reel frames a..b, world, props, shapes, extra
    ('Z0', 0, 47, dict(bg='#02080A', flare=dict(y=1250)), [P(file='z_clock.png', w=1024, h=1024, width=760, pos=[860, 230], spin=10, grow=1.06, op=80), P(file='z_clock.png', w=1024, h=1024, width=900, pos=[80, 1000], spin=-8, grow=1.06, op=85)], [], {}),
    ('Z1', 48, 98, dict(bg='#100203', shafts=[shaft(300, 0, 540, 1300, 300, 900, '#7A0A0A', 70)]), [P(file='z_tv.png', w=880, h=1168, width=640, pos=[560, 1060], grow=1.05)], [], {}),
    ('Z3', 196, 237, dict(bg='#4A3628', stripes=[dict(quad=[[0, 300], [1080, 0], [1080, 260], [0, 640]]), dict(quad=[[0, 900], [1080, 520], [1080, 700], [0, 1120]])]),
     [P(file='z_clipboard.png', w=880, h=1168, width=900, pos=[560, 1020], rot=-2)], [], dict(color=DARK_INK, font='HelvReal-Bold')),
    ('Z4', 238, 336, dict(bg='#4A3628', stripes=[dict(quad=[[0, 200], [1080, 0], [1080, 200], [0, 520]], op=40)]),
     [P(file='z_clipboard.png', w=880, h=1168, width=1000, pos=[520, 1040]), P(file='z_sketch.png', w=1024, h=1024, width=440, pos=[560, 900], multiply=True, **{'in': (4, 10)})],
     [dict(kind='disc', d=46, color='#C8221A', pos=[420, 520], t=6)], dict(color=DARK_INK)),
    ('Z5', 337, 374, dict(bg='#02090B', shafts=[shaft(0, 400, 700, 1100, 260, 600)]), [P(file='z_cliff.png', w=880, h=1168, width=760, pos=[760, 1180], grow=1.05)], [], {}),
    ('Z6', 375, 406, dict(bg='#0E0203', shafts=[shaft(540, 0, 540, 900, 300, 700, '#6A0808', 60)]), [],
     [dict(kind='ring', d=1250, color='#E01010', w=10, pos=[540, 960], glow='#FF2020', screen=True)], dict(glow_color='#FF3030', glow_op=60)),
    ('Z7', 407, 451, dict(bg='#01060A', flare=dict(y=1150)), [], [], {}),
    ('Z8', 452, 492, dict(bg='#010A0D', shafts=[shaft(540, 0, 540, 1920, 200, 600, TEAL, 40)]), [P(file='z_sword.png', w=752, h=1344, width=720, pos=[540, 980], grow=1.25, glow='#20E0F0', glow_op=90, glow_size=40)], [], {}),
    ('Z9', 493, 567, dict(bg='#D9D7D1', stripes=[dict(quad=[[0, 560], [1080, 200], [1080, 480], [0, 900]], op=30)]), [P(file='z_sneaker.png', w=1168, h=880, width=520, pos=[560, 1000], **{'in': (6, 12)})],
     [dict(kind='disc', d=620, color='#C9A27E', pos=[560, 1000]), dict(kind='rect', w=560, h=700, stroke='#3A2418', sw=22, pos=[560, 1000], t=4),
      dict(kind='rect', w=200, h=260, stroke='#1E1612', sw=14, pos=[200, 420]), dict(kind='rect', w=220, h=290, stroke='#1E1612', sw=14, pos=[870, 1500], t=20)],
     dict(color=DARK_INK)),
    ('Z10', 568, 584, dict(bg='#E8E2D8'), [], [dict(kind='disc', d=1100, color='#C9A27E', pos=[900, 500]), dict(kind='rect', w=420, h=560, stroke='#1E1612', sw=20, pos=[200, 1100])], dict(color=DARK_INK)),
    ('Z11', 585, 656, dict(bg='#07071A', shafts=[shaft(150, 0, 600, 1500, 250, 800, '#3A3A90', 70)]), [P(file='z_vase.png', w=752, h=1344, width=560, pos=[540, 1120])], [], {}),
    ('Z12', 657, 705, dict(bg='#030405', flare=dict(y=960, color='#8A9AA0', hot='#DDE8EA')), [], [dict(kind='ring', d=1050, color='#2A3034', w=40, pos=[540, 980])], {}),
    ('Z13', 706, 736, dict(bg='#010603', flare=dict(y=960, color='#1A7A2A', hot='#5FE07A')), [P(file='z_lock.png', w=1024, h=1024, width=420, pos=[540, 960], glow='#30FF60')], [], {}),
    ('Z14', 737, 778, dict(bg='#050507'), [P(file='z_hands.png', w=1024, h=1024, width=1000, pos=[540, 980], grow=1.06)], [dict(kind='ring', d=1100, color='#30363A', w=6, pos=[540, 980])], {}),
    ('Z15', 779, 795, dict(bg='#040405'), [P(file='z_hands.png', w=1024, h=1024, width=1300, pos=[540, 980], blur=12, op=60)], [], {}),
    ('Z16', 796, 932, dict(bg='#020203'), [],
     [dict(kind='poly', pts=[[0, -230], [230, 0], [0, 230], [-230, 0]], stroke='#E8E8E8', sw=3, dot=22, pos=[540, 960], spin=20, glow='#FFFFFF')], {}),
    ('Z17', 933, 957, dict(bg='#050102', shafts=[shaft(540, 600, 540, 1920, 300, 1100, '#B00A10', 70)]), [],
     [dict(kind='rect', w=360, h=700, fill='#D0101A', pos=[540, 980]), dict(kind='rect', w=240, h=600, fill='#200206', pos=[580, 1010]),
      dict(kind='poly', pts=[[-120, 0], [120, 0], [0, -140]], fill='#D0101A', pos=[540, 560])], {}),
    ('Z18', 958, 1022, dict(bg='#030304'), [P(file='z_card.png', w=880, h=1168, width=640, pos=[380, 820], rot=-15, spin=-6, tint=('#000000', '#9A9A9A', 50))], [], {}),
    ('Z19', 1023, 1216, dict(bg='#030405', shafts=[shaft(700, 0, 700, 1600, 200, 600, '#8A5A20', 45)]), [P(file='z_tv.png', w=880, h=1168, width=500, pos=[620, 900], tint=('#000000', '#E0A050', 80), op=70)], [], {}),
    ('Z20', 1217, 1232, dict(bg='#02090B', shafts=[shaft(0, 600, 900, 1200, 300, 700)]), [P(file='z_ui.png', w=752, h=1344, width=600, pos=[700, 900], rot=-12)], [], {}),
    ('Z21', 1233, 1343, dict(bg='#01080A', shafts=[shaft(540, 0, 540, 1920, 260, 700, TEAL, 45)]), [], [], {}),
]


def build():
    p = Project()
    order = []
    for name, a, b, world, props, shapes, ex in SHOTS:
        texts = auto_texts(a, b, color=ex.get('color', INK), font=ex.get('font', 'HelvReal-Bold'))
        for t in texts:
            if 'glow_color' in ex: t.update(glow_color=ex['glow_color'], glow_op=ex['glow_op'])
            if ex.get('color') == DARK_INK: t['glow'] = False
        sh = next(q for q in BD['shots'] if q['start'] <= a <= q['end'])
        fl = a > 0 and any(t in sh['transition_in'] for t in ('flash_white', 'invert'))
        cine_scene.build(p, name, b - a + 1, world, props, shapes, texts, camera=cam(a, b), flash_in=fl)
        order.append((name, b - a + 1))
        if name == 'Z1':   # shot 2 is the two hand-built templates
            flare_script.build(p, 'Z2A'); brain_words.build(p, 'Z2B')
            order += [('Z2A', flare_script.DUR_F), ('Z2B', brain_words.DUR_F)]
    tot = sum(n for _, n in order) * cine_scene.F
    m = p.comp('ZEIGARNIK', dur=tot); t = 0.0
    comps = {c.name: c for c in p.comps} if hasattr(p, 'comps') else {}
    for name, n in order:
        m.precomp(comps[name], t, t + n * cine_scene.F, start=t); t += n * cine_scene.F
    m.finalize()
    out = os.path.join(HERE, 'zeigarnik_tpl.json'); p.dump(out); print(out, len(order), 'shots', round(tot, 2), 's')


if __name__ == '__main__':
    build()
