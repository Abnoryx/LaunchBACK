"""Template 'disc_brain' (reel S1b, f97-140, 44 frames): definition beat.
Whip-in from the previous shot; a kicker line reveals while a coloured disc grows behind a halftoned prop on graph paper;
dolly-in; on the beat: burst lines retract, RGB time split, the term reveals (bold sans + serif italic) and a hand-drawn
scribble loops around the italic word. Static header banner and a fine-print definition.
World coordinates for the reel's camera solve (local frame = reel frame - 97)."""
import math
from ..aeb import K, P, hexc, MULTIPLY, tint, drop_shadow, ellipse_group
from .. import style as S

F = S.F
DUR_F = 44

DEFAULTS = {
    'words': {'kicker': "it’s called", 'term': 'Endowment', 'term_accent': 'effect'},
    'definition': 'The endowment effect is overvaluing things just because you own them',
    'banner': {'left_num': '19', 'left_word': 'nineteen', 'right_num': '26', 'right_word': 'twenty-six',
               'l1': 'PERCEPTIONS', 'l2': '2024 Publication 064', 'r1': '38°EAST LONGITUDE', 'r2': '38°4′24″E'},
    'prop': {'model': 'brain_side.glb', 'scale': 94, 'ry': (-12.0, 12.0)},  # 3D brain, slow Y turn over the shot (OG 80 -> -83 over 12 s)
    'palette': 'original',
    'layout': {'kicker': [130, 742, 345], 'term': [373, 1407, 778], 'accent': [656, 1426, 770], 'kicker_size': 94,
               'term_size': 94, 'accent_size': 128, 'disc': [540, 960, 724], 'disc_size': 590, 'prop': [540, 955, 700],
               'graph': [536, 998, 1294], 'graph_width': 1340, 'disc_color': '#34B258', 'ink': '#0F0A09'},
    'timing': {'kicker': (0, 10), 'disc': (0, 20), 'burst': (18, 28), 'split': (17, 29), 'term': (17, 32), 'accent': (20, 30),
               'scribble': (22, 43)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def smooth_handles(vtx, k=1 / 6):
    """Catmull-Rom tangents for an open path: one smooth curve through every vertex instead of straight segments."""
    n = len(vtx); inn, outt = [], []
    for i in range(n):
        a, c = vtx[max(0, i - 1)], vtx[min(n - 1, i + 1)]
        tx, ty = (c[0] - a[0]) * k, (c[1] - a[1]) * k
        inn.append([-tx, -ty]); outt.append([tx, ty])
    return inn, outt


def stroke_group(vtx, color, width, trim_keys, inn=None, outt=None):
    sh = {'_shape': 1, 'closed': False, 'vtx': vtx, 'in': inn or [[0, 0]] * len(vtx), 'out': outt or [[0, 0]] * len(vtx)}
    return P('Shape', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v=sh)]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc(color)), P('Stroke Width', 'ADBE Vector Stroke Width', v=width)]),
        P('Trim Paths 1', 'ADBE Vector Filter - Trim', children=[P('Start', 'ADBE Vector Trim Start', v=0), P('End', 'ADBE Vector Trim End', keys=trim_keys)])])])


