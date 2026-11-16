"""Template 'brand_box' (reel S4, f345-454, 110 frames): brand name in a frame + product.
Box splits from a bar and widens; outline brand letters gather in, fill letters pop in random order; a scrambled tagline
decodes; blinking dots + tag list; the product rises spinning into place; tag box 'invites you to'; serif-italic words over
and beside the brand while the camera pushes and pans; a marker box with a word + neon dot; black bar wipe out.
World coordinates for the reel's camera solve (local frame = reel frame - 345)."""
from ..aeb import K, P, hexc, rect_group, drop_shadow, MULTIPLY
from .. import style as S

F = S.F
DUR_F = 110

DEFAULTS = {
    'words': {'brand': 'IKEA', 'tagline': 'Good Stuff !!', 'tags': 'soft sofa\ntop rated\nlovely bed', 'tag_box': 'invites you to',
              'over': 'Sit', 'side': 'touch', 'marker': 'imagine'},
    'fineprint': 'IKEA is a global home furnishings company known for affordable, flat-pack furniture and modern Scandinavian design.',
    'prop': {'file': 'sofa.png', 'w': 1002, 'h': 985, 'width': 480},
    'palette': 'original',
    'layout': {'brand': [540, 969], 'brand_size': 317, 'box': [540, 949, 774, 278], 'tagline': [193, 1136], 'tagline_size': 43,
               'dots': [150, 140], 'tags': [160, 150], 'prop': [516, 1080, -40], 'tag_box': [540, 722, 387, 73],
               'over': [245, 1013], 'side': [794, 983], 'marker': [858, 948, 573, 170], 'paper': '#F4F4F4'},
    'timing': {'box_split': (0, 5), 'box_widen': (5, 22), 'brand_out': (6, 16), 'brand_fill': (10, 50), 'decode': (0, 46),
               'prop_rise': (0, 20), 'prop_out': (50, 65), 'tag_box': (21, 31), 'over': (33, 43), 'side': (52, 62),
               'marker': (75, 85), 'wipe': (97, 109)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def decode_animator(t0, t1, offset=11):
    """Characters show as other letters (Character Offset) until a left-to-right sweep reveals the real word."""
    sel = P('Range Selector 1', 'ADBE Text Selector', children=[
        P('Start', 'ADBE Text Percent Start', keys=[(t0, 0.0), (t1, 100.0)]),
        P('Advanced', 'ADBE Text Range Advanced', children=[P('Based On', 'ADBE Text Range Type2', v=1), P('Shape', 'ADBE Text Range Shape', v=1)])])
    return P('Animator 1', 'ADBE Text Animator', children=[P('Selectors', 'ADBE Text Selectors', children=[sel]),
                                                          P('Properties', 'ADBE Text Animator Properties', children=[P('Character Offset', 'ADBE Text Character Offset', v=offset)])])


def build(proj, name='brand_box', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T, pal = Pm['words'], Pm['layout'], Pm['timing'], S.PALETTES[Pm['palette']]
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, serif = S.FONTS['sans_bold'], S.FONTS['serif_italic']
    green, dark = '#1A922A', '#002A00'

    # ---- end wipe: black bar grows from the marker box
    mx, my, mw, mh = Lo['marker']
    w0, w1 = T['wipe']
    wipe = c.shape('wipe', w0 * F, end, [rect_group(mw, 222, color='#000000')], three_d_layer=True)
    c.transform(wipe, pos=[mx, my, 0], scale=K((w0 * F, [0, 0, 100], (0.8, 0, 0.2, 1)), ((w0 + 7) * F, [131, 100, 100]), ((w1 - 3) * F, [193, 100, 100], 'lin'), (w1 * F, [193, 900, 100])))
    S.lens_blur_in(c, 0, 5, 50)
    S.paper_finish(proj, c, 0, end, edge_blur=8)
    sl = c.adjustment('scanlines', 0, end); c.effects(sl, P('S_ScanLines', 'S_ScanLines', children=[P('Lines Angle', 'S_ScanLines-0052', v=35)]))
    fp = c.text('fineprint', Pm['fineprint'], 0, end, S.FONTS['fine_serif'], 34, '#A0A0A0', justify=7415, box=[620, 140], leading=30)
    c.transform(fp, pos=[540, 1720])
    c.camera('camera', 0, end, S.solved_camera('scene 4', 345, 345 + DUR_F, offset=345))

    # ---- marker box + word + neon dot (marker is above the side word, covering it)
    mk = c.text('marker word', W['marker'], T['marker'][1] * F, end, sans, 135, '#002800', tracking=-80, justify=7415, three_d_layer=True)
    c.transform(mk, pos=[mx - 20, my + 48, 0])
    md = c.text('marker dot', '.', T['marker'][1] * F, end, sans, 135, '#1EFF1E', three_d_layer=True)
    c.transform(md, pos=[mx + 210, my + 48, 0])
    mb = c.shape('marker box', T['marker'][0] * F, end, [rect_group(mw, mh, color='#35B749')], three_d_layer=True)
    c.transform(mb, pos=[mx, my, 0], scale=K((T['marker'][0] * F, [0, 100, 100], S.EASE['standard']), (T['marker'][1] * F, [100, 100, 100])))
    # ---- serif words with soft shadows
    for key, col in (('over', '#FFFFFF'), ('side', '#003208')):
        L = c.text(key, W[key], 0, end, serif, 238, col, tracking=-80, three_d_layer=True, reveal=S.word_reveal(T[key][0] * F, T[key][1] * F))
        c.transform(L, pos=[*Lo[key], 0]); c.effects(L, drop_shadow('#000000', 45, 135, 8, 11))
    # ---- tag box with its words
    tx, ty, tw, th = Lo['tag_box']
    tb = c.text('tag box words', W['tag_box'], 0, end, serif, 94, dark, tracking=-80, justify=7415, three_d_layer=True,
                reveal=S.word_reveal(T['tag_box'][0] * F, T['tag_box'][1] * F))
    c.transform(tb, pos=[tx, ty + 30, 0])
    bx = c.shape('tag box', T['tag_box'][0] * F, end, [rect_group(tw, th, color='#36AE4A')], three_d_layer=True)
    c.transform(bx, pos=[tx - tw / 2, ty, 0], anchor=[-tw / 2, 0], scale=K((T['tag_box'][0] * F, [0, 100, 100], (0.124, 0, 0, 1)), (T['tag_box'][1] * F, [100, 100, 100])))
    # ---- product: rises spinning into place, spins out
    pr = Pm['prop']; psc = 100 * pr['width'] / pr['w']
    px, py, pz = Lo['prop']
    sofa = c.footage(proj.still(pr['file'], pr['w'], pr['h']), 0, end, three_d_layer=True)
    r0, r1 = T['prop_rise']; o0, o1 = T['prop_out']
    c.transform(sofa, pos=K((r0 * F, [531, 1439 + 100, pz], (0.33, 0, 0, 1)), (r1 * F, [px, py, pz])), scale=[psc, psc, psc],
                ry=K((r0 * F, -83.0, (0.17, 0, 0, 1)), (r1 * F, 0.0), (o0 * F, 0.0, (0.18, 0, 0, 1)), (o1 * F, -91.0)))
    c.effects(sofa, drop_shadow('#000000', 30, 329, 12, 18))
    # ---- tagline decode, dots, tag list + rule
    tg = c.text('tagline', W['tagline'], 0, end, sans, Lo['tagline_size'], '#848484', tracking=-40, three_d_layer=True,
                reveal=decode_animator(T['decode'][0] * F, T['decode'][1] * F))
    c.transform(tg, pos=[*Lo['tagline'], 0])
    dots = c.text('dots', '■ ■ ■', 0, end, sans, 40, '#17C302', tracking=200)
    c.transform(dots, pos=Lo['dots'], op=K(*[(k * 10 * F, 100.0 if k % 2 == 0 else 15.0) for k in range(6)]))
    tags = c.text('tags', W['tags'], 0, end, S.FONTS['fine_serif'], 34, '#869A7B', leading=30)
    c.transform(tags, pos=Lo['tags'])
    rule = c.shape('rule', 0, end, [rect_group(300, 5, color='#046600')]); c.transform(rule, pos=[150, 250])
    # ---- brand: outline gathers in, fill letters pop in random order; box splits from a bar and widens
    bf = c.text('brand fill', W['brand'], 0, end, 'CoolRegular', Lo['brand_size'], green, justify=7415, three_d_layer=True,
                reveal=S.char_reveal(T['brand_fill'][0] * F, T['brand_fill'][1] * F, blur=0, ease='lin', random_seed=3))
    c.transform(bf, pos=[*Lo['brand'], 0])
    bo = c.text('brand outline', W['brand'], 0, end, 'CoolRegular', Lo['brand_size'], '#F4F4F4', justify=7415, three_d_layer=True,
                stroke='#388723', stroke_w=3, reveal=S.char_reveal(T['brand_out'][0] * F, T['brand_out'][1] * F))
    c.transform(bo, pos=[*Lo['brand'], 0])
    bxx, byy, bww, bhh = Lo['box']
    s0, s1 = T['box_split']; v0, v1 = T['box_widen']
    box = c.shape('box', 0, end, [P('Rect', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Rectangle Path 1', 'ADBE Vector Shape - Rect', children=[P('Size', 'ADBE Vector Rect Size', keys=[(s0 * F, [58, 1997]), (s1 * F, [120, bhh], (0.167, 0.167, 0, 1)), (v1 * F, [bww, bhh])])]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc('#269032')), P('Stroke Width', 'ADBE Vector Stroke Width', keys=[(s0 * F, 59.0), (s1 * F, 3.0)])])])])],
        three_d_layer=True)
    c.transform(box, pos=[bxx, byy, 0])
    S.paper(proj, c, 0, end, Lo['paper'])
    c.finalize()
    return c
