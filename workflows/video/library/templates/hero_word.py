"""Template 'hero_word' (reel S1, f0-96, 97 frames):
kicker word -> giant hero word (bleeds off right) -> prop drives in under it -> 2-part question line close to camera ->
pop-in 2-line subline on the push-in -> prop exits, depth-of-field pull, whip out. Two floating 3D marks.

Inputs (all optional except words): see DEFAULTS. Layout values are world coordinates for the reel's camera solve."""
from ..aeb import K, MULTIPLY  # noqa: F401
from .. import style as S

F = S.F
DUR_F = 97

DEFAULTS = {
    'words': {'kicker': 'ever', 'hero': 'WONDER', 'q1': 'why', 'q2': 'test drive', 'sub1': 'work so', 'sub2': 'well'},
    'mark': '?',
    'prop': {'file': 'car.png', 'w': 1024, 'h': 688, 'scale': 85},
    'palette': 'original',
    'layout': {
        'kicker': [-185, 669, 671], 'hero': [-230, 1235, 671], 'hero_size': 370, 'hero_scale': [140, 163, 100],
        'q1': [524, 1110, -264], 'q2': [661, 1110, -264], 'sub1': [318, 1028, 582], 'sub2': [318, 1153, 582],
        'markB': [1137, 85, 1049], 'markB_scale': 150, 'markB_rot': 8,
        'markA': [520, 1675, 99], 'markA_scale': 125, 'markA_rot': -8,
        'prop_y': 1090, 'prop_park_x': 470, 'prop_z': 193,
    },
    'timing': {'kicker': (0.30, 0.60), 'hero': (0.567, 0.9), 'q1': (35, 45), 'q2': (36, 46), 'sub_in': 67,
               'prop_park': 0.9, 'prop_exit': (61, 81), 'dof': (67, 74), 'dof_max': 10.0},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='hero_word', **params):
    P = merge(DEFAULTS, params)
    W, Lo, T, pal = P['words'], P['layout'], P['timing'], S.PALETTES[P['palette']]
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, hero_font = S.FONTS['sans_bold'], S.FONTS['hero_condensed']

    # transitions + finish (top of stack)
    S.minimax_flash(c, 67, 2, 31)
    S.minimax_flash(c, 96, 3, 35)
    S.lens_blur_in(c, 0, 20, 20)
    S.paper_finish(proj, c, 0, end)
    c.camera('camera', 0, end, S.solved_camera('Comp 1', 0, DUR_F))

    k = c.text('kicker', W['kicker'], 0, end, sans, 131, pal['ink_soft'], tracking=-80, three_d_layer=True,
               reveal=S.word_reveal(*T['kicker']))
    c.transform(k, pos=Lo['kicker'])
    h = c.text('hero', W['hero'], 0, end, hero_font, Lo['hero_size'], pal['accent_dark'], three_d_layer=True,
               reveal=S.char_reveal(*T['hero']))
    c.transform(h, pos=Lo['hero'], scale=Lo['hero_scale'])
    dof = K((T['dof'][0] * F, 0.0), (T['dof'][1] * F, T['dof_max']))
    q1 = c.text('q1', W['q1'], 0, end, sans, 78, pal['white'], tracking=-80, three_d_layer=True,
                reveal=S.word_reveal(T['q1'][0] * F, T['q1'][1] * F))
    c.transform(q1, pos=Lo['q1'])
    c.effects(q1, _ds(35, 315, 21, 16), S.gaussian(dof))
    q2 = c.text('q2', W['q2'], 0, end, sans, 78, pal['accent'], tracking=-80, hscale=0.89, three_d_layer=True,
                reveal=S.word_reveal(T['q2'][0] * F, T['q2'][1] * F))
    c.transform(q2, pos=Lo['q2'])
    c.effects(q2, _ds(35, 305, 15, 40), S.gaussian(dof))
    s1 = c.text('sub1', W['sub1'], T['sub_in'] * F, end, sans, 98, pal['ink'], tracking=-80, three_d_layer=True)
    c.transform(s1, pos=Lo['sub1']); c.effects(s1, _ds(40, 331, 8, 26))
    s2 = c.text('sub2', W['sub2'], T['sub_in'] * F, end, sans, 171, pal['accent'], tracking=-80, three_d_layer=True)
    c.transform(s2, pos=Lo['sub2']); c.effects(s2, _ds(40, 331, 8, 26))

    S.stacked_mark(c, 'markB', P['mark'], 0, end, Lo['markB'], Lo['markB_scale'], Lo['markB_rot'], pal)
    S.stacked_mark(c, 'markA', P['mark'], 0, end, Lo['markA'], Lo['markA_scale'], Lo['markA_rot'], pal)

    pr = P['prop']
    if pr:
        f = proj.still(pr['file'], pr['w'], pr['h'])
        L = c.footage(f, 0, end, three_d_layer=True)
        y, z, px = Lo['prop_y'], Lo['prop_z'], Lo['prop_park_x']
        e0, e1 = T['prop_exit']
        c.transform(L, pos=K((0, [1693, y, z], S.EASE['standard']), (T['prop_park'], [px, y, z]),
                             (e0 * F, [px, y, z], S.EASE['standard']), (e1 * F, [-1100, y, z])),
                    scale=[pr['scale']] * 3)
        L['name'] = 'prop'
    S.paper(proj, c, 0, end, pal['paper'])
    c.finalize()
    return c


def _ds(op, direction, dist, soft):
    from ..aeb import drop_shadow
    return drop_shadow('#000000', op, direction, dist, soft)
