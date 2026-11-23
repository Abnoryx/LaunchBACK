"""Template 'logo_reveal': the LaunchBack logo assembles itself (pieces from make_logo.py).
The up-arrow draws up from its base, the diagonal arrow launches in along its own direction with a red motion trail,
the B's lower chevron snaps on as the arrow lands (RGB-split hit), then LAUNCH pops in per letter and BACK follows
lighter; slow push-in hold. Mark in the accent colour, wordmark white. Local frames at 30 fps."""
import json, os
from ..aeb import K, P, hexc, mask, gaussian, tint, SCREEN
from .. import style as S

F = S.F
DUR_F = 105
LOGO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'logo')
SRC_CX, SRC_CY = 704, 384          # centre of the logo artwork in source px
EASE_OUT = (0.15, 0.85, 0.25, 1)    # fast launch, soft landing
POP = (0.3, 1.6, 0.6, 1)            # overshoot

DEFAULTS = {
    'scale': 0.82, 'center': [540, 960], 'accent': '#E10600', 'ink': '#F4F4F2', 'bg': None,
    'timing': {'up': (0, 10), 'arrow': (6, 17), 'bowl': (15, 20), 'hit': (16, 20), 'launch': (19, 2), 'back': (31, 2),
               'push': (0, DUR_F)},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='logo_reveal', **params):
    Pm = merge(DEFAULTS, params)
    T, sc, acc, ink = Pm['timing'], Pm['scale'], Pm['accent'], Pm['ink']
    pieces = json.load(open(os.path.join(LOGO, 'pieces.json')))
    end = DUR_F * F
    lc = proj.comp(f'{name} art', dur=end, motion_blur=True)
    cx, cy = 540, 960

    def place(nm):
        x0, y0, x1, y1 = pieces[nm]
        w, h = x1 - x0, y1 - y0
        f = proj.still(f'logo/{nm}.png', w, h)
        pos = [cx + ((x0 + x1) / 2 - SRC_CX) * sc, cy + ((y0 + y1) / 2 - SRC_CY) * sc]
        return f, w, h, pos

    # wordmark: BACK (lighter, later) then LAUNCH, per letter pop
    for word, letters, (t0, step), op in (('back', ['B', 'A2', 'C2', 'K'], T['back'], 100), ('launch', ['L', 'A', 'U', 'N', 'C', 'H'], T['launch'], 100)):
        for i, ltr in enumerate(letters):
            f, w, h, pos = place('l_' + ltr)
            a = (t0 + i * step) * F
            L = lc.footage(f, a, end, motion_blur=True)
            lc.transform(L, pos=K((a, [pos[0], pos[1] + 26 * sc], POP), (a + 6 * F, pos)), scale=K((a, [40 * sc, 40 * sc], POP), (a + 6 * F, [100 * sc, 100 * sc])),
                         op=K((a, 0.0), (a + 3 * F, float(op))))
            lc.effects(L, tint('#000000', ink), P('Gaussian Blur', 'ADBE Gaussian Blur 2', children=[
                P('Blurriness', 'ADBE Gaussian Blur 2-0001', keys=[(a, 14.0), (a + 5 * F, 0.0)])]))
    # B lower chevron: snaps on as the arrow lands
    f, w, h, pos = place('mark_bowl')
    b0, b1 = T['bowl']
    L = lc.footage(f, b0 * F, end)
    lc.transform(L, pos=pos, scale=K((b0 * F, [0, 0], POP), (b1 * F, [100 * sc, 100 * sc])))
    lc.effects(L, tint('#000000', acc))
    # diagonal arrow: launches in along its own 45 deg direction, with a blurred red trail lagging 2 f
    f, w, h, pos = place('mark_arrow')
    a0, a1 = T['arrow']
    far = 900
    for lag, op, blur in ((2, 55.0, 14.0), (0, 100.0, 0.0)):
        L = lc.footage(f, (a0 + lag) * F, end, motion_blur=True)
        lc.transform(L, pos=K(((a0 + lag) * F, [pos[0] - far, pos[1] + far], EASE_OUT), ((a1 + lag) * F, pos)), scale=[100 * sc, 100 * sc],
                     op=K(((a0 + lag) * F, op), ((a1 + lag + 3) * F, op if lag == 0 else 0.0)))
        lc.effects(L, tint('#000000', acc), *([gaussian(blur)] if blur else []))
    # up-arrow: draws up from its base (mask grows bottom -> top)
    f, w, h, pos = place('mark_up')
    u0, u1 = T['up']
    L = lc.footage(f, u0 * F, end)
    lc.transform(L, pos=pos, scale=[100 * sc, 100 * sc])
    mk = mask([[0, h], [w, h], [w, h], [0, h]])
    def top(u):  # ease-out baked per frame (shape keys interpolate linearly)
        e = 1 - (1 - u) ** 3
        return h - e * (h + 5)
    mk['c'][0] = P('Mask Path', 'ADBE Mask Shape', keys=[
        ((u0 + k) * F, {'_shape': 1, 'closed': True, 'vtx': [[-5, top(k / (u1 - u0))], [w + 5, top(k / (u1 - u0))], [w + 5, h + 5], [-5, h + 5]],
                        'in': [[0, 0]] * 4, 'out': [[0, 0]] * 4}) for k in range(u1 - u0 + 1)])
    lc.masks(L, mk)
    lc.effects(L, tint('#000000', acc))
    lc.finalize()

    c = proj.comp(name, dur=end, motion_blur=True)
    h0, h1 = T['hit']
    hit = c.adjustment('rgb hit', h0 * F, h1 * F); c.effects(hit, P('S_TimeWarpRGB', 'S_TimeWarpRGB', children=[]))
    c.footage(proj.still('film_edge_dark.png', 1080, 1920), 0, end, blend=SCREEN)
    art = c.precomp(lc, 0, end)
    p0, p1 = T['push']
    c.transform(art, anchor=[540, 960], pos=Pm['center'], scale=K((p0 * F, [100, 100], 'lin'), (p1 * F, [106, 106])))
    if Pm['bg']:
        c.footage(proj.solid(Pm['bg'], name='logo bg'), 0, end)
    c.finalize()
    return c
