"""Michelin reel build: plan.json -> work/ (ours project + one project per bought scene) + work/manifest.json for kgl.render_multi.
usage: python3 gen/runs/michelin/build.py   (then python3 -m kgl.render_multi gen/runs/michelin/work/manifest.json gen/runs/michelin/work/r1)"""
import importlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.abspath(os.path.join(HERE, '..', '..', '..')); sys.path.insert(0, VID)
from library import aeb, style as S, palette_swap
from library.aeb import Project
F = S.F; W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True)
ASSETS = os.path.join(VID, 'library', 'assets'); BLANK = os.path.join(ASSETS, 'blank.png')
PREV = '--samples 1 --preview 540'
FINE = ' '; WM = ' '
RED = '#E10600'
TPL = '/home/user/tpl/lib'

# ---- ours: template + params (no third-party marks; red accent via palette_swap) ----
OURS = {
 'hero_word': dict(words={'kicker': 'a tyre company', 'hero': 'POWER', 'q1': 'over', 'q2': 'chefs', 'sub1': 'has more', 'sub2': ' '}, mark='↑',
                   prop={'file': 'm_tyre.png', 'w': 705, 'h': 1006, 'scale': 75}, layout={'hero': [150, 1218, 671], 'hero_scale': [96, 116, 100]}),
 'share_card': dict(words={'line1': 'And it started', 'pill': 'FREE', 'with': 'as a', 'accent': 'giveaway.', 'who': 'for', 'bar': 'every', 'tail': 'driver'}, watermark=WM, fineprint=FINE),
 'calendar_flip': dict(pages=[1897, 1898, 1899, 1900, 1900], words={'brand': 'Michelin', 'gives': 'sold', 'nights': 'tyres.', 'end': '1900', 'end_small': 'France'},
                       layout={'bg': '#5A1210', 'flap': '#200606'}, prop={'file': 'm_tyre.png', 'w': 705, 'h': 1006, 'width': 220},
                       timing={'nights': (44, 58), 'end': (64, 74), 'end_small': (70, 80)}),
 'flythrough_words': dict(words={'a': 'the', 'b': 'problem:', 'c_small': 'almost nobody', 'c_accent': 'owned a car.'}),
 'word_prop_pop': dict(words={'brand': 'a car?', 'small': 'almost nobody', 'label': 'in france', 'l1': 'owned', 'l2': 'a', 'accent': 'car'}, fineprint=FINE, watermark=WM,
                       prop={'model': 'm_tyre.glb', 'scale': 90, 'ry': 25}, prop_tint=False,
                       hand={'poses': [('glove_cut_fist_red.png', 776, 994, 18, -40, 0, 0.75), ('glove_cut_half_red.png', 811, 955, 8, -10, -15, 0.8),
                                       ('glove_cut_near_red.png', 885, 935, 2, 5, -25, 0.95), ('glove_cut_open_red.png', 966, 961, 0, 10, -30, 1.05)]}),
 'dark_docs': dict(words={'a': 'no ad', 'b': 'budget.', 'c': 'zero', 'd': 'spent.'}, watermark=WM, fineprint=FINE),
 'brain_collage': dict(words={'amp': ' ', 'line': 'They had\na map', 'small': 'and a', 'accent': 'plan.', 'label': 'Route'}, ring='ROADS  FUEL  HOTELS  FOOD  ROADS  FUEL  HOTELS  FOOD',
                       watermark=WM, fineprint=FINE, prop={'model': 'm_tyre.glb', 'scale': 95, 'rx': 0, 'rz': 0}, quad=('m_map.png', 1168, 878, 30)),
 'word_panel': dict(words={'a': 'So they gave', 'b': 'a guide', 'panel': 'away', 'big': 'FREE'}),
 'hand_flame': dict(words={'small': 'this road goes', 'big': 'some  where'}, flame=('flame_loop.mp4', 716, 1280, 73 / 24),
                    hand={'poses': [('hand_rim_open_red.png', 752, 1344, [330, 330]), ('hand_rim_mid_red.png', 752, 1344, [316, 322]),
                                    ('hand_rim_pinch_red.png', 752, 1344, [300, 330])], 'times': [10, 14]}),
 'statement_flip': dict(words={'line': 'The map wasn’t', 'accent': 'the crazy', 'small': 'part. The', 'big': 'eating.'}, watermark=WM, fineprint=FINE, scan=['m_france_dark.png'], accent_rise=True),
 'disc_brain': dict(words={'kicker': 'they sold', 'term': 'tyres.', 'term_accent': ' '}, definition=' ',
                    banner={'left_num': '19', 'left_word': 'nineteen', 'right_num': '00', 'right_word': 'hundred', 'l1': 'THE TYRE', 'l2': 'paid for it', 'r1': 'THE GUIDE', 'r2': 'was free'},
                    prop={'model': 'm_tyre.glb', 'scale': 110, 'ry': (-30.0, 30.0)}),
 'needle_solo': dict(words={'cta': 'finding them', 'accent': 'one', 'small': 'at a', 'big': 'time.'}, watermark=WM, fineprint=' ',
                     needle={'assets': {'logo': BLANK, 'plate': os.path.join(ASSETS, 'needle_plate_red.png')}, 'layout': {'pens': []}}),
 'logo_reveal': dict(bg='#000000'),
}

