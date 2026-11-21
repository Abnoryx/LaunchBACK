"""Template 'flare_script' (Zeigarnik reel shot 2a, f99-152, 54 frames): near-black room, a teal anamorphic lens
flare streaks in from the right edge (hot white core at the frame edge), dust specks.
A short sans-italic line blurs in, then a thin monoline script word writes on under it; slow push-in; the text
smears out (lens blur) at the end. Measured on the reel at 1080x1920 (local frame = reel frame - 99)."""
import random
from ..aeb import K, hexc, SCREEN, CENTER, mask, ellipse_group, drop_shadow, lens_blur
from .. import style as S

F = S.F
DUR_F = 54

DEFAULTS = {
    'words': {'line': 'Just good', 'script': 'Storytelling'},
    'layout': {'line': [540, 885], 'script': [540, 985], 'line_size': 92, 'script_size': 140,
               'ink': '#DCDAD6', 'bg': '#010507', 'teal': '#1F7A86', 'flare_y': 1092},
    'timing': {'line': (4, 12), 'script': (8, 22), 'out': (44, 54)},   # local frames
    'push': (100, 106),
    'dust_seed': 3,
}


def merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def build(proj, name='flare_script', **params):
    Pm = merge(DEFAULTS, params)
    W, Lo, T = Pm['words'], Pm['layout'], Pm['timing']
    end = DUR_F * F
    c = proj.comp(name, dur=end)
    q = c.adjustment('fringe', 0, end); c.effects(q, S.qca(0.6))
    o0, o1 = T['out'][0] * F, T['out'][1] * F
    z0, z1 = Pm['push']

    def text_layer(nm, s, font, size, pos, t, tracking=0):
        L = c.text(nm, s, 0, end, font, size, Lo['ink'], tracking=tracking, justify=CENTER,
                   reveal=S.char_reveal(t[0] * F, t[1] * F))
        c.transform(L, pos=K((0, pos), (end, [pos[0], pos[1] - 12])), scale=K((0, [z0, z0]), (end, [z1, z1])),
                    op=K((o0, 100), (o1, 0)))
        c.effects(L, drop_shadow('#FFFFFF', 18, 0, 0, 8), lens_blur(K((0, 0), (o0, 0), (o1, 24))))
        return L

    text_layer('line', W['line'], 'HelvReal-Oblique', Lo['line_size'], Lo['line'], T['line'], tracking=-30)
    text_layer('script', W['script'], 'Sacramento', Lo['script_size'], Lo['script'], T['script'])

    # anamorphic flare: thin teal streak that fades to the left (stacked segments), a soft white-hot core at the edge
    fy = Lo['flare_y']

    def ell(cx, cy, rx, ry, n=24):
        import math
        return [[cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)] for i in range(n)]
    for nm, rx, ry, col, op, fe in (('streak a', 1200, 7, Lo['teal'], 45, 10), ('streak b', 700, 9, Lo['teal'], 60, 12),
                                    ('streak c', 330, 12, '#5FC3CE', 80, 14), ('core glow', 150, 60, Lo['teal'], 70, 90),
                                    ('core', 70, 22, '#F4FFFF', 100, 30)):
        L = c.footage(proj.solid(col, name=f'flare {nm}'), 0, end, blend=SCREEN)
        c.masks(L, mask(ell(1080, fy, rx, ry), feather=fe))
        c.transform(L, op=K((0, op * 0.55), (10 * F, op), (end, op * 0.9)))
    haze = proj.solid('#0B2A30', name='haze')
    L = c.footage(haze, 0, end, blend=SCREEN)
    c.masks(L, mask([[560, fy - 260], [1180, fy - 260], [1180, fy + 260], [560, fy + 260]], feather=260))

    rnd = random.Random(Pm['dust_seed'])
    specks = [ellipse_group(s, s, '#CFE6EA', pos=(rnd.uniform(0, 1080), rnd.uniform(0, 1920)))
              for s in (rnd.uniform(2, 4) for _ in range(22))]
    dust = c.shape('dust', 0, end, specks, blend=SCREEN)
    c.transform(dust, pos=K((0, [0, 0]), (end, [-10, 25])), anchor=[0, 0], op=60)
    c.footage(proj.solid(Lo['bg'], name='bg'), 0, end)
    c.finalize()
    return c
