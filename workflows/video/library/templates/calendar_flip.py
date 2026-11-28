"""Template 'calendar_flip' (reel S5, f455-546, 92 frames): green room, page-turn counter.
Slam-in onto a calendar card in a green room with diagonal blind shadows; pages flip 1 -> 10 -> 30 -> 50 -> 100
(dark flap, ~5 f per flip); a serif-italic brand word + 'gives you' reveal; pan right with a foreground prop in parallax;
'nights to', then an oblique line 'sleep on it'; lens-blur exit. World coordinates for the reel's camera solve
(local frame = reel frame - 455). Page turn is drawn as a moving fold: per-frame clip mask + dark flap polygon."""
import math
from ..aeb import K, P, hexc, SCREEN, MULTIPLY, tint, gaussian, drop_shadow, mask
from .. import style as S

F = S.F
DUR_F = 92
CW, CH = 827, 956

DEFAULTS = {
    'pages': [1, 10, 30, 50, 100],
    'words': {'brand': 'Casper', 'gives': 'gives you', 'nights': 'nights to', 'end': 'sleep', 'end_small': 'on it'},
    'prop': {'file': 'bed.png', 'w': 1145, 'h': 879, 'width': 300},
    'layout': {'card': [545, 960, 777], 'card_scale': 129, 'brand': [250, 622, -294], 'gives': [407, 676, -294],
               'nights': [995, 997, 0], 'end': [808, 1110, 0], 'end_small': [1120, 1110, 0], 'prop': [711, 1187, -563], 'prop_rot': -18,
               'bg': '#27623D', 'flap': '#10201C'},
    # flips (local frames): (curl starts, fast sweep starts, fold mid-page, flap gone off the card)
    'timing': {'flips': [(2, 9, 13, 17), (21, 22, 24, 27), (31, 32, 34, 37), (41, 42, 44, 47)], 'brand': (16, 18),
               'gives': (29, 33), 'nights': (46, 50), 'end': (68, 71), 'end_small': (72, 76), 'split': (0, 12),
               'blur_out': (81, 91)},
    # window light: everything outside these screen polygons is in shadow (static, 2D; measured on reel f472/f520)
    'light': [[[900, 0], [1080, 0], [1080, 680], [210, 1050], [130, 1050], [120, 560]],
              [[1080, 790], [690, 958], [330, 1200], [330, 1300], [480, 1500], [750, 1450], [1080, 1350]]],
    'shadow': '#484A55',
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def _clip(poly, n, c):
    """Keep the part of polygon `poly` where dot(p, n) >= c (Sutherland-Hodgman, one plane)."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = a[0] * n[0] + a[1] * n[1] - c, b[0] * n[0] + b[1] * n[1] - c
        if da >= 0: out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db); out.append([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])])
    return out


def _fold_d(f, c0, c1, mid, end):
    """Fold distance from the corner along the diagonal (fraction of it): slow curl, then an accelerating sweep."""
    if f <= c1: return 0.02 + 0.13 * max(0, f - c0) / max(1, c1 - c0)
    if f <= mid: u = (f - c1) / (mid - c1); return 0.15 + 0.35 * u * u
    return 0.5 + 1.3 * ((f - mid) / (end - mid)) ** 1.3


def page_turn_frames(c0, c1, mid, end):
    """Per-frame (time, visible polygon, flap polygon) for a fold sweeping from the top-right corner to past the
    bottom-left one, in card-local pixels. The flap (the turned corner, reflected) is not clipped to the card."""
    rect = [[0, 0], [CW, 0], [CW, CH], [0, CH]]
    corner = (CW, 0)
    # the fold line stays parallel to the other diagonal (TL-BR), so at mid-turn the flap is exactly the lower-left half
    D = math.hypot(CW, CH); dirn = (-CH / D, CW / D)
    L = 2 * CW * CH / D  # corner-to-corner travel along the fold normal
    out = []
    for f in range(c0, end + 1):
        d = _fold_d(f, c0, c1, mid, end) * L
        cdot = corner[0] * dirn[0] + corner[1] * dirn[1] + d
        vis = _clip(rect, dirn, cdot)
        cut = _clip(rect, (-dirn[0], -dirn[1]), -cdot)
        # reflect the cut-off corner across the fold line -> the flap lying on the page
        flap = []
        for p in cut:
            s_ = p[0] * dirn[0] + p[1] * dirn[1] - cdot
            flap.append([p[0] - 2 * s_ * dirn[0], p[1] - 2 * s_ * dirn[1]])
        out.append(((f - 0.5) * F, vis, flap))  # half a frame early so frame f samples its own key
    return out


def build(proj, name='calendar_flip', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, serif = S.FONTS['sans_bold'], S.FONTS['serif_italic']

    S.lens_blur_in(c, 0, 10, 20)
    S.lens_blur_out(c, T['blur_out'][1] * F + F, T['blur_out'][1] - T['blur_out'][0], 50)
    sp = c.adjustment('rgb split in', T['split'][0] * F, T['split'][1] * F); c.effects(sp, P('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))
    eb = c.adjustment('edge blur', 0, end)
    c.masks(eb, mask([[540, 75], [75, 958], [528, 1853], [995, 950]], inv=True, feather=120))
    c.effects(eb, gaussian(15))
    c.camera('camera', 0, end, S.solved_camera('scene 5', 455, 455 + DUR_F, offset=455))

    # words (lit by the window, so above the shadow layer)
    es = c.text('end_small', W['end_small'], T['end_small'][0] * F, end, sans, 75, '#FFFFFF', tracking=-60, three_d_layer=True,
                reveal=S.word_reveal(T['end_small'][0] * F, T['end_small'][1] * F))
    c.transform(es, pos=Lo['end_small'])
    w_end = c.text('end', W['end'], T['end'][0] * F, end, 'HelvReal-BoldOblique', 121, '#F3FCF0', tracking=-60, three_d_layer=True,
                   stroke='#101010', stroke_w=4, reveal=S.word_reveal(T['end'][0] * F, T['end'][1] * F))
    c.transform(w_end, pos=Lo['end']); c.effects(w_end, drop_shadow('#000000', 85, 135, 6, 6))
    nt = c.text('nights', W['nights'], T['nights'][0] * F, end, sans, 75, '#FFFFFF', tracking=-60, three_d_layer=True,
                reveal=S.word_reveal(T['nights'][0] * F, T['nights'][1] * F))
    c.transform(nt, pos=Lo['nights'])
    gv = c.text('gives', W['gives'], T['gives'][0] * F, end, sans, 87, '#FFFFFF', tracking=-60, three_d_layer=True,
                reveal=S.word_reveal(T['gives'][0] * F, T['gives'][1] * F))
    c.transform(gv, pos=Lo['gives'])
    br = c.text('brand', W['brand'], 0, end, serif, 184, '#FFFFFF', tracking=-80, hscale=0.76, three_d_layer=True,
                reveal=S.word_reveal(T['brand'][0] * F, T['brand'][1] * F))
    c.transform(br, pos=Lo['brand'])
    # window shadow: full frame minus the lit polygons, multiplied over the scene
    sh = c.footage(proj.solid(Pm['shadow'], name='window shadow'), 0, end, blend=MULTIPLY)
    c.masks(sh, mask([[-50, -50], [1130, -50], [1130, 1970], [-50, 1970]]), *[mask(poly, mode=6814, feather=24) for poly in Pm['light']])
    # foreground prop (parallax)
    pr = Pm['prop']; psc = 100 * pr['width'] / pr['w']
    bed = c.footage(proj.still(pr['file'], pr['w'], pr['h']), 0, end, three_d_layer=True)
    c.transform(bed, pos=Lo['prop'], scale=[psc, psc, psc], rot=Lo['prop_rot'])
    c.effects(bed, drop_shadow('#000000', 50, 274, 38, 31))
    # calendar: top page first; each page turns, revealing the next
    cx, cy, cz = Lo['card']; sc = Lo['card_scale']
    pages = Pm['pages']
    for i, num in enumerate(pages):
        f = proj.still(f'calendar_{num}.png', CW, CH)
        t_out = end
        if i < len(T['flips']):
            frames = page_turn_frames(*T['flips'][i])
            t_out = (T['flips'][i][3] + 1) * F
            # flap above the page
            fk_vis = [(t, {'_shape': 1, 'closed': True, 'vtx': flap or [[0, 0], [0, 0], [0, 0]], 'in': [[0, 0]] * max(3, len(flap)), 'out': [[0, 0]] * max(3, len(flap))}, 'hold')
                      for t, _, flap in frames]
            flap_grp = P('Flap', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
                P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', keys=fk_vis)]),
                P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(Lo['flap']))])])])
            fl = c.shape(f'flap {num}', frames[0][0], (T['flips'][i][3] + 1) * F, [flap_grp], three_d_layer=True)
            c.transform(fl, pos=[cx, cy, cz - 0.5 - i * 0.01], anchor=[CW / 2, CH / 2], scale=[sc, sc, sc])
            t_out = next((t for t, vis, _ in frames if len(vis) < 3), t_out)  # page fully turned: hide it
            frames = [fr for fr in frames if len(fr[1]) >= 3]
        L = c.footage(f, 0, t_out, three_d_layer=True)
        c.transform(L, pos=[cx, cy, cz + i * 0.01], scale=[sc, sc, sc])
        if i < len(T['flips']):
            mk = mask([[0, 0], [CW, 0], [CW, CH], [0, CH]])
            mk['c'][0] = P('Mask Path', 'ADBE Mask Shape', keys=[(t, {'_shape': 1, 'closed': True, 'vtx': vis, 'in': [[0, 0]] * len(vis), 'out': [[0, 0]] * len(vis)}, 'hold') for t, vis, _ in frames])
            c.masks(L, mk)
        if i == len(pages) - 1:
            c.effects(L, drop_shadow('#000000', 45, 220, 17, 54))
    # background: dim document behind everything, green room
    doc = c.footage(proj.still(Pm.get('doc', 'census_doc.png'), 1128, 893), 0, end, three_d_layer=True, blend=SCREEN)
    c.transform(doc, pos=[540, 760, 874], scale=[241, 241, 241]); c.effects(doc, tint('#4B4B4B', '#000000'))
    bg = proj.solid(Lo['bg'], name='green room'); c.footage(bg, 0, end)
    c.finalize()
    return c
