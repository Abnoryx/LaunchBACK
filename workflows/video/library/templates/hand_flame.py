"""Template 'hand_flame' (reel S2b, f200-248, 49 frames): dark base, rim-lit hand holding a lit match.
Continues the word_panel fly-through: the camera has just flown in (z0 plane x4.6), RGB time split on arrival; a dark
hand with a green rim grows up from the bottom holding a match; the flame pops on with a warm glow; small line reveals
by word above it, then a big line reveals across the flame (the flame always covers the middle word); lens-blur exit.
World coordinates for the reel's camera solve (local frame = reel frame - 200)."""
from ..aeb import K, P, hexc, SCREEN, tint, mask
from .. import style as S
from .word_panel import light_sweep_edge

F = S.F
DUR_F = 49

DEFAULTS = {
    'words': {'small': 'don’t wanna', 'big': 'Let it Go'},
    'hand': ('hand_match.png', 752, 1344), 'flame': ('flame.png', 752, 1344),
    'layout': {'small': [503, 916, 0], 'big': [550, 949, 0], 'flame': [551.7, 940, 0], 'flame_scale': 4.4,
               'hand_pos': [553, 1890], 'hand_anchor': [376, 1344], 'hand_scale': 76, 'base': '#171513', 'glow': '#0A6A16',
               'hand_tint': '#273F23', 'rim': '#00FF4D', 'ink_small': '#FAF6E5', 'ink_big': '#F5EDDD'},
    'timing': {'split': (0, 13), 'hand': (2, 12), 'flame': (5, 15), 'small': (6, 16), 'big': (23, 33), 'blur_out': (38, 48)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='hand_flame', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end, motion_blur=True)
    sans = S.FONTS['sans_bold']

    S.lens_blur_out(c, (T['blur_out'][1] + 1) * F, T['blur_out'][1] - T['blur_out'][0], 20)
    sp = c.adjustment('rgb time split', T['split'][0] * F, T['split'][1] * F); c.effects(sp, P('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))
    eb = c.adjustment('edge blur', 0, end)
    c.masks(eb, mask([[535, 87], [85, 970], [530, 1835], [985, 965]], inv=True, feather=120))
    from ..aeb import gaussian
    c.effects(eb, gaussian(18))
    c.footage(proj.still('film_edge_dark.png', 1080, 1920), 0, end, blend=SCREEN)
    c.camera('camera', 0, end, S.solved_camera('scene 2', 200, 200 + DUR_F, offset=200))

    # flame above the words (it always covers the middle word), warm glow
    ff, fw, fh = Pm['flame']; fs = Lo['flame_scale']
    fl = c.footage(proj.still(ff, fw, fh), T['flame'][0] * F, end, three_d_layer=True, blend=SCREEN)
    c.transform(fl, pos=Lo['flame'], scale=K((T['flame'][0] * F, [0, 0, 0], (0.333, 0, 0, 1)), (T['flame'][1] * F, [fs, fs, fs])))
    c.effects(fl, P('Deep Glow', 'PEDG', children=[P('Exposure', 'PEDG-0002', v=0.5), P('Radius', 'PEDG-0004', v=120.0)]))
    big = c.text('big', W['big'], 0, end, sans, 82, Lo['ink_big'], tracking=-80, justify=7415, three_d_layer=True,
                 reveal=S.word_reveal(T['big'][0] * F, T['big'][1] * F))
    c.transform(big, anchor=[-1.6, -29.5, 0], pos=Lo['big'], scale=[50, 50, 50])
    sm = c.text('small', W['small'], 0, end, sans, 29, Lo['ink_small'], tracking=-80, justify=7415, three_d_layer=True,
                reveal=S.word_reveal(T['small'][0] * F, T['small'][1] * F))
    c.transform(sm, pos=Lo['small'], scale=[50, 50, 50])
    # hand: grows up from the bottom, dark with a green rim
    hf, hw, hh = Pm['hand']; hs = Lo['hand_scale']
    hd = c.footage(proj.still(hf, hw, hh), T['hand'][0] * F, end, motion_blur=True)
    c.transform(hd, anchor=Lo['hand_anchor'], pos=Lo['hand_pos'],
                scale=K((T['hand'][0] * F, [hs * 70 / 234, hs * 70 / 234], (0.333, 0, 0, 1)), (T['hand'][1] * F, [hs, hs])))
    c.effects(hd, tint('#000000', Lo['hand_tint']),
              light_sweep_edge(Lo['rim'], direction=-119, width=900, edge=120, thickness=4, center=(250, 700)))
    # dark base + green glow lower left
    gl = c.footage(proj.solid(Lo['glow'], name='glow'), 0, end)
    c.masks(gl, mask([[-300, 1300], [-300, 2300], [700, 2300], [300, 1500]], feather=500))
    c.footage(proj.solid(Lo['base'], name='base'), 0, end)
    c.finalize()
    return c
