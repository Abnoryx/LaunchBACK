"""forty_hours: the 14 'psych' scenes in original order with our words/props (pattern of scratch/michelin.py).
usage (from workflows/video): python3 gen/runs/forty_hours/build.py -> gen/runs/forty_hours/forty_tpl.json (comp 'FORTY')"""
import importlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from library import aeb
from library.aeb import Project
from library import style as S, palette_swap

F = S.F
WM = 'launch.back'
FINE = 'LaunchBack turns expert knowledge into short, clean, finished reels.'
HAND = {'poses': [('glove_cut_fist_red.png', 776, 994, 18, -40, 0, 0.75), ('glove_cut_half_red.png', 811, 955, 8, -10, -15, 0.8),
                  ('glove_cut_near_red.png', 885, 935, 2, 5, -25, 0.95), ('glove_cut_open_red.png', 966, 961, 0, 10, -30, 1.05)]}
SHOTS = [
    ('S1', 'hero_word', dict(words={'kicker': 'this 8-second shot', 'hero': 'FORTY', 'q1': 'took', 'q2': 'hours', 'sub1': "you'll see", 'sub2': 'it'},
                             mark='40h', prop={'file': 'fh_reel_card.png', 'w': 540, 'h': 960, 'scale': 105})),
    ('S2', 'disc_brain', dict(words={'kicker': 'in about', 'term': 'EIGHT', 'term_accent': 'seconds'}, definition='Forty hours in. Eight seconds out.',
                              banner={'left_num': '00', 'left_word': 'zero', 'right_num': '08', 'right_word': 'eight', 'l1': 'TIMELINE', 'l2': 'Version 09 FINAL',
                                      'r1': 'RUNTIME', 'r2': '00:00:08'},
                              prop={'model': 'phone.glb', 'scale': 94, 'ry': (-12.0, 12.0)})),
    ('S3', 'word_panel', dict(words={'a': "here's the", 'b': 'same thing', 'panel': 'before it', 'big': 'CLEAN'}, layout={'plate': '#F3E7E5'})),
    ('S4', 'hand_flame', dict(words={'small': 'the real', 'big': 'mess'}, hand={'poses': [('hand_rim_open_red.png', 752, 1344, [330, 330]), ('hand_rim_mid_red.png', 752, 1344, [316, 322]),
                                                                                         ('hand_rim_pinch_red.png', 752, 1344, [300, 330])], 'times': [10, 14]})),
    ('S5', 'word_prop_pop', dict(words={'brand': 'layers.', 'small': 'FORTY', 'label': 'v9 FINAL', 'l1': 'nine versions.', 'l2': 'four', 'accent': 'deleted'},
                                 fineprint=FINE, watermark=WM, prop={'model': 'm_book.glb', 'scale': 78, 'ry': 25}, prop_tint=False, hand=HAND)),
    ('S6', 'brand_box', dict(words={'brand': 'ONE', 'tagline': 'rebuilt', 'tags': 'from scratch\nat 2am\nthe audio', 'tag_box': 'because', 'over': 'moved', 'side': 'half', 'marker': 'a second'},
                             fineprint=FINE, prop={'model': 'm_book.glb', 'scale': 110, 'ry0': 25, 'rx': 6},
                             swaps=[(('still', 'fh_alarm_clock.png', 513, 707, 34, 0.0), 50)], swap_pos=[[760, 1150]],
                             swap_ease=(S.QUAD_IN, S.QUAD_OUT), idle_turn=8.0)),
    ('S7', 'calendar_flip', dict(pages=[1, 2, 3, 4, 5], words={'brand': 'the audio', 'gives': 'changed', 'nights': 'length by', 'end': 'half', 'end_small': 'a second'}, doc='fh_versions_doc.png',
                                 prop={'file': 'fh_alarm_clock.png', 'w': 513, 'h': 707, 'width': 200})),
    ('S8', 'statement_flip', dict(words={'line': 'Nobody bought', 'accent': 'forty hours', 'small': 'they bought', 'big': '8 seconds'},
                                  watermark=WM, fineprint=FINE, scan=['fh_scan_card.png'])),
    ('S9', 'dark_docs', dict(words={'a': 'the eight seconds', 'b': 'those hours', 'c': 'made', 'd': 'possible'}, watermark=WM, fineprint=FINE,
                              docs=('fh_versions_doc.png', 'fh_wave_chart.png'))),
    ('S10', 'brain_collage', dict(words={'amp': '', 'line': 'your\nexpertise', 'small': 'runs', 'accent': 'the same way', 'label': 'You'},
                                  ring='HOURS  LAYERS  VERSIONS  HOURS  LAYERS  VERSIONS', watermark=WM, fineprint=FINE)),
    ('S11', 'flythrough_words', dict(words={'a': 'the messy', 'b': 'part is', 'c_small': 'the thing', 'c_accent': 'worth'}, layout={'bg': '#0D0707'})),
    ('S12', 'follow_needle', dict(words={'cta': 'worth', 'accent': 'paying for', 'small': 'you just\nhave to', 'big': 'Be'}, watermark=WM, fineprint=FINE,
                                  logo=('launchback_mark.png', 237, 208),
                                  layout={'bg': '#0D0707', 'accent_color': '#E10600', 'accent_band': '#5A0A08', 'needle': '#A58A8C', 'glow': '#E10600'})),
    ('S13', 'needle_solo', dict(words={'cta': 'the one', 'accent': 'who can', 'small': 'show', 'big': 'it.'}, watermark=WM, fineprint=FINE,
                                 needle={'assets': {'plate': os.path.join(HERE, '..', '..', '..', 'library', 'assets', 'needle_plate_red.png'),
                                                    'logo': os.path.join(HERE, '..', '..', '..', 'library', 'assets', 'launchback_mark.png')},
                                         'layout': {'bg': '#0D0707', 'waveDark': '#0D0707', 'accent': '#E10600', 'needle': '#A58A8C'}})),
    ('S14', 'share_card', dict(words={'line1': 'Send this', 'pill': 'SEND', 'with': 'to', 'accent': 'someone', 'who': 'who', 'bar': 'builds', 'tail': 'it'}, watermark=WM, fineprint=FINE)),
]


def build():
    p = Project()
    aeb.EASE_OVERRIDE = S.QUAD_OUT
    parts, t = [], 0.0
    for name, tpl, params in SHOTS:
        mod = importlib.import_module(f'library.templates.{tpl}')
        c = mod.build(p, name, **params)
        dur = mod.DUR_F * F
        parts.append((c, t, dur)); t += dur
    aeb.EASE_OVERRIDE = None
    m = p.comp('FORTY', dur=t)
    for c, t0, dur in reversed(parts):
        m.precomp(c, t0, t0 + dur, start=t0)
    m.finalize()
    out = os.path.join(HERE, 'forty_tpl.json')
    p.dump(out)
    d = json.load(open(out)); n = palette_swap.apply(d)
    txt = json.dumps(d).replace('KODAK PORTRA 400', 'LAUNCH.BACK 400').replace('earnera.co', 'launch.back')   # no third-party marks
    open(out, 'w').write(txt)
    print(out, f'{t:.2f}s', 'recoloured', n)
    json.dump({'names': [c.name for c, _, _ in parts], 'starts': [round(t0, 3) for _, t0, _ in parts], 'durs': [round(d_, 3) for _, _, d_ in parts]}, open(os.path.join(HERE, 'scenes.json'), 'w'))
    for c, t0, dur in parts: print(f'{c.name:5s} {t0:6.2f} {dur:5.2f}')


if __name__ == '__main__':
    build()
