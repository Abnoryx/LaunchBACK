"""Template 'brain_collage' (reel S8a, f713-773, 61 frames): white collage around a top-view brain.
Whip-in from the left; a halftoned top-view brain pops out of the centre over a maths collage (graph sheet, formula
board, ruler, green card with small brain renders + a handwritten label); a ring of huge blurred numbers spins round it
in 3D; a two-line statement reveals top-left; a green line draws down from the brain and kicks right into a small line
+ big serif-italic accent word; accelerating dolly-out exit. World coordinates for the reel's camera solve
(local frame = reel frame - 713)."""
from ..aeb import K, P, hexc, MULTIPLY, tint, gaussian, drop_shadow, rect_group, fill, mask
from .. import style as S
from .disc_brain import stroke_group

F = S.F
DUR_F = 61

DEFAULTS = {
    'words': {'amp': '&', 'line': 'it becomes\ntheirs', 'small': 'In their', 'accent': 'mind', 'label': 'Brain'},
    'ring': '12 13 14 15 16 17 18 19 20 21 22 23 24 25',
    'watermark': 'earnera.co',
    'fineprint': 'Marketing is the process of creating, communicating, and delivering value to customers in order to build relationships and drive business growth.',
    'prop': {'model': 'brain.glb', 'scale': 116, 'rx': -90, 'rz': 180},  # 3D brain (top view); ring wraps round it
    'layout': {'amp': [205, 477, 0], 'line': [659, 477, 0], 'line_size': 98, 'line_leading': 61, 'small': [651, 1476, 0],
               'accent': [753, 1540, 0], 'card': [540, 960, 1094], 'card_color': '#28E27B', 'graph': [540, 960, 1079],
               'quad': [750, 770, 0], 'ruler': [540, 1272, 381], 'board': [332, 934, 0], 'prop': [540, 960, 0],
               'ring': [578, 1060, 0], 'arrow': [463, 908, 0], 'accent_color': '#00C60F', 'accent_band': '#00721C',
               'line_color': '#04A604', 'ink': '#1C1C1C'},
    'timing': {'pop': (0, 20), 'line': (3, 22), 'amp': (3, 9), 'arrow': (24, 44), 'small': (30, 40), 'accent': (35, 54)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def number_ring(proj, text, dur, name='numbers', split=None):
    """Precomp: digits stand up off a circular text path (X Rotation 90 per glyph); the ring is tilted back (X -78,
    orientation Z 31) and spins fast to 53 deg in 10 f, then crawls."""
    rc = proj.comp(name, dur=dur)
    L = rc.text('ring', text, 0, dur, S.FONTS['sans_bold'], 113, '#000000', tracking=-80, justify=7415, three_d_layer=True,
                reveal=P('Animator 1', 'ADBE Text Animator', children=[
                    P('Selectors', 'ADBE Text Selectors', children=[P('Range Selector 1', 'ADBE Text Selector', children=[])]),
                    P('Properties', 'ADBE Text Animator Properties', children=[P('X Rotation', 'ADBE Text Rotation X', v=90.0)])]))
    tp = next(p for p in L['props'] if p['m'] == 'ADBE Text Properties')
    tp['c'].append(P('Path Options', 'ADBE Text Path Options', children=[
        P('Path', 'ADBE Text Path', v=1), P('Perpendicular To Path', 'ADBE Text Perpendicular To Path', v=1.0)]))
    cx, cy, r, k = -24.5, 43.6, 291.4, 160.9
    rc.masks(L, dict(mask([[cx, cy - r], [cx - r, cy], [cx, cy + r], [cx + r, cy]], inn=[[k, 0], [0, -k], [-k, 0], [0, k]],
                          outt=[[-k, 0], [0, k], [k, 0], [0, -k]]), mode=6812))
    if split: L['depth_split'] = split
    rc.transform(L, pos=[569, 960, 0], ori=[0, 0, 31.15], rx=-78, rot=K((0, 0.0, (0.01, 0.6, 0, 1)), (10 * F, 53.0, 'lin'), (92 * F, 83.0)))
    rc.finalize()
    return rc


def build(proj, name='brain_collage', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    sans, serif, ink = S.FONTS['sans_bold'], S.FONTS['serif_italic'], Lo['ink']
    ring_near = number_ring(proj, Pm['ring'], end, f'{name} numbers near', {'pt': Lo['prop'], 'keep': 'near'})
    ring_far = number_ring(proj, Pm['ring'], end, f'{name} numbers far', {'pt': Lo['prop'], 'keep': 'far'})
    c = proj.comp(name, dur=end, motion_blur=True)

    S.paper_finish(proj, c, 0, end, edge_blur=0, edge_fringe=0, fringe=1.2)
    for txt, pos, size, col, font, box in ((Pm['watermark'], [541, 215], 78, '#0E5E00', serif, None),
                                           (Pm['fineprint'], [561, 1700], 27, '#6C6C6C', S.FONTS['fine_serif'], [555, 147])):
        L = c.text(txt[:12], txt, 0, end, font, size, col, tracking=-80, justify=7415, box=box, leading=24 if box else None)
        c.transform(L, pos=pos)
    c.camera('camera', 0, end, S.solved_camera('scene 8', 713, 713 + DUR_F, offset=713))

    # ---- words
    acc = c.text('accent', W['accent'], T['accent'][0] * F, end, serif, 164, Lo['accent_color'], tracking=-80, hscale=1.05, justify=7415,
                 three_d_layer=True, reveal=S.reveal_rise(T['accent'][0] * F, T['accent'][1] * F, dy=36, blur=30))
    c.transform(acc, pos=Lo['accent'], scale=[105, 105, 105])
    band = c.text('accent band', W['accent'], T['accent'][0] * F, end, serif, 164, Lo['accent_band'], tracking=-80, hscale=1.05, justify=7415,
                  three_d_layer=True, reveal=S.reveal_rise(T['accent'][0] * F, T['accent'][1] * F, dy=36, blur=30))
    c.transform(band, pos=Lo['accent'], scale=[105, 105, 105])
    c.masks(band, mask([[-2000, -34], [2000, -34], [2000, -12.6], [-2000, -12.6]], feather=20))
    sm = c.text('small', W['small'], 0, end, sans, 56, ink, tracking=-80, justify=7415, three_d_layer=True,
                reveal=S.word_reveal(T['small'][0] * F, T['small'][1] * F))
    c.transform(sm, pos=Lo['small'], scale=[105, 105, 105])
    ln = c.text('line', W['line'], 0, end, sans, Lo['line_size'], ink, tracking=-80, justify=7414, hscale=0.88, leading=Lo['line_leading'],
                three_d_layer=True, reveal=S.word_reveal(T['line'][0] * F, T['line'][1] * F))
    c.transform(ln, pos=Lo['line'])
    amp = c.text('amp', W['amp'], 0, end, sans, 56, ink, tracking=-80, three_d_layer=True, reveal=S.word_reveal(T['amp'][0] * F, T['amp'][1] * F))
    c.transform(amp, pos=Lo['amp'])
    # ---- number ring, near half (collapsed precomp, blurred): in front of the brain; the far half sits behind it
    rl = c.precomp(ring_near, 0, end, three_d_layer=True, collapse_transformation=True)
    c.transform(rl, pos=Lo['ring'], scale=[203, 203, 203]); c.effects(rl, gaussian(Lo.get('ring_blur', 9.0)))
    # ---- label on the green card
    lb = c.text('label', W['label'], 0, end, 'BradleyHandITC', 58, '#000000', tracking=-80, justify=7415, three_d_layer=True)
    c.transform(lb, pos=[Lo['quad'][0], Lo['quad'][1] + 5, 0])
    # ---- green line: down from under the brain, kick right into the small line
    ax, ay, az = Lo['arrow']
    ar = c.shape('arrow', 11 * F, end, [stroke_group([[ax - 29.3, ay + 265.2], [ax - 29.5, ay + 501.8], [ax + 72.6, ay + 544.1]], Lo['line_color'], 12,
                                                     [(T['arrow'][0] * F, 0.0, (0.333, 0, 0, 1)), (T['arrow'][1] * F, 100.0)])], three_d_layer=True)
    c.transform(ar, anchor=[0, 0], pos=[0, 0, az])
    # ---- the brain: pops out of the centre, darkened + halftoned
    pr = Pm['prop']; psc = pr['scale']
    br = c.model(proj.model(pr['model']), 0, end)
    c.transform(br, pos=Lo['prop'], rx=pr['rx'], rot=pr['rz'], scale=K((T['pop'][0] * F, [0, 0, 0], (0.0, 0.6, 0, 1)), (T['pop'][1] * F, [psc, psc, psc])))
    c.effects(br, tint('#000000', '#FFFFFF'),
              P('Curves', 'ADBE CurvesCustom', children=[P('Curves', 'ADBE CurvesCustom-0001', v={'_curves': 1, 'channels': {'rgb': [[0, 0], [90, 25], [170, 170], [255, 255]]}})]),
              P('BCC Halftone', 'BCC Halftone', children=[P('Cell', 'BCC Halftone-c', v=4.5), P('Ink', 'BCC Halftone-i', v=hexc('#141414')),
                                                          P('Paper', 'BCC Halftone-p', v=hexc('#F2EEEE'))]),
              drop_shadow('#000000', 50, 71, 49, 75))
    rf = c.precomp(ring_far, 0, end, three_d_layer=True, collapse_transformation=True)
    c.transform(rf, pos=Lo['ring'], scale=[203, 203, 203]); c.effects(rf, gaussian(Lo.get('ring_blur', 9.0)))
    # ---- collage behind
    fb = c.footage(proj.still('formula_board.png', 1200, 840), 0, end, three_d_layer=True, blend=MULTIPLY)
    c.transform(fb, pos=Lo['board'], scale=[51, 51, 51], rot=90)
    ru = c.footage(proj.still('ruler.png', 1280, 640), 0, end, three_d_layer=True)
    c.transform(ru, pos=Lo['ruler'], scale=[65, 65, 65])
    qf, qw, qh, qs = Pm.get('quad', ('brain_quad.png', 1024, 1024, 35))
    q = c.footage(proj.still(qf, qw, qh), 0, end, three_d_layer=True)
    c.transform(q, pos=Lo['quad'], scale=[qs, qs, qs]); c.effects(q, drop_shadow('#000000', 50, 135, 13, 56))
    gp = c.footage(proj.still('math_graph.png', 2640, 2640), 0, end, three_d_layer=True)
    c.transform(gp, pos=Lo['graph'], scale=[64.4, 64.4, 64.4])
    cd = c.shape('green card', 0, end, [rect_group(485.6, 435.8, color=Lo['card_color'], pos=(245.7, -221.6))], three_d_layer=True)
    c.transform(cd, pos=Lo['card'], scale=[167, 167, 167])
    S.paper(proj, c, 0, end, '#FDFDFD')
    c.finalize()
    return c
