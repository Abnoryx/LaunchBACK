"""Template 'brain_words' (Zeigarnik reel shot 2b, f153-195, 43 frames): dark room, a broad teal light shaft from the
top left and the lens-flare streak; a prop (brain) blurs in centre with a bold italic line above it, then the camera
pushes in and pans so the prop slides right while a small italic line and a big serif-italic word reveal on the left.
Measured at 1080x1920 (local frame = reel frame - 153)."""
import math
from ..aeb import K, SCREEN, CENTER, LEFT, mask, drop_shadow, lens_blur, tint
from .. import style as S

F = S.F
DUR_F = 43
CX, CY = 540, 960

DEFAULTS = {
    'words': {'top': 'Its how', 'small': 'your brain', 'big': 'Works'},
    'prop': {'file': 'z_brain.png', 'w': 1024, 'h': 1024, 'width': 500, 'pos': [540, 1000], 'tint': ('#0A0203', '#D2604E', 90)},
    'layout': {'top': [540, 735], 'top_size': 130, 'small': [26, 786], 'small_size': 46, 'big': [-77, 877], 'big_size': 100,
               'ink': '#ECEAE6', 'bg': '#010507', 'teal': '#1F7A86', 'flare_y': 1092},
    'timing': {'prop': (0, 5), 'top': (0, 6), 'small': (9, 15), 'big': (14, 21), 'move': (8, 34)},
    'camera': {'zoom': 1.32, 'pan': [426, 30]},
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='brain_words', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T, Pr, Cm = Pm['words'], Pm['layout'], Pm['timing'], Pm['prop'], Pm['camera']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    q = c.adjustment('fringe', 0, end); c.effects(q, S.qca(0.6))
    m0, m1 = T['move'][0] * F, T['move'][1] * F
    ease = S.QUAD_OUT

    def cam(p, z):   # where a point lands after the camera move (zoom about the frame centre, then pan)
        z = z if z else 1.0
        return [CX + (p[0] - CX) * z + (Cm['pan'][0] if z != 1.0 else 0), CY + (p[1] - CY) * z + (Cm['pan'][1] if z != 1.0 else 0)]

    def place(L, p, s=100):
        z = Cm['zoom']
        c.transform(L, pos=K((m0, p), (m1, cam(p, z), ease)), scale=K((m0, [s, s]), (m1, [s * z, s * z], ease)))

    for nm, key, font, just in (('top', 'top', 'HelvReal-BoldOblique', CENTER), ('small', 'small', 'HelvReal-Oblique', LEFT),
                                ('big', 'big', 'DidotLTPro-BoldItalic', LEFT)):
        L = c.text(nm, W[key], 0, end, font, Lo[f'{key}_size'], Lo['ink'], tracking=-40, justify=just,
                   reveal=S.word_reveal(T[key][0] * F, T[key][1] * F))
        place(L, Lo[key]); c.effects(L, drop_shadow('#FFFFFF', 18, 0, 0, 8))

    ft = proj.still(Pr['file'], Pr['w'], Pr['h'])
    P = c.footage(ft, 0, end)
    s = 100 * Pr['width'] / Pr['w']
    place(P, Pr['pos'], s)
    c.effects(P, tint(*Pr['tint']), drop_shadow('#2FB6C4', 60, 0, 0, 18),
              lens_blur(K((T['prop'][0] * F, 18), (T['prop'][1] * F, 0))))
    c.transform(P, op=K((T['prop'][0] * F, 0), (T['prop'][1] * F, 100)))

    fy = Lo['flare_y']

    def ell(cx, cy, rx, ry, n=24):
        return [[cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)] for i in range(n)]
    for nm, rx, ry, col, op, fe in (('streak a', 1200, 7, Lo['teal'], 45, 10), ('streak b', 700, 9, Lo['teal'], 60, 12),
                                    ('streak c', 330, 12, '#5FC3CE', 80, 14), ('core glow', 150, 60, Lo['teal'], 70, 90),
                                    ('core', 70, 22, '#F4FFFF', 100, 30)):
        L = c.footage(proj.solid(col, name=f'flare {nm}'), 0, end, blend=SCREEN)
        c.masks(L, mask(ell(1080, fy, rx, ry), feather=fe)); c.transform(L, op=op)
    # broad teal shaft from the top left, falling to the right
    sh = c.footage(proj.solid('#2A8C98', name='shaft'), 0, end, blend=SCREEN)
    c.masks(sh, mask([[0, 300], [900, 900], [900, 1300], [0, 880]], feather=140))
    c.transform(sh, op=K((0, 45), (end, 55)))   # mask vertices must stay inside the layer: the engine drops masks that leave it
    c.footage(proj.solid(Lo['bg'], name='bg'), 0, end)
    c.finalize()
    return c
