"""Template 'share_card' (reel S10, f934-991, 58 frames): call-to-action end card.
Phase 1 (paper): 'Share this' + dark pill word with a bounce, then 'with' + serif-italic accent word; watermark and fine print.
Phase 2 (f968+): the card shrinks onto black with an RGB split; small card with a big word, accent bar word + dot, tail word.
All positions are 2D comp pixels measured on the reel (boxes at f962 / f986)."""
from ..aeb import K, hexc, rect_group, drop_shadow, fx
from .. import style as S

F = S.F
DUR_F = 58  # f934..f991 (reel cut to black at f992)

DEFAULTS = {
    'words': {'line1': 'Share this', 'pill': 'SHARE', 'with': 'with', 'accent': 'someone',
              'who': 'who', 'bar': 'needs', 'tail': 'it'},
    'watermark': 'earnera.co',
    'fineprint': 'Marketing is the process of creating, communicating, and delivering value to customers in order to build relationships and drive business growth.',
    'palette': 'original',
    'layout': {
        'line1': [105, 884], 'line1_size': 137,
        'pill_c': [585, 969], 'pill_wh': [411, 117], 'pill_text_size': 92,
        'with': [386, 1156], 'with_size': 68, 'accent': [525, 1158], 'accent_size': 192,
        'watermark': [538, 198], 'watermark_size': 58,
        'fineprint': [540, 1600], 'fine_box': [560, 120], 'fine_size': 32,
        'card_c': [540, 959], 'card_wh': [886, 608],
        'who': [105, 848], 'who_size': 155, 'bar_box': [249, 884, 824, 1088], 'bar_text': [329, 1033], 'bar_text_size': 155,
        'tail': [774, 1193], 'tail_size': 110,
    },
    # comp-local frames (reel frame - 934)
    'timing': {'line1': (0, 6), 'pill_in': 2, 'with': (12, 18), 'accent': (18, 24), 'shrink': (34, 40), 'who': 40, 'bar': (40, 46), 'tail': 46},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='share_card', **params):
    P = merge(DEFAULTS, params)
    W, Lo, T, pal = P['words'], P['layout'], P['timing'], S.PALETTES[P['palette']]
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans = S.FONTS['sans_bold']
    t_shrink0, t_shrink1 = T['shrink'][0] * F, T['shrink'][1] * F

    # -------- phase 2 (on top once it starts): small card on black
    who = c.text('who', W['who'], T['who'] * F, end, sans, Lo['who_size'], '#0D0D0D', tracking=-80)
    c.transform(who, pos=Lo['who'])
    bt = c.text('bar text', W['bar'] + ' .', T['bar'][0] * F, end, sans, Lo['bar_text_size'], '#0D0D0D', tracking=-80)
    c.transform(bt, pos=Lo['bar_text'])
    x0, y0, x1, y1 = Lo['bar_box']
    bar = c.shape('bar', T['bar'][0] * F, end, [rect_group(x1 - x0, y1 - y0, color='#11BD00')])
    c.transform(bar, pos=[x0, (y0 + y1) / 2], anchor=[-(x1 - x0) / 2, 0],
                scale=K((T['bar'][0] * F, [0, 100], (0.7, 0, 0.3, 1)), (T['bar'][1] * F, [100, 100])))
    tail = c.text('tail', W['tail'], T['tail'] * F, end, sans, Lo['tail_size'], '#0D0D0D', tracking=-80)
    c.transform(tail, pos=Lo['tail'])
    cw, ch = Lo['card_wh']
    card = c.shape('small card', t_shrink1, end, [rect_group(cw, ch, color=pal['paper'] if False else '#F5F5F5')])
    c.transform(card, pos=Lo['card_c'])
    black = proj.solid('#000000', name='black')
    c.footage(black, t_shrink1, end)
    # card shrink onto black with the temporal RGB split (reel f968-973)
    from ..aeb import P as PP
    sh = c.adjustment('shrink', t_shrink0, t_shrink1)
    sc = 100 * Lo['card_wh'][0] / 1080
    geo = PP('Transform', 'ADBE Geometry2', children=[
        PP('Anchor Point', 'ADBE Geometry2-0001', v=[540, 960]),
        PP('Position', 'ADBE Geometry2-0002', keys=[(t_shrink0, [540, 960], (0.8, 0, 0.2, 1)), (t_shrink1, list(Lo['card_c']))]),
        PP('Scale Height', 'ADBE Geometry2-0004', keys=[(t_shrink0, 100.0, (0.8, 0, 0.2, 1)), (t_shrink1, sc)])])
    c.effects(sh, geo, PP('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))

    # -------- phase 1: paper card (finish on top of it)
    S.paper_finish(proj, c, 0, t_shrink1, edge_blur=6)  # (adjustments below 'shrink' so it shrinks the finished card)
    wm = c.text('watermark', P['watermark'], 0, end, S.FONTS['serif_italic'], Lo['watermark_size'], '#156D0A', justify=7415)
    c.transform(wm, pos=Lo['watermark'])
    fp = c.text('fineprint', P['fineprint'], 0, end, S.FONTS['fine_serif'], Lo['fine_size'], '#444444', justify=7415,
                box=Lo['fine_box'], leading=Lo['fine_size'] * 1.0)
    c.transform(fp, pos=[Lo['fineprint'][0] - Lo['fine_box'][0] / 2, Lo['fineprint'][1]])

    l1 = c.text('line1', W['line1'], 0, t_shrink1, sans, Lo['line1_size'], '#0D0D0D', tracking=-80,
                reveal=S.word_reveal(T['line1'][0] * F, T['line1'][1] * F))
    c.transform(l1, pos=Lo['line1'])
    # pill: scale 100 -> 80 -> 100 then a decaying bounce (reel: 104.4 f940, 108.4 f942, 96.1 f950, settled f970)
    t0 = T['pill_in'] * F
    bounce = K((0, [80, 80]), (t0, [80, 80], (0.33, 0, 0.67, 1)), (t0 + 6 * F, [108.4, 108.4], (0.33, 0, 0.67, 1)),
               (t0 + 14 * F, [96.1, 96.1], (0.33, 0, 0.67, 1)), (t0 + 22 * F, [101.5, 101.5], (0.33, 0, 0.67, 1)), (t0 + 32 * F, [100, 100]))
    pw, ph = Lo['pill_wh']
    pt = c.text('pill text', W['pill'], 0, t_shrink1, S.FONTS['pill'], Lo['pill_text_size'], '#FFFFFF', tracking=135,
                justify=7415, vscale=0.78)
    c.transform(pt, pos=[Lo['pill_c'][0], Lo['pill_c'][1] + Lo['pill_text_size'] * 0.3], scale=bounce)
    pill = c.shape('pill', 0, t_shrink1, [rect_group(pw, ph, color='#1E1E1E', round_=ph / 2)])
    c.transform(pill, pos=Lo['pill_c'], scale=bounce)
    c.effects(pill, drop_shadow('#000000', 45, 229, 24, 28))
    wi = c.text('with', W['with'], 0, t_shrink1, sans, Lo['with_size'], '#0D0D0D', tracking=-80,
                reveal=S.word_reveal(T['with'][0] * F, T['with'][1] * F))
    c.transform(wi, pos=Lo['with'])
    ac = c.text('accent', W['accent'], 0, t_shrink1, S.FONTS['serif_italic'], Lo['accent_size'], '#289B0C', tracking=-80,
                reveal=S.word_reveal(T['accent'][0] * F, T['accent'][1] * F))
    c.transform(ac, pos=Lo['accent'])
    S.paper(proj, c, 0, t_shrink1, '#F5F5F5')
    c.finalize()
    return c
