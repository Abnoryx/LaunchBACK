"""Template 'follow_needle' (reel S9, f845-933, 89 frames): dark outro / call to follow.
Whip-in from the right onto a teal-black plate: a green logo mark fades down into the dark under a diagonal glow
streak; 'follow for more' reveals by word, a serif-italic accent word rises in per word; blurred pens drift in the
foreground while the camera dollies out. A white wave opens up the middle (exclusion text turns dark over it), an arm
swings in and grips a vertical needle; 'that / move the' + a huge serif-italic 'Needle' reveal; a black wave wipes out.
World coordinates for the reel's camera solve (local frame = reel frame - 845)."""
from ..aeb import K, P, hexc, SCREEN, EXCLUSION, tint, gaussian, mask, fill
from .. import style as S

F = S.F
DUR_F = 89
EASE = (0.8, 0, 0.2, 1)

DEFAULTS = {
    'words': {'cta': 'follow for more', 'accent': 'insight', 'small': 'that \nmove the', 'big': 'Needle'},
    'watermark': 'earnera.co',
    'fineprint': 'Marketing is the process of creating, communicating, and delivering value to customers in order to build relationships and drive business growth.',
    'logo': ('e_mark.png', 640, 440), 'hand': ('fist.png', 1085, 650), 'pen': ('pen.png', 762, 1117),
    'layout': {'logo': [540, 560, 783], 'logo_scale': 145, 'cta': [541, 1055, 0], 'accent': [525, 1145, -367],
               'small': [158, 1117, -972], 'big': [199, 1772, -972], 'pens': [([915, 1412, -862], 334), ([30, 1286, 0], 21)],
               'hand_pivot': [-6, 1268], 'hand_scale': 60, 'needle_x': 880, 'bg': '#001011', 'accent_color': '#37AB19',
               'accent_band': '#004E31', 'ink': '#EBEBEB', 'needle': '#7E9A7C', 'glow': '#00A777'},
    'timing': {'cta': (0, 20), 'accent_in': 13, 'accent': (21, 31), 'small': (38, 51), 'big': (51, 64), 'wave': (41, 51),
               'arm': (36, 56), 'black_wave': (76, 96)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


# vase-shaped wave outline measured on reel f896 (screen px, wave fully open): left edge down, right edge up
WAVE_L = [(207, -40), (250, 240), (255, 360), (279, 480), (327, 600), (349, 720), (344, 840), (370, 960), (420, 1080), (460, 1200),
          (480, 1320), (495, 1440), (505, 1560), (520, 1680), (535, 1800), (540, 1960)]
WAVE_R = [(883, -40), (881, 120), (845, 240), (799, 360), (785, 480), (791, 600), (771, 720), (724, 840), (693, 960), (690, 1080),
          (670, 1200), (650, 1320), (615, 1440), (600, 1560), (593, 1680), (567, 1800), (545, 1960)]


def _wave_group(color):
    """Smooth closed path through the measured outline (Catmull-Rom handles), centred on x 540 so it scales open."""
    pts = WAVE_L + WAVE_R[::-1]
    n = len(pts); vtx, inn, out = [], [], []
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        tx, ty = (c[0] - a[0]) / 6, (c[1] - a[1]) / 6
        vtx.append([b[0] - 540, b[1] - 960]); inn.append([-tx, -ty]); out.append([tx, ty])
    return P('Wave', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v={'_shape': 1, 'closed': True, 'vtx': vtx, 'in': inn, 'out': out})]),
        P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(color))])])])


def _wave_comp(proj, name, dur, color, scale):
    """The wave as its own 1080x1920 comp, so Wave Warp on the precomp layer ripples it in screen space (as the OG)."""
    wc = proj.comp(name, dur=dur, motion_blur=True)
    L = wc.shape('wave', 0, dur, [_wave_group(color)], motion_blur=True)
    wc.transform(L, pos=[540, 960], scale=scale)
    wc.finalize()
    return wc


def _wave_warp(height=40.0, width=2500.0, speed=1.0):
    """OG: height 21 / width 267.5 applied in the shape's layer space (x288 % wide, x942 % tall) = ~40 px swing, ~2500 px wavelength in screen space."""
    return P('Wave Warp', 'ADBE Wave Warp', children=[P('Wave Height', 'ADBE Wave Warp-0002', v=height), P('Wave Width', 'ADBE Wave Warp-0003', v=width),
                                                       P('Direction', 'ADBE Wave Warp-0004', v=0.0), P('Wave Speed', 'ADBE Wave Warp-0005', v=speed),
                                                       P('Pinning', 'ADBE Wave Warp-0006', v=8.0)])


def _gradient(a, b):
    return P('S_Gradient', 'S_Gradient', children=[P('Start XY', 'S_Gradient-0050', v=a), P('End XY', 'S_Gradient-0051', v=b), P('Combine', 'S_Gradient-0058', v=2.0)])


