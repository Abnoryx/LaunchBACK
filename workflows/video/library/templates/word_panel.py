"""Template 'word_panel' (reel S2 type section, f141-200, 60 frames):
'Once' snaps in from a close-up and slides left as 'something' reveals -> a dark panel rises and 'feels like it's'
rises word by word in white -> the panel wipes off upward revealing a huge dark word rising per letter on the pale plate ->
the plate wipes off upward onto a dark base with a green glow; the big word stays as a mint-rimmed outline.
2D comp pixels measured on the reel (local frame = reel frame - 141)."""
from ..aeb import K, P, hexc, SCREEN, MATTE_ALPHA, drop_shadow
from .. import style as S

F = S.F
DUR_F = 60

DEFAULTS = {
    'words': {'a': 'Once', 'b': 'something', 'panel': "feels like it’s", 'big': 'YOURS'},
    'palette': 'original',
    'layout': {'line_y': 990, 'line_size': 112, 'a_x0': 540, 'a_x1': 126, 'panel_x': 532, 'big_y': 1080, 'big_size': 330,
               'big_hscale': 1.12, 'plate': '#E2F4F5', 'panel': '#161613', 'base': '#171513', 'big_ink': '#10130F',
               'glow': '#0A6A16'},
    'timing': {'snap': (0, 10), 'slide': (5, 15), 'b': (8, 18), 'panel_up': (13, 23), 'panel_words': (15, 33),
               'panel_wipe': (31, 41), 'big': (32, 47), 'plate_wipe': (39, 49), 'base_on': 44},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def linear_wipe(t0, t1, angle=0, ease=(0.8, 0, 0.2, 1)):
    return P('Linear Wipe', 'ADBE Linear Wipe', children=[
        P('Transition Completion', 'ADBE Linear Wipe-0001', keys=[(t0, 0.0, ease), (t1, 100.0)]),
        P('Wipe Angle', 'ADBE Linear Wipe-0002', v=angle)])


def light_sweep_edge(color='#00FF52', direction=237, width=900, edge=0.73 * 100, thickness=7.6, center=(540, 1080)):
    return P('CC Light Sweep', 'CC Light Sweep', children=[
        P('Center', 'CC Light Sweep-0001', v=list(center)), P('Direction', 'CC Light Sweep-0002', v=direction),
        P('Shape', 'CC Light Sweep-0003', v=2), P('Width', 'CC Light Sweep-0004', v=width),
        P('Sweep Intensity', 'CC Light Sweep-0005', v=0), P('Edge Intensity', 'CC Light Sweep-0006', v=edge),
        P('Edge Thickness', 'CC Light Sweep-0007', v=thickness), P('Light Color', 'CC Light Sweep-0008', v=hexc(color))])


def build(proj, name='word_panel', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    sans, big_font = S.FONTS['sans_bold'], S.FONTS['hero_condensed']
    y = Lo['line_y']

    # ---------------- top: film edge (screen, amber) over the dark base once the plate is gone
    fd = proj.still('film_edge_dark.png', 1080, 1920)
    c.footage(fd, T['plate_wipe'][0] * F, end, blend=SCREEN)

    # ---------------- panel words (matted to the panel)
    pw = c.text('panel words', W['panel'], T['panel_up'][0] * F, T['panel_wipe'][1] * F, sans, Lo['line_size'], '#F2F2F2',
                tracking=-80, justify=7415,
                reveal=S.reveal_rise(T['panel_words'][0] * F, T['panel_words'][1] * F, dy=50, blur=10))
    c.transform(pw, pos=[Lo['panel_x'], y])
    panel_solid = proj.solid(Lo['panel'], name='panel')
    pn = c.footage(panel_solid, T['panel_up'][0] * F, T['panel_wipe'][1] * F)
    c.transform(pn, pos=K((T['panel_up'][0] * F, [540, 2903], S.EASE['standard']), (T['panel_up'][1] * F, [540, 960])))
    c.effects(pn, linear_wipe(T['panel_wipe'][0] * F, T['panel_wipe'][1] * F, 0))

    # ---------------- first line on the pale plate
    a = c.text('a', W['a'], 0, T['panel_up'][1] * F, sans, Lo['line_size'], '#090805', tracking=-80)
    sx0, sx1 = T['slide']
    half = Lo['line_size'] * 1.25  # 'Once' is ~2.5 em wide: scale about its centre
    c.transform(a, pos=K((sx0 * F, [Lo['a_x0'], y - Lo['line_size'] * 0.35], S.EASE['standard']), (sx1 * F, [Lo['a_x1'] + half, y - Lo['line_size'] * 0.35])),
                anchor=[half, -Lo['line_size'] * 0.35],
                scale=K((0, [220, 220], S.EASE['snap']), (T['snap'][1] * F, [100, 100])))
    b = c.text('b', W['b'], 0, T['panel_up'][1] * F, sans, Lo['line_size'], '#090805', tracking=-80,
               reveal=S.word_reveal(T['b'][0] * F, T['b'][1] * F))
    c.transform(b, pos=[Lo['a_x1'] + Lo['line_size'] * 2.62, y])

    # ---------------- big word: rises per letter on the plate, then rim-lit outline on the dark base
    big = c.text('big', W['big'], T['big'][0] * F, end, big_font, Lo['big_size'], Lo['big_ink'], justify=7415, hscale=Lo['big_hscale'],
                 reveal=S.reveal_rise(T['big'][0] * F, T['big'][1] * F, dy=115, blur=0, based_on=2))
    c.transform(big, pos=[540, Lo['big_y']])
    c.effects(big, light_sweep_edge())
    plate = proj.solid(Lo['plate'], name='plate')
    pl = c.footage(plate, 0, end)
    c.effects(pl, linear_wipe(T['plate_wipe'][0] * F, T['plate_wipe'][1] * F, 0, ease='lin'))

    # ---------------- dark base + green glow (lower left)
    glow = proj.solid(Lo['glow'], name='glow')
    gl = c.footage(glow, T['base_on'] * F, end)
    from ..aeb import mask
    c.masks(gl, mask([[-300, 1300], [-300, 2300], [700, 2300], [300, 1500]], feather=500))
    base = proj.solid(Lo['base'], name='base')
    c.footage(base, T['base_on'] * F - 5 * F, end)
    c.finalize()
    return c