# ---- bought scenes: text per layer id, footage swaps (brand/person imagery -> blank) ----
def T(**kw): return kw
BOUGHT = {
 'gen/s12': dict(texts={'iphone nigga/0': 'power', 'iphone nigga/1': 'over', 'iphone nigga/2': ' ', 'photo 1/2': 'CHEFS', 'photo 2/2': 'CHEFS', 'scene9/4': 'tyre', 'scene9/5': 'company',
                       'scene9/6': 'has more', 'scene9/7': 'POWER', 'scene9/9': ' ', 'scene9/10': ' ', 'scene9/11': ' ', 'scene9/18': 'chefs', 'scene 10/10': 'THAN'},
                 footage={'1429': BLANK, '493': BLANK}),
 'gen/s08': dict(texts={'scene 7/7': 'critic alive', 'scene 7/8': 'critic alive', 'scene 7/9': 'than any food', 'scene 7/10': 'than any food'}, footage={'1181': BLANK}),
 'sells/s22': dict(texts={'scene 17/3': 'tyres need', 'scene 17/4': 'A', 'scene 17/9': 'MOVEMENT', 'scene 17/10': '1', 'scene 18/6': 'Tyres need roads to go anywhere',
                          'scene 18/7': 'Tyres need roads to go anywhere', 'scene 18/8': 'Tyres need roads to go anywhere', 'scene 18/17': 'A', 'scene 18/18': 'DS', 'scene 18/19': 'RO'}),
 'sells/s20': dict(texts={'8th reel/9': 'Fuel. Sleep. Eat.', 'scene 17/3': 'FUEL', 'scene 17/4': ' ', 'scene 17/9': 'SLEEP · EAT', 'scene 17/10': '1'}),
 'gen/s10': dict(texts={'Comp 1/47': 'No ', 'Comp 1/48': 'appeal.', 'iphone nigga/0': ' ', 'iphone nigga/1': ' ', 'iphone nigga/2': ' '}, footage={'1429': BLANK}),
 'sells/s14': dict(texts={'8th reel/23': 'Chefs chase ', '8th reel/24': 'the mark', '8th reel/29': 'A rating', '8th reel/30': 'no appeal'}, footage={'1663': BLANK, '1674': BLANK}),
 'gen/s01': dict(texts={'scene 1/23': 'A tyre company', 'ui text/3': 'invented it.'}, footage={'126': BLANK, '120': BLANK}),
 'gen/s09': dict(texts={'Comp 1/47': 'Somewhere ', 'scene 7/7': 'to go', 'scene 7/8': 'to go', 'scene 7/9': 'they gave', 'scene 7/10': 'they gave', 'scene 8/9': 'somewhere.',
                        'scene 8/12': 'to go.', 'scene 8/16': 'first they gave', 'scene 8/19': 'Read', 'scene 8/20': 'people somewhere', 'scene 8/26': 'The Red Book', 'scene 8/27': 'The Red Book'},
                  footage={'1181': BLANK}),
 'gen/s02': dict(texts={'pc /2': ' ', 'scene 1/23': 'Every business', 'scene 2/4': 'you love has', 'scene 2/5': 'you love has', 'scene 2/6': 'you love has', 'scene 2/10': 'a guidebook',
                        'scene 2/12': 'a guidebook', 'scene 2/13': 'a guidebook', 'scene 3/6': 'GUIDE', 'ui text/3': 'like this.'}, footage={'126': BLANK, '120': BLANK}),
 'sells/s19': dict(texts={'8th reel/9': 'Your guidebook?', 'scene 16/5': 'Your', 'scene 16/6': 'guidebook?'}, footage={'2385': BLANK}),
}
REPLACE = {'stop/s02': 'sells/s19'}   # stop/* private files are not in the Kaggle backup

def main():
    plan = json.load(open(os.path.join(HERE, 'plan.json')))['shots']
    for s in plan: s['template'] = REPLACE.get(s['template'], s['template'])
    p = Project(); aeb.EASE_OVERRIDE = S.QUAD_OUT; entries, order = [], []
    foot = {'gen': f'{TPL}/gen/assets', 'sells': f'{TPL}/sells/assets'}
    for n, s in enumerate(plan, 1):
        t, sec, label = s['template'], s['seconds'], f'{n:02d}'
        if t in OURS:
            mod = importlib.import_module(f'library.templates.{t}'); c = mod.build(p, f'S{label}', **OURS[t]); dur = mod.DUR_F * F
            entries.append(dict(project='__OURS__', comp=f'S{label}', **{'from': 0, 'to': round(min(dur, sec), 4)}, label=label, footage=[], extra=PREV))
        else:
            reel, sid = t.split('/'); i = int(sid[1:]); tp = f'{TPL}/{reel}/templates/shot_{i:02d}.json'
            pj = os.path.join(W, f'params_{label}.json'); json.dump({**BOUGHT[t], 'accent': RED}, open(pj, 'w'))
            out = os.path.join(W, f'proj_{label}.json')
            subprocess.run([sys.executable, '-m', 'extract.aep_template', 'apply', tp, pj, out], cwd=VID, check=True, capture_output=True)
            tm = json.load(open(tp))['template']; a, b = tm['window']
            entries.append(dict(project=out, comp=tm['root'], **{'from': a, 'to': round(min(b, a + sec), 4)}, label=label, footage=[reel],
                                extra=f"{PREV} --luts footage/{reel}/luts.json"))
        order.append((label, t, sec))
    aeb.EASE_OVERRIDE = None
    ours = os.path.join(W, 'ours.json'); p.dump(ours); d = json.load(open(ours)); palette_swap.apply(d); json.dump(d, open(ours, 'w'))
    for e in entries:
        if e['project'] == '__OURS__': e['project'] = ours
    man = dict(footage=foot, entries=entries, fps=30); json.dump(man, open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
    tot = sum(e['to'] - e['from'] for e in entries); print(f'{len(entries)} entries, {tot:.1f}s total'); [print(*o) for o in order]

if __name__ == '__main__': main()
