"""Template 'pill_diagram' (new; archetype #18 from the creator's r4/r5): one idea splits into two outcomes.
Dark plate; a glowing node pulses in, two curved lines draw down to two glowing accent pills (label inside); a 3D
prop rises under each pill as its line of VO lands; the top line swaps from the first statement to the second.
Words: 'a1' + red italic 'a2' (left half of the VO), then 'b1' + 'b2' (right half). Local frames at 30 fps."""
from ..aeb import K, P, hexc, SCREEN, rect_group, ellipse_group, gaussian, drop_shadow
from .. import style as S
from .disc_brain import stroke_group, smooth_handles

F = S.F
DUR_F = 96
EASE = (0.8, 0, 0.2, 1)
POP = (0.3, 1.5, 0.6, 1)

DEFAULTS = {
    'words': {'a1': 'Their audience was', 'a2': 'the guide.', 'b1': 'Their money was', 'b2': 'the tyres.',
              'pill_a': 'AUDIENCE', 'pill_b': 'MONEY'},
    'props': {'a': ('m_book.glb', 58, 0.0), 'b': ('m_tyre.glb', 62, 0.0)},   # model, scale %, base ry
    'layout': {'node': [540, 760], 'pill_a': [300, 1120], 'pill_b': [780, 1120], 'pill': [400, 112], 'line_y': 470,
               'prop_y': 1460, 'accent': '#E10600', 'glow': '#FF2A1A', 'bg': '#0A0A0B', 'ink': '#F2EFEA'},
    'timing': {'node': (0, 6), 'lines': (6, 20), 'a': (2, 14), 'pill_a': (16, 24), 'prop_a': (20, 34), 'swap': 44,
               'b': (46, 58), 'pill_b': (52, 60), 'prop_b': (56, 70), 'push': (0, DUR_F)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='pill_diagram', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end, motion_blur=True)
    sans, serif, acc, ink = S.FONTS['sans_bold'], S.FONTS['serif_italic'], Lo['accent'], Lo['ink']
    nx, ny = Lo['node']
    pw, ph = Lo['pill']

    S.lens_blur_out(c, end, 8, 30)
    c.footage(proj.still('film_edge_dark.png', 1080, 1920), 0, end, blend=SCREEN)
    c.camera('camera', 0, end, [(t * F, 540, 960, -1050 + 60 * t / DUR_F, 1050) for t in range(DUR_F + 1)])

    # top line: first statement, swapped for the second (per-word blur-in both)
    for key, (t0, t1), out in (('a', T['a'], T['swap']), ('b', T['b'], end / F)):
        L = c.text(key + '1', W[key + '1'], t0 * F, out * F, sans, 78, ink, tracking=-60, justify=7415, three_d_layer=True,
                   reveal=S.word_reveal(t0 * F, t1 * F))
        c.transform(L, pos=[540, Lo['line_y'], 0])
        L2 = c.text(key + '2', W[key + '2'], t0 * F, out * F, serif, 150, acc, tracking=-80, justify=7415, three_d_layer=True,
                    reveal=S.word_reveal((t0 + 4) * F, (t1 + 4) * F))
        c.transform(L2, pos=[540, Lo['line_y'] + 150, 0])
    # props rising under each pill
    for key, pk in (('a', 'prop_a'), ('b', 'prop_b')):
        mf, msc, ry = Pm['props'][key]
        px = Lo['pill_' + key][0]
        t0, t1 = T[pk]
        m = c.model(proj.model(mf), t0 * F, end)
        c.transform(m, pos=K((t0 * F, [px, Lo['prop_y'] + 260, 0], EASE), (t1 * F, [px, Lo['prop_y'], 0])),
                    scale=K((t0 * F, [0, 0, 0], POP), ((t0 + 8) * F, [msc] * 3)),
                    ry=K((t0 * F, ry - 120.0, (0.2, 0, 0, 1)), (t1 * F, ry), ((t1 + 1) * F, ry, 'lin'), (end, ry + 25.0)))
        c.effects(m, drop_shadow('#000000', 60, 180, 25, 40))
    # pills: glow copy (blurred, screen) + crisp outline + label
    for key in ('a', 'b'):
        x, y = Lo['pill_' + key]
        t0, t1 = T['pill_' + key]
        lab = c.text('pill label ' + key, W['pill_' + key], t0 * F, end, sans, 54, ink, tracking=60, justify=7415)
        c.transform(lab, pos=[x, y + 19], scale=K((t0 * F, [0, 0], POP), (t1 * F, [100, 100])))
        for glow in (True, False):
            g = c.shape(f'pill {key}{" glow" if glow else ""}', t0 * F, end,
                        [rect_group(pw, ph, color='#2A0505' if not glow else None, stroke=Lo['glow'] if glow else acc, stroke_w=14 if glow else 5, round_=ph / 2)],
                        blend=SCREEN if glow else 5212)
            c.transform(g, pos=[x, y], scale=K((t0 * F, [0, 0], POP), (t1 * F, [100, 100])))
            if glow:
                c.effects(g, gaussian(26))
            c.layers.remove(g); c.layers.insert(c.layers.index(lab) + 1, g)
    # lines from the node to each pill (smooth curves, drawn with trim)
    l0, l1 = T['lines']
    groups = []
    for key in ('a', 'b'):
        x, y = Lo['pill_' + key]
        vtx = [[nx, ny + 30], [nx + (x - nx) * 0.15, ny + 160], [x, y - ph / 2 - 150], [x, y - ph / 2]]
        inn, outt = smooth_handles(vtx)
        groups.append(stroke_group(vtx, acc, 6, [(l0 * F, 0.0, EASE), (l1 * F, 100.0)], inn, outt))
    ln = c.shape('lines', l0 * F, end, groups)
    c.transform(ln, anchor=[0, 0], pos=[0, 0])
    # node: glowing dot, pulses in
    n0, n1 = T['node']
    for glow in (True, False):
        d = c.shape('node' + (' glow' if glow else ''), n0 * F, end, [ellipse_group(70 if glow else 34, 70 if glow else 34, Lo['glow'] if glow else acc)],
                    blend=SCREEN if glow else 5212)
        c.transform(d, pos=[nx, ny], scale=K((n0 * F, [0, 0], POP), (n1 * F, [100, 100])))
        if glow:
            c.effects(d, gaussian(30))
    c.footage(proj.solid(Lo['bg'], name='plate'), 0, end)
    c.finalize()
    return c
