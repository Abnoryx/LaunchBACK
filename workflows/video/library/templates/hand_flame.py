"""Template 'hand_flame' (reel S2b, f200-248, 49 frames): dark base, rim-lit hand holding a lit match.
Continues the word_panel fly-through: the camera has just flown in (z0 plane x4.6), RGB time split on arrival; a dark
hand with a green rim grows up from the bottom holding a match; the flame pops on with a warm glow; small line reveals
by word above it, then a big line reveals across the flame (the flame always covers the middle word); lens-blur exit.
World coordinates for the reel's camera solve (local frame = reel frame - 200)."""
from ..aeb import K, P, hexc, SCREEN, tint, mask, fx, gaussian
from .. import style as S
from .word_panel import light_sweep_edge

F = S.F
DUR_F = 49

DEFAULTS = {
    'words': {'small': 'don’t wanna', 'big': 'Let it Go'},
    # animated footage (keyed in the engine like the OG): a hand closing round the flame, a flickering flame
    'hand': {'poses': [('hand_rim_open.png', 752, 1344, [330, 330]), ('hand_rim_mid.png', 752, 1344, [316, 322]), ('hand_rim_pinch.png', 752, 1344, [300, 330])],
             'times': [10, 14]},  # pose switches (local frames)
    'flame': ('flame_loop.mp4', 716, 1280, 73 / 24),
    'layout': {'small': [503, 916, 0], 'big': [550, 949, 0], 'flame': [551.7, 948, 0], 'flame_scale': 9.45,
               'hand_pos': [585, 1075], 'hand_anchor': [0, 0], 'hand_scale': 90, 'base': '#171513', 'glow': '#0A6A16',
               'hand_tint': '#1E2A1C', 'rim': '#00FF4D', 'ink_small': '#FAF6E5', 'ink_big': '#F5EDDD'},
    'timing': {'split': (0, 13), 'hand': (2, 12), 'flame': (5, 15), 'small': (6, 16), 'big': (21, 31), 'blur_out': (38, 48)},
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
    ff, fw, fh, fd = Pm['flame']; fs = Lo['flame_scale']
    fl = c.footage(proj.video(ff, fw, fh, fd, fps=24.0), T['flame'][0] * F, end, start=T['flame'][0] * F, three_d_layer=True, blend=SCREEN)
    c.transform(fl, pos=Lo['flame'], scale=K((T['flame'][0] * F, [0, 0, 0], (0.333, 0, 0, 1)), (T['flame'][1] * F, [fs, fs, fs])))
    c.effects(fl, P('Deep Glow', 'PEDG', children=[P('Exposure', 'PEDG-0002', v=1.2), P('Radius', 'PEDG-0004', v=120.0)]))
    # warm halo: a blurred, orange-tinted copy of the flame (the OG's Deep Glow spreads ~60-70 px round the core)
    halo = c.footage(proj.video(ff, fw, fh, fd, fps=24.0), T['flame'][0] * F, end, start=T['flame'][0] * F, three_d_layer=True, blend=SCREEN)
    c.transform(halo, pos=Lo['flame'], scale=K((T['flame'][0] * F, [0, 0, 0], (0.333, 0, 0, 1)), (T['flame'][1] * F, [fs * 1.15, fs * 1.15, fs * 1.15])))
    c.effects(halo, tint('#000000', '#FF9A2E'), gaussian(45))
    big = c.text('big', W['big'], 0, end, sans, 82, Lo['ink_big'], tracking=-80, justify=7415, three_d_layer=True,
                 reveal=S.word_reveal(T['big'][0] * F, T['big'][1] * F))
    c.transform(big, anchor=[-1.6, -29.5, 0], pos=Lo['big'], scale=[50, 50, 50])
    sm = c.text('small', W['small'], 0, end, sans, 29, Lo['ink_small'], tracking=-80, justify=7415, three_d_layer=True,
                reveal=S.word_reveal(T['small'][0] * F, T['small'][1] * F))
    c.transform(sm, pos=Lo['small'], scale=[50, 50, 50])
    # hand: grows up from the bottom, dark with a green rim
    # dark rim-lit hand (generated from the OG frame): 2D like the OG, grows up from the bottom, anchored at the pinch
    # graphic rim-lit hand as pose frames (reference-matched stills, like the OG's flat dark hand + rim): reaching
    # open -> closing -> pinched on the flame, while it grows up from the bottom; SCREEN so the black drops out
    hs = Lo['hand_scale']; poses = Pm['hand']['poses']; pt = Pm['hand']['times']
    grow = K((T['hand'][0] * F, [hs * 70 / 234, hs * 70 / 234], (0.333, 0, 0, 1)), (T['hand'][1] * F, [hs, hs]))
    edges = [T['hand'][0]] + list(pt) + [DUR_F]
    for i, (hf, hw, hh, anc) in enumerate(poses):
        hd = c.footage(proj.still(hf, hw, hh), edges[i] * F, edges[i + 1] * F, motion_blur=True, blend=SCREEN)
        c.transform(hd, anchor=anc, pos=Lo['hand_pos'], scale=grow)
    # dark base + green glow lower left
    gl = c.footage(proj.solid(Lo['glow'], name='glow'), 0, end)
    c.masks(gl, mask([[-300, 1300], [-300, 2300], [700, 2300], [300, 1500]], feather=500))
    c.footage(proj.solid(Lo['base'], name='base'), 0, end)
    c.finalize()
    return c
