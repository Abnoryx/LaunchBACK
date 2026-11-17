"""Template 'statement_flip' (reel S6, f547-635, 89 frames).
White paper: a line soft-rises in word by word, then a serif-italic accent word; slow push-out.
2-frame invert flash -> cut to a dark scan inside a camera viewfinder (alternating slices, temporal RGB split)
with a small word + a big EXCLUSION word over it; lens-blur exit. Local frame = reel frame - 547."""
from ..aeb import K, P, EXCLUSION, MULTIPLY, tint
from .. import style as S

F = S.F
DUR_F = 89

DEFAULTS = {
    'words': {'line': "This isn’t just", 'accent': 'marketing', 'small': "it’s", 'big': 'psychology'},
    'watermark': 'earnera.co',
    'fineprint': 'Marketing is the process of creating, communicating, and delivering value to customers in order to build relationships and drive business growth.',
    'palette': 'original',
    'scan': ['mri_a.png'],  # one slice + tiny shifts: the reel's gif frames barely change, so the RGB split only fringes edges
    'layout': {'line': [544.2, 971.5], 'line_size': 95, 'accent': [564.7, 1073.5], 'accent_size': 195,
               'small': [270, 885], 'small_size': 116, 'small_hscale': 0.649, 'big': [262, 1010], 'big_size': 116, 'big_hscale': 1.14,
               'scan_c': [580, 975], 'scan_size': 1280},
    'timing': {'line': (0, 22), 'accent': (27, 45), 'flash': (51, 53), 'cut': 55, 'small': (55, 65), 'big': (60, 70), 'blur_out': (78, 88)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='statement_flip', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T, pal = Pm['words'], Pm['layout'], Pm['timing'], S.PALETTES[Pm['palette']]
    end, cut = DUR_F * F, T['cut'] * F
    c = proj.comp(name, dur=end)
    sans, serif = S.FONTS['sans_bold'], S.FONTS['serif_italic']

    # ---- top: lens blur in/out, watermark + fine print (above the invert flash, never inverted)
    lb = c.adjustment('lens blur in', 0, 11 * F)
    c.effects(lb, S.lens_blur(K((0, 50.0), (10 * F, 0.0))))
    lo = c.adjustment('lens blur out', T['blur_out'][0] * F, end)
    c.effects(lo, S.lens_blur(K((T['blur_out'][0] * F, 0.0), (T['blur_out'][1] * F, 50.0))))
    for k, (t0, t1, col_wm, col_fp, fy) in enumerate(((2 * F, cut, '#169200', '#000000', 1600), (cut, end, '#363636', '#777777', 1760))):
        wm = c.text(f'watermark {k}', Pm['watermark'], t0, t1, serif, 78, col_wm, tracking=-80, justify=7415)
        c.transform(wm, pos=[541.5, 199.9])
        fp = c.text(f'fineprint {k}', Pm['fineprint'], t0, t1, serif, 34, col_fp, justify=7415, box=[560, 120], leading=30)
        c.transform(fp, pos=[540, fy])  # centred box text is laid out around its origin

    # ---- second half (dark): words over the scan, viewfinder, temporal RGB split on the scan only
    sm = c.text('small', W['small'], cut, end, sans, Lo['small_size'], '#FFFFFF', tracking=-80, hscale=Lo['small_hscale'],
                reveal=S.word_reveal(T['small'][0] * F, T['small'][1] * F))
    c.transform(sm, pos=Lo['small'])
    bg_ = c.text('big', W['big'], cut, end, sans, Lo['big_size'], '#FFFFFF', tracking=-80, hscale=Lo['big_hscale'], blend=EXCLUSION,
                 reveal=S.word_reveal(T['big'][0] * F, T['big'][1] * F))
    c.transform(bg_, pos=Lo['big'])
    vf = proj.still('viewfinder.png', 1080, 1920)
    c.footage(vf, cut, end)
    tw = c.adjustment('rgb time split', cut, end)
    c.effects(tw, P('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))
    # scan "gif": slices alternate every ~2.7 frames with a slight jitter (that is what the RGB split catches)
    files = Pm['scan']
    stills = [proj.still(f, 1024, 1024) for f in files]
    sc = 100 * Lo['scan_size'] / 1024
    t, k = T['cut'], 0
    while t < DUR_F:
        t1 = min(DUR_F, t + (3 if k % 3 != 2 else 2))
        L = c.footage(stills[k % len(stills)], t * F, t1 * F)
        jx, jy, js = ((k * 37) % 5 - 2) * 1.5, ((k * 53) % 5 - 2) * 1.5, 1 + ((k * 29) % 5 - 2) * 0.003
        c.transform(L, pos=[Lo['scan_c'][0] + jx, Lo['scan_c'][1] + jy], scale=[sc * js, sc * js])
        t, k = t1, k + 1
    black = proj.solid('#010101', name='black'); c.footage(black, cut, end)

    # ---- first half (paper): invert flash over the line + film edge
    inv = c.adjustment('invert flash', T['flash'][0] * F, T['flash'][1] * F)
    c.effects(inv, tint('#FFFFFF', '#000000', 100))
    fe = proj.still('film_edge.png', 1080, 1920)
    c.footage(fe, 2 * F, cut, blend=MULTIPLY)
    cam_frames = [(t * F, 540, 960, -1050 - 103 * min(1, max(0, (t - 2) / 53)), 1050) for t in range(0, T['cut'] + 1)]
    c.camera('camera', 0, cut, cam_frames)
    ln = c.text('line', W['line'], 0, cut, sans, Lo['line_size'], '#000000', tracking=-80, justify=7415, three_d_layer=True,
                reveal=S.reveal_rise(T['line'][0] * F, T['line'][1] * F, dy=50, blur=30))
    c.transform(ln, pos=[*Lo['line'], 0])
    ac = c.text('accent', W['accent'], 0, cut, serif, Lo['accent_size'], '#0A9C28', tracking=-80, justify=7415, three_d_layer=True,
                reveal=(S.reveal_rise(T['accent'][0] * F, T['accent'][1] * F, dy=70, blur=14, based_on=1) if Pm.get('accent_rise') else S.word_reveal(T['accent'][0] * F, T['accent'][1] * F)))
    c.transform(ac, pos=[*Lo['accent'], 0])
    S.paper(proj, c, 0, cut, '#FDFDFD')
    c.finalize()
    return c
