"""Template 'dark_docs' (reel S7, f636-712, 77 frames): dark green documents + flare.
Tinted, blurred documents float in depth on a tilted plane (screen); a small white line + a big accent word reveal
during a snap-in, a red underline draws under the accent word, a big camera pan brings a second pair of words,
whip exit. Green optical flare at the right edge, fine diagonal scanlines, edge blur, film edge, dust.
World coordinates for the reel's camera solve (local frame = reel frame - 636)."""
import random
from ..aeb import K, P, hexc, SCREEN, mask, ellipse_group, tint, gaussian, qca
from .. import style as S

F = S.F
DUR_F = 77

DEFAULTS = {
    'words': {'a': 'let people', 'b': 'experience', 'c': 'your', 'd': 'product'},
    'watermark': 'earnera.co',
    'fineprint': 'Marketing is the process of creating, communicating, and delivering value to customers in order to build relationships and drive business growth.',
    'palette': 'original',
    'layout': {'a': [462.9, 693.8, 251], 'b': [723, 832.1, 0], 'c': [1316, 846.5, 0], 'd': [1533, 932, 0],
               'a_size': 76, 'b_size': 121, 'c_size': 76, 'd_size': 155, 'underline': [682, 960, 54.4]},
    'timing': {'a': (13, 23), 'b': (20, 30), 'line': (24, 44), 'c': (43, 53), 'd': (48, 58)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def docs_comp(proj, end):
    """The three documents in depth: Tint black->colour / white->black, blurred, screened."""
    d = proj.comp('docs', dur=end)
    chart = proj.still('chart_doc.png', 932, 600)
    census = proj.still('census_doc.png', 1128, 893)
    for name, f, pos, sc, col, blur in (('chart far', chart, [60.1, 1932.7, 1567], 297 / 2, '#009329', 10.4),
                                        ('chart near', chart, [990.4, 1480.8, 493], 297 / 2, '#046900', 14.6),
                                        ('census', census, [836.5, 486.1, 1097], 262, '#606060', 14.5)):
        L = d.footage(f, 0, end, blend=SCREEN, three_d_layer=True)
        L['name'] = name
        d.transform(L, pos=pos, scale=[sc, sc, sc])
        d.effects(L, tint(col, '#000000'), gaussian(blur))
    d.finalize()
    return d


def _ink_band(c, above, word, pos, size, font, in_f, rev, color='#014300', justify=7415):
    """Dark stripe through the lower-middle of the x-height (reel: Fill #014300 in a feathered band y -40..-15 per 121 px)."""
    k = size / 121
    L = c.text(f'{above["name"]} band', word, in_f * F, 1e9, font, size, color, tracking=-80, justify=justify, three_d_layer=True,
               motion_blur=True, reveal=S.word_reveal(rev[0] * F, rev[1] * F))
    c.layers.remove(L); c.layers.insert(c.layers.index(above), L)  # directly above the word
    c.transform(L, pos=pos)
    c.masks(L, S.mask([[-2000, -40 * k], [2000, -40 * k], [2000, -15 * k], [-2000, -15 * k]], feather=20 * k))
    return L


def build(proj, name='dark_docs', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end, motion_blur=True)
    sans = S.FONTS['sans_bold']
    ink, accent = '#F5FDEE', '#04CB00'

    # ---- top: dust, film edge (screen, amber), scanlines, edge blur, flare, lens blur in
    rnd = random.Random(3)
    dust = c.shape('dust', 0, end, [ellipse_group(rnd.uniform(1.5, 3), rnd.uniform(1.5, 3), '#E8F2E6', pos=(rnd.uniform(0, 1080), rnd.uniform(0, 1920))) for _ in range(14)], blend=SCREEN)
    c.transform(dust, anchor=[0, 0], pos=K((0, [0, 0]), (end, [8, 30])), op=60)
    fd = proj.still('film_edge_dark.png', 1080, 1920); c.footage(fd, 0, end, blend=SCREEN)
    sl = c.adjustment('scanlines', 0, end); c.effects(sl, P('S_ScanLines', 'S_ScanLines', children=[P('Lines Angle', 'S_ScanLines-0052', v=35)]))
    eb = c.adjustment('edge blur', 0, end)
    c.masks(eb, S.mask([[540, 75], [75, 958], [528, 1853], [995, 950]], inv=True, feather=120))
    c.effects(eb, gaussian(15), qca(3))
    fl = proj.solid('#000000', name='flare'); fll = c.footage(fl, 0, end)
    c.effects(fll, P('Optical Flares', 'VIDEOCOPILOT OpticalFlares', children=[
        P('Position XY', 'VIDEOCOPILOT OpticalFlares-0001', v=[1071.1, 1380.4]), P('Brightness', 'VIDEOCOPILOT OpticalFlares-0003', v=60),
        P('Scale', 'VIDEOCOPILOT OpticalFlares-0004', v=80), P('Flicker', 'VIDEOCOPILOT OpticalFlares-0050', v=1),
        P('Speed', 'VIDEOCOPILOT OpticalFlares-0051', v=40), P('Amount', 'VIDEOCOPILOT OpticalFlares-0052', v=60)]),
        tint('#000000', '#18FF00'))
    fll['blending_mode'] = SCREEN
    S.lens_blur_in(c, 0, 10, 50)
    c.camera('camera', 0, end, S.solved_camera('scene 6', 636, 636 + DUR_F, offset=636))

    # ---- words + underline (3D)
    a = c.text('a', W['a'], 0, end, sans, Lo['a_size'], ink, tracking=-80, justify=7415, three_d_layer=True, motion_blur=True,
               reveal=S.word_reveal(T['a'][0] * F, T['a'][1] * F))
    c.transform(a, pos=Lo['a'])
    b = c.text('b', W['b'], 0, end, sans, Lo['b_size'], accent, tracking=-80, justify=7415, three_d_layer=True, motion_blur=True,
               reveal=S.word_reveal(T['b'][0] * F, T['b'][1] * F))
    c.transform(b, pos=Lo['b'])
    _ink_band(c, b, W['b'], Lo['b'], Lo['b_size'], sans, 0, T['b'])
    trim = P('Trim Paths 1', 'ADBE Vector Filter - Trim', children=[
        P('Start', 'ADBE Vector Trim Start', v=0), P('End', 'ADBE Vector Trim End', keys=[(T['line'][0] * F, 0.0, S.EASE['standard']), (T['line'][1] * F, 100.0)])])
    sh = {'_shape': 1, 'closed': False, 'vtx': [[-243.7, -118.3], [319.1, -118.3]], 'in': [[0, 0], [0, 0]], 'out': [[0, 0], [0, 0]]}
    grp = P('Shape 1', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v=sh)]),
        P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc('#B20000')), P('Stroke Width', 'ADBE Vector Stroke Width', v=8)]),
        trim])])
    ul = c.shape('underline', T['line'][0] * F, end, [grp], three_d_layer=True, motion_blur=True)
    c.transform(ul, pos=Lo['underline'], anchor=[0, 0])
    cw = c.text('c', W['c'], 0, end, sans, Lo['c_size'], ink, tracking=-80, justify=7415, three_d_layer=True, motion_blur=True,
                reveal=S.word_reveal(T['c'][0] * F, T['c'][1] * F))
    c.transform(cw, pos=Lo['c'])
    dw = c.text('d', W['d'], 15 * F, end, sans, Lo['d_size'], accent, tracking=-80, justify=7415, three_d_layer=True, motion_blur=True,
                reveal=S.word_reveal(T['d'][0] * F, T['d'][1] * F))
    c.transform(dw, pos=Lo['d'])
    _ink_band(c, dw, W['d'], Lo['d'], Lo['d_size'], sans, 15, T['d'])

    # ---- watermark + fine print (2D), documents (collapsed 3D precomp), background
    wm = c.text('watermark', Pm['watermark'], 0, end, S.FONTS['serif_italic'], 78, '#1A4915', tracking=-80, justify=7415)
    c.transform(wm, pos=[541.5, 199.9])
    fp = c.text('fineprint', Pm['fineprint'], 0, end, S.FONTS['fine_serif'], 30, '#4A5F45', justify=7415, box=[610, 162], leading=28)
    c.transform(fp, pos=[561, 1629.6])
    docs = docs_comp(proj, end)
    dl = c.precomp(docs, 0, end, three_d_layer=True, collapse_transformation=True)
    c.transform(dl, pos=[926, 960, 0], ori=[355.2, 346.56, 0])
    bg = proj.solid('#070E08', name='bg'); c.footage(bg, 0, end)
    c.finalize()
    return c
