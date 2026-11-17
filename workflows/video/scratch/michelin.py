"""LaunchBack reel #1 — "The Michelin Play". Built only from proven library templates + our assets, red accent.
Each shot is a template build with our words/props; the master comp plays them back to back at their natural
lengths (the VO will retime them later). S18 is a placeholder until the user's AutoAE render arrives.
usage: python3 michelin.py  -> scratch/michelin_tpl.json (comps 'MICHELIN' + one per shot)"""
import importlib, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library import style as S, palette_swap

F = S.F
FINE = ('The Michelin Guide was first printed in 1900 and handed out free to French drivers: where to fill up, '
        'where to sleep, where to eat. It existed to sell tyres.')
WM = ' '
RED = '#E10600'

SHOTS = [
    ('S1', 'hero_word', dict(words={'kicker': 'a tyre company', 'hero': 'POWER', 'q1': 'over', 'q2': 'chefs', 'sub1': 'has more', 'sub2': ' '},
                             mark='★', prop={'file': 'm_tyre.png', 'w': 705, 'h': 1006, 'scale': 75},
                             layout={'hero': [150, 1218, 671], 'hero_scale': [96, 116, 100]})),
    ('S2', 'disc_brain', dict(words={'kicker': 'than any', 'term': 'food critic', 'term_accent': 'alive.'},
                              definition=FINE[:96],
                              banner={'left_num': '19', 'left_word': 'nineteen', 'right_num': '00', 'right_word': 'hundred',
                                      'l1': 'THE GUIDE', 'l2': '1900 Edition 001', 'r1': 'FRANCE', 'r2': '46°N 2°E'},
                              prop={'model': 'm_cloche.glb', 'scale': 95, 'ry': (-20.0, 20.0)})),
    ('S3', 'calendar_flip', dict(pages=[1897, 1898, 1899, 1900, 1900], words={'brand': 'Michelin', 'gives': 'sells', 'nights': 'tyres.', 'end': '1900', 'end_small': 'France'},
                                 layout={'bg': '#5A1210', 'flap': '#200606'}, prop={'file': 'm_tyre.png', 'w': 705, 'h': 1006, 'width': 220},
                                 timing={'nights': (44, 58), 'end': (64, 74), 'end_small': (70, 80)})),
    ('S4', 'statement_flip', dict(words={'line': 'Problem: almost', 'accent': 'nobody', 'small': 'owns a', 'big': 'car.'},
                                  watermark=WM, fineprint=FINE, scan=['m_france_dark.png'], accent_rise=True)),
    ('S5', 'word_panel', dict(words={'a': 'A tyre', 'b': 'business', 'panel': 'needs', 'big': 'MOVE'})),
    ('S6', 'dark_docs', dict(words={'a': 'They had', 'b': 'no ad', 'c': 'budget', 'd': 'at all.'}, watermark=WM, fineprint=FINE)),
    ('S7', 'word_prop_pop', dict(words={'brand': 'map.', 'small': 'They had a', 'label': 'the guide', 'l1': 'So they made', 'l2': 'a free', 'accent': 'guide'},
                                 fineprint=FINE, watermark=WM, prop={'model': 'm_book.glb', 'scale': 78, 'ry': 25}, prop_tint=False,
                                 hand={'poses': [('glove_cut_fist_red.png', 776, 994, 18, -40, 0, 0.75), ('glove_cut_half_red.png', 811, 955, 8, -10, -15, 0.8),
                                                 ('glove_cut_near_red.png', 885, 935, 2, 5, -25, 0.95), ('glove_cut_open_red.png', 966, 961, 0, 10, -30, 1.05)]})),
    ('S8', 'share_card', dict(words={'line1': 'So they gave', 'pill': 'ONE', 'with': 'away', 'accent': 'free.', 'who': 'for', 'bar': 'every', 'tail': 'driver'},
                              watermark=WM, fineprint=FINE)),
    ('S9', 'brand_box', dict(words={'brand': 'GUIDE', 'tagline': 'Where to...', 'tags': 'fill up\nsleep\neat', 'tag_box': 'where to',
                                    'over': 'fill', 'side': 'sleep', 'marker': 'eat'},
                             fineprint=FINE, prop={'model': 'm_pump.glb', 'scale': 150, 'ry0': 25, 'rx': 6}, timing={'prop_out': (44, 52)}, layout={'prop': [650, 1100, 0]},
                             swaps=[(('still', 'bed.png', 1145, 879, 40), (44, 52), (67, 75)), (('model', 'm_cloche.glb', 70), (67, 75), None)])),
    ('S10', 'brain_collage', dict(words={'amp': '&', 'line': 'France started\ndriving', 'small': 'to places', 'accent': 'unknown', 'label': 'Route'},
                                  ring='ROADS  FUEL  HOTELS  FOOD  ROADS  FUEL  HOTELS  FOOD', watermark=WM, fineprint=FINE,
                                  prop={'model': 'm_tyre.glb', 'scale': 95, 'rx': 0, 'rz': 0}, quad=('m_map.png', 1168, 878, 30))),
    ('S11', 'flythrough_words', dict(words={'a': 'it had', 'b': 'never', 'c_small': 'even', 'c_accent': 'heard of.'})),
    ('S12', 'word_panel', dict(words={'a': 'The guide', 'b': 'was free', 'panel': 'for', 'big': 'DECADES'}, layout={'big_size': 230, 'line_size': 92, 'b_x': 570})),
    ('S13', 'disc_brain', dict(words={'kicker': 'The tyres', 'term': 'paid', 'term_accent': 'for it.'}, definition=FINE[:96],
                               banner={'left_num': '19', 'left_word': 'nineteen', 'right_num': '20', 'right_word': 'twenty',
                                       'l1': 'FREE COPIES', 'l2': '1900-1920', 'r1': 'PAID BY', 'r2': 'TYRES'},
                               prop={'model': 'm_tyre.glb', 'scale': 110, 'ry': (-30.0, 30.0)})),
    ('S14', 'hand_flame', dict(words={'small': 'chefs chasing', 'big': 'the    mark'}, flame=('star_glow.mp4', 716, 1280, 73 / 24),
                               hand={'poses': [('hand_rim_open_red.png', 752, 1344, [330, 330]), ('hand_rim_mid_red.png', 752, 1344, [316, 322]),
                                               ('hand_rim_pinch_red.png', 752, 1344, [300, 330])], 'times': [10, 14]})),
    ('S15', 'dark_docs', dict(words={'a': 'a rubber', 'b': 'company', 'c': 'invented', 'd': 'it.'}, watermark=WM, fineprint=FINE)),
    ('S16', 'statement_flip', dict(words={'line': 'Michelin never sold', 'accent': 'information', 'small': 'they built', 'big': 'demand'},
                                   watermark=WM, fineprint=FINE, scan=['m_france_dark.png'], accent_rise=True)),
    ('S17', 'flythrough_words', dict(words={'a': 'and collected', 'b': 'it', 'c_small': 'somewhere', 'c_accent': 'else.'})),
    ('S18', 'disc_brain', dict(words={'kicker': 'their audience', 'term': 'was the', 'term_accent': 'guide.'}, prop_plain=True, definition=FINE[:96],
                               banner={'left_num': 'AU', 'left_word': 'audience', 'right_num': '$', 'right_word': 'money',
                                       'l1': 'THE GUIDE', 'l2': 'free, 1900-1920', 'r1': 'THE TYRES', 'r2': 'paid for it'},
                               prop={'model': 'm_book.glb', 'scale': 95, 'ry': (-25.0, 25.0)})),
    ('S18b', 'hero_word', dict(words={'kicker': 'their money was', 'hero': 'TYRES', 'q1': 'the', 'q2': 'tyres.', 'sub1': ' ', 'sub2': ' '},
                               mark='★', prop={'file': 'm_tyre.png', 'w': 705, 'h': 1006, 'scale': 75},
                               layout={'hero': [150, 1218, 671], 'hero_scale': [96, 116, 100]})),
    ('S19', 'brain_collage', dict(words={'amp': '', 'line': 'Most creators\nhave a guide', 'small': 'and no', 'accent': 'tyres.', 'label': 'Audience'},
                                  ring='FOLLOWERS  VIEWS  LIKES  FOLLOWERS  VIEWS  LIKES', watermark=WM, fineprint=FINE,
                                  prop={'model': 'm_book.glb', 'scale': 110, 'rx': 0, 'rz': 0}, quad=('m_book.png', 713, 1108, 26), prop_plain=True)),
    ('S20', 'follow_needle', dict(words={'cta': 'That gap', 'accent': 'is what', 'small': 'I work', 'big': 'on.'},
                                  watermark=WM, fineprint=FINE, logo=('blank.png', 4, 4), hand=None,
                                  layout={'pens': [([915, 1412, -862], 334, ('m_tyre.png', 705, 1006), 45), ([30, 1286, 0], 21, ('m_book.png', 713, 1108), 45)]})),
    ('LOGO', 'logo_reveal', dict(bg='#000000')),
]


