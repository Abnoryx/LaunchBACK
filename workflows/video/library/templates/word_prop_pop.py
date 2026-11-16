"""Template 'word_prop_pop' (reel S3, f249-344, 96 frames): cream paper, brand beat.
Huge serif-italic brand word reveals in random order; a hand slides in as a fist; a small line reveals; the product pops
out of the opening hand with a bouncy settle; a hand-drawn arrow points to a handwritten label; a 3-line sentence builds
under it (last word big serif italic with ink band) while a grey stroke draws and erases underneath.
2D comp pixels measured on the reel (local frame = reel frame - 249); a slow push-out camera."""
from ..aeb import K, P, hexc, rect_group, drop_shadow, tint, mask, fx as afx
from .. import style as S
from .disc_brain import stroke_group

F = S.F
DUR_F = 96

DEFAULTS = {
    'words': {'brand': 'Apple', 'small': 'let you', 'label': 'iphone 15', 'l1': 'use the phone', 'l2': 'before you', 'accent': 'buy'},
    'fineprint': 'Apple is a global technology company known for its innovative products like the iPhone, Mac, and ecosystem-driven design.',
    'watermark': 'earnera.co',
    'prop': {'model': 'iphone15.glb', 'scale': 470, 'ry': 38},  # real iPhone 15 Pro Max model (CC-BY-4.0, polyman on Sketchfab); back facing, half-spin on the pop
    # paper cut-out glove poses (Higgsfield, ref = OG frames): file, w, h, rot, dx, dy, width as a fraction of hand_w
    'hand': {'poses': [('glove_cut_fist.png', 776, 994, 18, -40, 0, 0.75), ('glove_cut_half.png', 811, 955, 8, -10, -15, 0.8),
                       ('glove_cut_near.png', 885, 935, 2, 5, -25, 0.95), ('glove_cut_open.png', 966, 961, 0, 10, -30, 1.05)]},
    'palette': 'original',
    'layout': {'brand': [93, 1088], 'brand_size': 388, 'small': [560, 900], 'small_size': 103, 'prop_rest': [529, 859],
               'label': [750, 690], 'label_size': 120, 'l1': [222, 1410], 'l1_size': 117, 'l2': [555, 1497], 'l2_size': 93,
               'accent': [477, 1560], 'accent_size': 229, 'hand': [585, 1200], 'hand_w': 380, 'paper': '#FDF9EF', 'ink': '#211F1C'},
    'timing': {'brand': (3, 23), 'hand_in': (4, 13), 'small': (16, 30), 'pop': (28, 33), 'hand_open': 29, 'arrow': (33, 43),
               'l1': (32, 42), 'label': (40, 46), 'l2': (53, 63), 'accent': (58, 68), 'path': (33, 53, 62), 'blur_out': (87, 95)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='word_prop_pop', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T, pal = Pm['words'], Pm['layout'], Pm['timing'], S.PALETTES[Pm['palette']]
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, serif, ink = S.FONTS['sans_bold'], S.FONTS['serif_italic'], Lo['ink']
    accent = '#0F8D00' if Pm['palette'] == 'original' else pal['accent']

    S.lens_blur_in(c, 0, 9, 20)
    S.lens_blur_out(c, T['blur_out'][1] * F + F, T['blur_out'][1] - T['blur_out'][0], 50)
    S.paper_finish(proj, c, 0, end, edge_blur=8)
    for txt, pos, size, col, box in ((Pm['fineprint'], [540, 250], 30, '#79756E', [585, 199]), (Pm['watermark'], [540, 1750], 44, '#BAB8B3', None)):
        L = c.text(txt[:12], txt, 0, end, S.FONTS['fine_serif'], size, col, justify=7415, box=box, leading=34)
        c.transform(L, pos=pos)
    c.camera('camera', 0, end, [(t * F, 540, 960, -1050 - 59 * min(1, t / 74), 1050) for t in range(DUR_F + 1)])

    # hand: slides in as a fist, opens under the product (drawn above product and text)
    # paper cut-out glove (generated from the OG frames): fist slides in, cuts to the open hand under the product
    # paper cut-out glove animated like stop-motion: fist slides in and wobbles, then snaps open through two
    # in-between poses (2 f each) and lands on the open pose with an overshoot; a slight idle wobble after
    hx, hy = Lo['hand']
    poses = Pm['hand']['poses']                      # [(file, w, h, rot, dx, dy, width_frac)], fist first, open last
    o0 = T['hand_open']
    times = [T['hand_in'][0]] + [o0 + 2 * i for i in range(len(poses) - 1)] + [DUR_F]
    for i, (pf, pw, ph, prot, dx, dy, wf) in enumerate(poses):
        a, b = times[i] * F, times[i + 1] * F
        L = c.footage(proj.still(pf, pw, ph), a, b, three_d_layer=True, motion_blur=True)
        sc = 100 * Lo['hand_w'] * wf / pw
        if i == 0:
            pos = K((a, [hx - 520, hy + 60, 0], S.EASE['out']), (T['hand_in'][1] * F, [hx + dx, hy + dy, 0]))
            rot = K((a, prot - 14.0, S.EASE['out']), (T['hand_in'][1] * F, prot + 4.0, (0.4, 0, 0.6, 1)), ((T['hand_in'][1] + 5) * F, prot - 2.0, (0.4, 0, 0.6, 1)), ((T['hand_in'][1] + 10) * F, prot))
            c.transform(L, pos=pos, scale=[sc, sc, sc], rot=rot)
        elif i == len(poses) - 1:
            c.transform(L, pos=[hx + dx, hy + dy, 0], scale=K((a, [sc * 1.08] * 3, (0.3, 0, 0.6, 1)), (a + 4 * F, [sc] * 3)),
                        rot=K((a, prot - 4.0, (0.4, 0, 0.6, 1)), (a + 6 * F, prot + 1.5, (0.4, 0, 0.6, 1)), (a + 14 * F, prot - 0.8, (0.4, 0, 0.6, 1)), (a + 24 * F, prot)))
        else:
            c.transform(L, pos=[hx + dx, hy + dy, 0], scale=[sc, sc, sc], rot=prot)
        c.effects(L, drop_shadow('#000000', 40, 303, 11, 19))
    # label + arrow
    lb = c.text('label', W['label'], 0, end, 'BradleyHand', Lo['label_size'], '#232323', three_d_layer=True,
                reveal=S.word_reveal(T['label'][0] * F, T['label'][1] * F))
    c.transform(lb, pos=[*Lo['label'], 0])
    px, py = Lo['prop_rest']
    ar = c.shape('arrow', T['arrow'][0] * F, end, [stroke_group([[px + 60, py - 150], [px + 120, py - 210], [px + 215, py - 195]], '#1F1F1F', 15,
                                                                [(T['arrow'][0] * F, 0.0, S.EASE['standard']), (T['arrow'][1] * F, 100.0)])], three_d_layer=True)
    c.transform(ar, anchor=[0, 0], pos=[0, 0, 0])
    # product pop + bounce (rest top y 668; peaks -50 f285, +16 f292, -8 f300, +4 f307, settled f312)
    pr = Pm['prop']
    psc = pr['scale']
    t0, t1 = T['pop']
    bounce = [(t0 * F, [px, 1171, 0], 'lin'), (t1 * F, [px, py, 0], (0.3, 0, 0.7, 1)), (36 * F, [px, py - 50, 0], (0.3, 0, 0.7, 1)),
              (43 * F, [px, py + 16, 0], (0.3, 0, 0.7, 1)), (51 * F, [px, py - 8, 0], (0.3, 0, 0.7, 1)), (58 * F, [px, py + 4, 0], (0.3, 0, 0.7, 1)), (63 * F, [px, py, 0])]
    ph = c.model(proj.model(pr['model']), t0 * F, end)
    c.transform(ph, pos=K(*bounce), scale=K((t0 * F, [0, 0, 0]), (t1 * F, [psc, psc, psc])),
                ry=K((t0 * F, pr['ry'] - 180.0, (0.2, 0, 0, 1)), (t0 * F + 18 * F, float(pr['ry']))))
    c.effects(ph, *([tint('#000000', '#C9C9C6', 100)] if Pm.get('prop_tint', True) else []), drop_shadow('#000000', 35, 240, 58, 109))
    # words
    for key, size, col, rev, font, fx in (('small', Lo['small_size'], ink, T['small'], sans, None), ('l1', Lo['l1_size'], ink, T['l1'], sans, None),
                                          ('l2', Lo['l2_size'], ink, T['l2'], sans, None)):
        L = c.text(key, W[key], 0, end, font, size, col, tracking=-80, three_d_layer=True, justify=7415 if key == 'small' else 7413,
                   reveal=S.word_reveal(rev[0] * F, rev[1] * F))
        c.transform(L, pos=[*Lo[key], 0])
    acc = c.text('accent', W['accent'], 0, end, serif, Lo['accent_size'], accent, tracking=-80, three_d_layer=True,
                 reveal=S.word_reveal(T['accent'][0] * F, T['accent'][1] * F))
    c.transform(acc, pos=[*Lo['accent'], 0])
    from .dark_docs import _ink_band
    _ink_band(c, acc, W['accent'], [*Lo['accent'], 0], Lo['accent_size'], serif, 0, T['accent'], color='#073F00', justify=7413)
    br = c.text('brand', W['brand'], 0, end, S.FONTS['didot_italic'], Lo['brand_size'], accent, three_d_layer=True,
                reveal=S.char_reveal(T['brand'][0] * F, T['brand'][1] * F, based_on=2, ease='lin', random_seed=7))
    c.transform(br, pos=[*Lo['brand'], 0])
    # grey stroke under the sentence: draws right, curls, then erases (trim end, then trim start)
    l1x, l1y = Lo['l1']
    a0, a1, a2 = T['path']
    sh = {'_shape': 1, 'closed': False, 'vtx': [[l1x, l1y + 40], [l1x + 400, l1y + 60], [l1x + 650, l1y + 80], [l1x + 700, l1y + 30], [l1x + 640, l1y + 20]],
          'in': [[0, 0], [-150, 0], [-80, 0], [0, 30], [30, 0]], 'out': [[150, 0], [80, 0], [30, -20], [-30, 0], [0, 0]]}
    grp = P('Shape', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v=sh)]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc('#868686')), P('Stroke Width', 'ADBE Vector Stroke Width', v=8)]),
        P('Trim Paths 1', 'ADBE Vector Filter - Trim', children=[P('Start', 'ADBE Vector Trim Start', keys=[(a1 * F, 0.0), (a2 * F, 100.0)]),
                                                               P('End', 'ADBE Vector Trim End', keys=[(a0 * F, 0.0), (a1 * F, 100.0)])])])])
    gp = c.shape('path', a0 * F, a2 * F, [grp], three_d_layer=True)
    c.transform(gp, anchor=[0, 0], pos=[0, 0, 0])
    S.paper(proj, c, 0, end, Lo['paper'])
    c.finalize()
    return c
