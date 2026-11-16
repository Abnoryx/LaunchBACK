"""Template 'desk_flatlay' (ours; archetype #11 top-down desk flatlay + #16 chat bubbles): a labelled object on a
cutting mat under a hard window shadow; two rounded bubbles pop in one after another (accent then white), an accent
bar draws under the object; slow top-down push + slight rotation. Local frames at 30 fps."""
from ..aeb import K, P, hexc, rect_group, drop_shadow, gaussian
from .. import style as S

F = S.F
DUR_F = 111
POP = (0.3, 1.5, 0.6, 1)
EASE = (0.8, 0, 0.2, 1)

DEFAULTS = {
    'words': {'label': 'The Michelin model', 'b1': 'Audience = the guide', 'b2': 'Money = the tyres'},
    'object': ('floppy.png', 945, 977, 46.0),        # file, w, h, scale %
    'plate': ('desk_plate.png', 752, 1344),
    'layout': {'object': [430, 1060], 'label_pos': [438, 1128], 'b1': [690, 640], 'b2': [690, 800], 'bubble_h': 104,
               'bar': [330, 1330, 300, 62], 'accent': '#E10600', 'paper': '#F6F4F0', 'ink': '#1C1C1C'},
    'timing': {'object': (0, 12), 'b1': (16, 24), 'b2': (36, 44), 'bar': (52, 68), 'push': (0, DUR_F), 'blur_out': (100, 110)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def _bubble(c, name, text, t0, t1, center, h, fill, ink, end):
    sans = S.FONTS['sans_bold']
    w = 64 + 0.52 * 50 * len(text)               # approx width for a 50 px grotesk line
    lab = c.text(name + ' text', text, t0 * F, end, sans, 50, ink, tracking=-30, justify=7415, three_d_layer=True,
                 reveal=S.word_reveal((t0 + 2) * F, (t1 + 4) * F))
    c.transform(lab, pos=[center[0], center[1] + 18, 0])
    bx = c.shape(name, t0 * F, end, [rect_group(w, h, color=fill, round_=h / 2)], three_d_layer=True)
    c.transform(bx, pos=[center[0], center[1], 0], scale=K((t0 * F, [0, 0, 100], POP), (t1 * F, [100, 100, 100])))
    c.effects(bx, drop_shadow('#000000', 40, 135, 10, 18))
    return bx


def build(proj, name='desk_flatlay', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end, motion_blur=True)
    acc, ink = Lo['accent'], Lo['ink']

    S.lens_blur_in(c, 0, 8, 20)
    S.lens_blur_out(c, (T['blur_out'][1] + 1) * F, T['blur_out'][1] - T['blur_out'][0], 30)
    p0, p1 = T['push']
    c.camera('camera', 0, end, [(t * F, 540 - 12 * t / DUR_F, 960 + 20 * t / DUR_F, -1050 + 120 * t / DUR_F, 1050) for t in range(DUR_F + 1)])

    # bubbles (second is white with dark text)
    _bubble(c, 'bubble 2', W['b2'], *T['b2'], Lo['b2'], Lo['bubble_h'], Lo['paper'], ink, end)
    _bubble(c, 'bubble 1', W['b1'], *T['b1'], Lo['b1'], Lo['bubble_h'], acc, '#FFFFFF', end)
    # accent bar with a thin dark line inside, drawing in from the left
    bx, by, bw, bh = Lo['bar']
    b0, b1 = T['bar']
    bar = c.shape('bar', b0 * F, end, [rect_group(bw, bh, color=acc, round_=8), rect_group(bw - 50, 4, color='#5A0A06', pos=(0, 4))], three_d_layer=True)
    c.transform(bar, anchor=[-bw / 2, 0], pos=[bx - bw / 2, by, 0], scale=K((b0 * F, [0, 100, 100], EASE), (b1 * F, [100, 100, 100])))
    c.effects(bar, drop_shadow('#000000', 35, 135, 8, 14))
    # the object: drops onto the mat (scale down + settle), label printed on it
    of, ow, oh, osc = Pm['object']
    o0, o1 = T['object']
    ox, oy = Lo['object']
    lbl = c.text('label', W['label'], o0 * F, end, 'TimesNewRomanPSMT', 28, '#2A2A2A', justify=7415, three_d_layer=True)
    c.transform(lbl, pos=[Lo['label_pos'][0], Lo['label_pos'][1], 0], rot=-4,
                scale=K((o0 * F, [140, 140, 100], EASE), (o1 * F, [100, 100, 100])), op=K((o0 * F, 0.0), ((o0 + 4) * F, 100.0)))
    ob = c.footage(proj.still(of, ow, oh), o0 * F, end, three_d_layer=True, motion_blur=True)
    c.transform(ob, pos=[ox, oy, 0], rot=K((o0 * F, -14.0, EASE), (o1 * F, -4.0)),
                scale=K((o0 * F, [osc * 1.4] * 3, EASE), (o1 * F, [osc] * 3)), op=K((o0 * F, 0.0), ((o0 + 4) * F, 100.0)))
    c.effects(ob, drop_shadow('#000000', 55, 135, 22, 34))
    # desk plate (3D so the camera push reads), fills the frame with margin
    pf, pw, ph = Pm['plate']
    sc = 100 * 1240 / pw
    pl = c.footage(proj.still(pf, pw, ph), 0, end, three_d_layer=True)
    c.transform(pl, pos=[540, 960, 60], scale=[sc, sc, sc], rot=K((0, -1.5, 'lin'), (end, 1.0)))
    c.footage(proj.solid('#B88A5A', name='desk'), 0, end)
    c.finalize()
    return c