def build(proj, name='follow_needle', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end, motion_blur=True)
    sans, serif, ink = S.FONTS['sans_bold'], S.FONTS['serif_italic'], Lo['ink']

    # ---- black wave wipe out (the white wave's shape, scaled again about the frame centre)
    b0, b1 = T['black_wave']
    bw = c.precomp(_wave_comp(proj, f'{name} black wave', end, '#000000', K((b0 * F, [0, 790, 100], EASE), (b1 * F, [418, 790, 100]))), b0 * F, end)
    c.effects(bw, _wave_warp())
    c.footage(proj.still('film_edge_dark.png', 1080, 1920), 0, end, blend=SCREEN)
    for txt, pos, size, col, font, box in ((Pm['watermark'], [541, 215], 78, '#2E5E2E', serif, None),
                                           (Pm['fineprint'], [561, 1700], 27, '#6C6C6C', S.FONTS['fine_serif'], [555, 147])):
        L = c.text(txt[:12], txt, 0, end, font, size, col, tracking=-80, justify=7415, box=box, leading=24 if box else None)
        c.transform(L, pos=pos)
    c.camera('camera', 0, end, S.solved_camera('Comp 1', 845, 845 + DUR_F, offset=845))

    # ---- exclusion words (white on dark, dark over the white wave)
    big = c.text('big', W['big'], 0, end, serif, 247, ink, tracking=-80, three_d_layer=True, blend=EXCLUSION,
                 reveal=S.word_reveal(T['big'][0] * F, T['big'][1] * F))
    c.transform(big, pos=Lo['big'], scale=[142, 142, 142])
    sm = c.text('small', W['small'], 0, end, sans, 61, ink, tracking=-80, leading=61, three_d_layer=True, blend=EXCLUSION,
                reveal=S.word_reveal(T['small'][0] * F, T['small'][1] * F))
    c.transform(sm, pos=Lo['small'], scale=[142, 142, 142])
    # ---- arm swings in about the shoulder (off screen left), gripping a vertical needle
    a0, a1 = T['arm']
    hf, hw, hh = Pm['hand']; hs = Lo['hand_scale']; px, py = Lo['hand_pivot']
    rot = K((a0 * F, -50.0, EASE), (a1 * F, 0.0))
    arm = c.footage(proj.still(hf, hw, hh), a0 * F, end, motion_blur=True)
    c.transform(arm, anchor=[0, hh / 2], pos=[px, py], scale=[hs, hs], rot=rot)
    c.effects(arm, tint('#000000', '#C2C2C2'))
    nx = Lo['needle_x']
    nd = c.shape('needle', a0 * F, end, [P('Needle', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v={'_shape': 1, 'closed': False, 'vtx': [[nx, -560], [nx, 1500]], 'in': [[0, 0]] * 2, 'out': [[0, 0]] * 2})]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc(Lo['needle'])), P('Stroke Width', 'ADBE Vector Stroke Width', v=30.0)])])])],
        motion_blur=True)
    c.transform(nd, anchor=[0, hh / 2], pos=[px, py], scale=[hs, hs], rot=rot)
    # ---- white wave opens the middle
    w0, w1 = T['wave']
    wv = c.precomp(_wave_comp(proj, f'{name} white wave', end, '#F4F4F2', K((w0 * F, [0, 100, 100], EASE), (w1 * F, [100, 100, 100]))), w0 * F, end)
    c.effects(wv, _wave_warp(), gaussian(14))
    # ---- blurred pens in the foreground
    pf, pw, ph = Pm['pen']
    for pos, ori in Lo['pens']:
        L = c.footage(proj.still(pf, pw, ph), 0, end, three_d_layer=True)
        c.transform(L, pos=pos, scale=[55, 55, 55], ori=[0, 0, ori])
        c.effects(L, P('Curves', 'ADBE CurvesCustom', children=[P('Curves', 'ADBE CurvesCustom-0001', v={'_curves': 1, 'channels': {'rgb': [[0, 0], [182, 92], [255, 178]]}})]),
                  gaussian(42.1))
    # ---- accent word: rises in per word, dark band through the lower x-height
    ac0, ac1 = T['accent']
    for nm, col in (('accent band', Lo['accent_band']), ('accent', Lo['accent_color'])):
        L = c.text(nm, W['accent'], T['accent_in'] * F, end, serif, 231, col, tracking=-80, justify=7415, three_d_layer=True, motion_blur=True,
                   reveal=S.reveal_rise(ac0 * F, ac1 * F, dy=105, blur=50))
        c.transform(L, pos=Lo['accent'])
        if nm == 'accent band':
            c.masks(L, mask([[-2000, -26.8], [2000, -26.8], [2000, -9.4], [-2000, -9.4]], feather=15))
    cta = c.text('cta', W['cta'], 0, end, sans, 92, ink, tracking=-80, justify=7415, three_d_layer=True,
                 reveal=S.word_reveal(T['cta'][0] * F, T['cta'][1] * F))
    c.transform(cta, pos=Lo['cta'])
    # ---- logo mark fading down into the dark
    lf, lw, lh = Pm['logo']; ls = Lo['logo_scale']
    lg = c.footage(proj.still(lf, lw, lh), 0, end, three_d_layer=True)
    c.transform(lg, pos=Lo['logo'], scale=[ls, ls, ls]); c.effects(lg, _gradient([lw / 2, lh * 0.25], [lw / 2, lh * 1.0]))
    # ---- diagonal glow streak (2D)
    gl = c.shape('glow', 0, end, [P('Streak', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v={'_shape': 1, 'closed': False, 'vtx': [[569.06, -784.28], [-40.0, -144.0]], 'in': [[0, 0]] * 2, 'out': [[0, 0]] * 2})]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc(Lo['glow'])), P('Stroke Width', 'ADBE Vector Stroke Width', v=140.0)])])])])
    c.transform(gl, pos=[540, 810])
    c.masks(gl, mask([[-20, -440], [-448, -324], [-304, 280], [192, -16]], inv=True, feather=442))
    c.effects(gl, gaussian(60), P('Curves', 'ADBE CurvesCustom', children=[P('Curves', 'ADBE CurvesCustom-0001', v={'_curves': 1, 'channels': {'rgb': [[0, 0], [170, 105], [255, 197]]}})]))
    c.footage(proj.solid(Lo['bg'], name='plate'), 0, end)
    c.finalize()
    return c