def build(proj, name='disc_brain', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T, B = Pm['words'], Pm['layout'], Pm['timing'], Pm['banner']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, serif = S.FONTS['sans_bold'], S.FONTS['serif_italic']

    S.minimax_flash(c, 0, 2, 31)
    S.minimax_flash(c, 43, 1, 35)
    sp = c.adjustment('rgb time split', T['split'][0] * F, T['split'][1] * F)
    c.effects(sp, P('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))
    # header banner + definition (2D, static)
    ink = Lo['ink']
    for txt, pos, size, col, fnt in ((B['left_num'], [70, 200], 190, ink, sans), (B['right_num'], [800, 200], 190, ink, sans),
                                     (B['left_word'], [256, 92], 28, '#9A9A9A', sans), (B['right_word'], [660, 92], 30, ink, sans),
                                     (B['l1'], [370, 188], 16, ink, sans), (B['l2'], [370, 206], 15, ink, sans),
                                     (B['r1'], [660, 188], 16, ink, sans), (B['r2'], [660, 206], 15, ink, sans)):
        L = c.text(f'banner {txt}', txt, 0, end, fnt, size, col, tracking=-40)
        c.transform(L, pos=pos)
    bar = c.shape('banner bar', 0, end, [P('Rect', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Rectangle Path 1', 'ADBE Vector Shape - Rect', children=[P('Size', 'ADBE Vector Rect Size', v=[260, 10])]),
        P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(ink))])])])])
    c.transform(bar, pos=[500, 148])
    df = c.text('definition', Pm['definition'], 0, end, S.FONTS['fine_serif'], 34, '#A1A09F', justify=7415, box=[470, 90], leading=30)
    c.transform(df, pos=[540, 1640])
    c.camera('camera', 0, end, S.solved_camera('Comp 1', 97, 97 + DUR_F, offset=97))

    # words
    k = c.text('kicker', W['kicker'], 0, end, sans, Lo['kicker_size'], ink, tracking=-80, three_d_layer=True,
               reveal=S.word_reveal(T['kicker'][0] * F, T['kicker'][1] * F))
    c.transform(k, pos=Lo['kicker'])
    tm = c.text('term', W['term'], T['term'][0] * F, end, sans, Lo['term_size'], ink, tracking=-80, three_d_layer=True, justify=7415,
                reveal=S.char_reveal(T['term'][0] * F, T['term'][1] * F))
    c.transform(tm, pos=Lo['term'])
    ac = c.text('accent', W['term_accent'], T['accent'][0] * F, end, serif, Lo['accent_size'], ink, tracking=-80, three_d_layer=True,
                reveal=S.word_reveal(T['accent'][0] * F, T['accent'][1] * F))
    c.transform(ac, pos=Lo['accent'])
    # scribble: enters left of the term, sweeps under it, ends as a loose ellipse round the accent word
    ax, ay, az = Lo['accent']
    # one hand-drawn loop round the italic word: starts top-left, goes round ~1.1 turns, slight tilt, overshoots the start
    cx, cy, rx, ry, tilt = ax + 99, ay - 22, 117, 58, -0.06
    vtx = []
    for i in range(19):
        a = math.pi * 1.12 + i * (2.2 * math.pi) / 18
        r = 1 + 0.04 * math.sin(i * 0.9)
        x, y = rx * r * math.cos(a), ry * r * math.sin(a)
        vtx.append([cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)])
    inn, outt = smooth_handles(vtx)
    sc = c.shape('scribble', T['scribble'][0] * F, end, [stroke_group(vtx, '#6E1418', 4.5, [(T['scribble'][0] * F, 0.0, (0.6, 0, 0.3, 1)), (T['scribble'][1] * F, 100.0)], inn, outt)],
                 three_d_layer=True)
    c.transform(sc, pos=[0, 0, az], anchor=[0, 0])
    # burst lines around the disc, retracting on the beat
    dx, dy, dz = Lo['disc']
    groups = []
    for i in range(13):
        a = i * 2 * math.pi / 13 + 0.2
        r0, r1 = 300 + (i % 3) * 25, 470 + (i * 37 % 5) * 30
        groups.append(stroke_group([[dx + r0 * math.cos(a), dy + r0 * math.sin(a)], [dx + r1 * math.cos(a), dy + r1 * math.sin(a)]], '#323232', 8,
                                   [(T['burst'][0] * F, 100.0, (0.015, 0, 0, 1)), (T['burst'][1] * F, 0.0)]))
    bu = c.shape('burst', T['burst'][0] * F, T['burst'][1] * F, groups, three_d_layer=True)
    c.transform(bu, pos=[0, 0, dz], anchor=[0, 0])
    # prop (halftoned, drop shadow down-left), disc, graph paper, background
    pr = Pm['prop']
    pl = c.model(proj.model(pr['model']), 0, end)
    sc_ = pr['scale']
    c.transform(pl, pos=Lo['prop'], scale=[sc_, sc_, sc_], ry=K((0, pr['ry'][0], 'lin'), (end, pr['ry'][1])))
    ht = P('BCC Halftone', 'BCC Halftone', children=[P('Cell', 'BCC Halftone-c', v=3.7), P('Ink', 'BCC Halftone-i', v=hexc('#1B1B1B')),
                                                     P('Paper', 'BCC Halftone-p', v=hexc('#E8E8E8'))])
    c.effects(pl, *([] if Pm.get('prop_plain') else [ht]), drop_shadow('#000000', 45, 196, 27, 29))
    ds = Lo['disc_size']  # draw at full size and scale 0 -> 100 (a 1 px circle scaled up rasterises soft)
    dk = c.shape('disc', 0, end, [ellipse_group(ds, ds, Lo['disc_color'])], three_d_layer=True)
    c.transform(dk, pos=Lo['disc'], anchor=[0, 0], scale=K((T['disc'][0] * F, [0, 0, 100], (0.333, 0, 0, 1)), (T['disc'][1] * F, [100, 100, 100])))
    gf = proj.still('graph_paper.png', 745, 745)
    gl = c.footage(gf, 0, end, three_d_layer=True, blend=MULTIPLY)
    gs = 100 * Lo['graph_width'] / 745
    c.transform(gl, pos=Lo['graph'], scale=[gs, gs, gs])
    c.effects(gl, tint('#5A5A5A', '#FFFFFF'))
    S.paper(proj, c, 0, end, '#FDFDFD')
    c.finalize()
    return c