def build():
    p = Project()
    master_parts, t = [], 0.0
    for name, tpl, params in SHOTS:
        if tpl is None:
            dur = 3.7
            c = p.comp(name, dur=dur)
            ph = c.text('placeholder', 'S18  AutoAE preset', 0, dur, S.FONTS['sans_bold'], 70, '#777777', justify=7415)
            c.transform(ph, pos=[540, 960])
            c.footage(p.solid('#151515', name='slate'), 0, dur)
            c.finalize()
        else:
            mod = importlib.import_module(f'library.templates.{tpl}')
            c = mod.build(p, name, **params)
            dur = mod.DUR_F * F
        master_parts.append((c, t, dur))
        t += dur
    m = p.comp('MICHELIN', dur=t)
    for c, t0, dur in reversed(master_parts):   # later shots lower in the stack; each plays only in its slot
        L = m.precomp(c, t0, t0 + dur, start=t0)
    m.finalize()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'michelin_tpl.json')
    p.dump(out)
    d = json.load(open(out)); n = palette_swap.apply(d); json.dump(d, open(out, 'w'))
    print(out, f'{t:.2f}s', 'recoloured', n)
    for c, t0, dur in master_parts: print(f'{c.name:5s} {t0:6.2f} {dur:5.2f}')


if __name__ == '__main__':
    build()
