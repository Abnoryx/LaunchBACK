"""Template 'flythrough_words' (reel S8b, f774-844, 71 frames): dark dust room.
A short line snaps back from close-up; a 2-word line flies in from behind the camera while revealing; a
small-word + serif-italic line flies in from the lower left; hold; whip exit to the right.
Soft light shafts from the top, drifting dust specks, warm off-white text with a soft bloom.
World coordinates for the reel's camera solve (local frame = reel frame - 774)."""
import random
from ..aeb import K, P, hexc, SCREEN, mask, ellipse_group, drop_shadow
from .. import style as S

F = S.F
DUR_F = 71

DEFAULTS = {
    'words': {'a': "that’s how", 'b': 'you sell', 'c_small': 'without', 'c_accent': 'selling'},
    'layout': {'a': [439.8, 911.4, 0], 'b': [625.1, 1005.9, -890], 'c': [413.5, 1063.1, -1317], 'size': 82,
               'c_small_size': 37, 'c_accent_size': 141, 'c_gap': 150, 'ink': '#E6DED8', 'bg': '#001011'},
    'timing': {'b': (11, 21), 'c': (24, 34)},
    'dust_seed': 7,
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def bloom():
    # Looks gives the text a soft warm halo (~6-10 px)
    return drop_shadow('#FFF1E8', 30, 0, 0, 14)


def build(proj, name='flythrough_words', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, serif = S.FONTS['sans_bold'], S.FONTS['serif_italic']

    q = c.adjustment('fringe', 0, end); c.effects(q, S.qca(1.0))
    c.camera('camera', 0, end, S.solved_camera('scene 8', 774, 774 + DUR_F, offset=774))

    a = c.text('a', W['a'], 0, end, sans, Lo['size'], Lo['ink'], tracking=-80, three_d_layer=True)
    c.transform(a, pos=Lo['a']); c.effects(a, bloom())
    b = c.text('b', W['b'], 0, end, sans, Lo['size'], Lo['ink'], tracking=-80, three_d_layer=True,
               reveal=S.word_reveal(T['b'][0] * F, T['b'][1] * F))
    c.transform(b, pos=Lo['b']); c.effects(b, bloom())
    cx, cy, cz = Lo['c']
    cs = c.text('c small', W['c_small'], 0, end, sans, Lo['c_small_size'], Lo['ink'], tracking=-80, three_d_layer=True,
                reveal=S.word_reveal(T['c'][0] * F, T['c'][1] * F))
    c.transform(cs, pos=[cx, cy, cz]); c.effects(cs, bloom())
    ca = c.text('c accent', W['c_accent'], 0, end, serif, Lo['c_accent_size'], Lo['ink'], tracking=-80, three_d_layer=True,
                reveal=S.word_reveal(T['c'][0] * F + 2 * F, T['c'][1] * F + 2 * F))
    c.transform(ca, pos=[cx + Lo['c_gap'], cy, cz]); c.effects(ca, bloom())

    # dust: 2-4 px specks drifting slowly (screen)
    rnd = random.Random(Pm['dust_seed'])
    specks = []
    for i in range(36):
        x, y, s = rnd.uniform(-40, 1120), rnd.uniform(-40, 1960), rnd.uniform(2, 4.5)
        specks.append(ellipse_group(s, s, '#DDEFF0' if i % 3 else '#9FD3D8', pos=(x, y)))
    dust = c.shape('dust', 0, end, specks, blend=SCREEN)
    c.transform(dust, pos=K((0, [0, 0]), (end, [rnd.uniform(-25, 25), 40])), anchor=[0, 0], op=70)
    # light shafts from the top (centre x ~375, ~360 px wide at y 300, fading by y ~1100; a fainter one right of centre)
    for i, (x0, w, op) in enumerate(((375, 360, 100), (760, 260, 45))):
        sh = proj.solid('#293336', name=f'shaft {i}')
        L = c.footage(sh, 0, end, blend=SCREEN)
        c.masks(L, mask([[x0 - w * 0.35, -200], [x0 + w * 0.35, -200], [x0 + w * 0.75, 1250], [x0 - w * 0.75, 1250]], feather=180))
        c.transform(L, op=op)
    bg = proj.solid(Lo['bg'], name='bg')
    c.footage(bg, 0, end)
    c.finalize()
    return c
