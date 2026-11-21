"""Template 'cine_scene': the generic cinematic shot of the Zeigarnik-style reels (dark rooms with teal/red/purple
light, or a paper desk), driven by data so /rescene can fill it straight from a breakdown:
  world   : bg colour, light shafts (screen), optional anamorphic lens flare, optional window-shadow stripes (paper)
  props   : still images (cut-out PNGs) with placement, tint, glow, blur-in, slow drift/rotation
  shapes  : rings, dots+lines, rectangles (frames, doors) drawn as shape layers
  texts   : lines of text (font, size, position, word/char reveal at measured frames, exit)
  camera  : measured per-frame keys {x, y, zoom, roll} applied to the whole content (precomp), as /rescene reports them
All coordinates are 1080x1920 comp space; frames are local to the shot."""
import math
from ..aeb import K, SCREEN, MULTIPLY, LEFT, CENTER, mask, ellipse_group, rect_group, path_group, drop_shadow, lens_blur, tint
from .. import style as S

F = S.F
JUST = {'left': LEFT, 'center': CENTER}


def ell(cx, cy, rx, ry, n=24):
    return [[cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)] for i in range(n)]


def clip(v):   # mask vertices must stay inside the layer: the engine drops masks that leave it
    return [[min(max(x, 0), 1080), min(max(y, 0), 1920)] for x, y in v]


def _world(proj, c, W, end):
    for i, s in enumerate(W.get('shafts', [])):   # {'quad': [[x,y]x4], 'color', 'op', 'feather'}
        L = c.footage(proj.solid(s['color'], name=f'shaft {i}'), 0, end, blend=SCREEN)
        c.masks(L, mask(clip(s['quad']), feather=s.get('feather', 150))); c.transform(L, op=s.get('op', 60))
    if W.get('flare'):
        fy, col = W['flare'].get('y', 1092), W['flare'].get('color', '#1F7A86')
        for nm, rx, ry, cc, op, fe in (('streak a', 1200, 7, col, 45, 10), ('streak b', 700, 9, col, 60, 12),
                                       ('streak c', 330, 12, W['flare'].get('hot', '#5FC3CE'), 80, 14),
                                       ('core glow', 150, 60, col, 70, 90), ('core', 70, 22, '#F4FFFF', 100, 30)):
            L = c.footage(proj.solid(cc, name=f'flare {nm}'), 0, end, blend=SCREEN)
            c.masks(L, mask(clip(ell(1080, fy, rx, ry)), feather=fe)); c.transform(L, op=op)
    for i, s in enumerate(W.get('stripes', [])):   # window shadow on paper: {'quad', 'op'}
        L = c.footage(proj.solid('#3A3028', name=f'shadow {i}'), 0, end, blend=MULTIPLY)
        c.masks(L, mask(clip(s['quad']), feather=s.get('feather', 40))); c.transform(L, op=s.get('op', 45))


def build(proj, name, dur_f, world, props=(), shapes=(), texts=(), camera=None, out_blur=None, fringe=0.6):
    end = dur_f * F
    inner = proj.comp(f'{name} content', dur=end)
    for i, t in enumerate(texts):
        f0, f1 = t['in']; out = (t.get('out') or dur_f) * F
        rv = (S.char_reveal if t.get('reveal') == 'char' else S.word_reveal)(f0 * F, f1 * F)
        L = inner.text(f'text {i}', t['s'], 0, out, t.get('font', 'HelvReal-Bold'), t['size'], t.get('color', '#ECEAE6'),
                       tracking=t.get('tracking', -30), justify=JUST[t.get('just', 'left')], reveal=rv)
        p = t['pos']; d = t.get('drift', [0, 0])
        inner.transform(L, pos=K((0, p), (end, [p[0] + d[0], p[1] + d[1]])))
        if t.get('glow', True): inner.effects(L, drop_shadow(t.get('glow_color', '#FFFFFF'), t.get('glow_op', 18), 0, 0, 8))
    for i, s in enumerate(shapes):
        k = s['kind']
        if k == 'ring':
            g = [path_group(ell(0, 0, s['d'] / 2, s['d'] / 2, 64), None, s['color'], s.get('w', 4))]
        elif k == 'disc':
            g = [ellipse_group(s['d'], s['d'], s['color'])]
        elif k == 'rect':
            g = [rect_group(s['w'], s['h'], s.get('fill'), s.get('stroke'), s.get('sw', 0))]
        elif k == 'poly':   # open/closed polyline + dots: constellations, door frames
            g = [path_group(s['pts'], s.get('fill'), s.get('stroke'), s.get('sw', 2), closed=s.get('closed', True))]
            g += [ellipse_group(s.get('dot', 0), s.get('dot', 0), s.get('stroke', '#FFFFFF'), pos=tuple(p)) for p in s['pts']] if s.get('dot') else []
        L = inner.shape(f'shape {i}', s.get('t', 0) * F, end, g, **({'blend': SCREEN} if s.get('screen') else {}))
        inner.transform(L, pos=s['pos'], rot=K((0, 0), (end, s.get('spin', 0))) if s.get('spin') else None,
                        op=K((s.get('t', 0) * F, 0), ((s.get('t', 0) + 4) * F, s.get('op', 100))))
        if s.get('glow'): inner.effects(L, drop_shadow(s['glow'], 70, 0, 0, 16))
    for i, p in enumerate(props):
        ft = proj.still(p['file'], p['w'], p['h'])
        L = inner.footage(ft, 0, end, **({'blend': MULTIPLY} if p.get('multiply') else {}))
        sc = 100 * p['width'] / p['w']; t0 = p.get('in', (0, 4))
        g = p.get('grow', 1.0); d = p.get('drift', [0, 0]); r = p.get('rot', 0)
        inner.transform(L, pos=K((0, p['pos']), (end, [p['pos'][0] + d[0], p['pos'][1] + d[1]])),
                        scale=K((0, [sc, sc]), (end, [sc * g, sc * g])), rot=K((0, r), (end, r + p.get('spin', 0))),
                        op=K((t0[0] * F, 0), (t0[1] * F, p.get('op', 100))))
        fx = []
        if p.get('tint'): fx.append(tint(*p['tint']))
        if p.get('glow'): fx.append(drop_shadow(p['glow'], 60, 0, 0, 18))
        fx.append(lens_blur(K((t0[0] * F, p.get('blur_in', 14)), (t0[1] * F, p.get('blur', 0)))))
        inner.effects(L, *fx)
    _world(proj, inner, world, end)
    inner.footage(proj.solid(world['bg'], name='bg'), 0, end)
    inner.finalize()

    c = proj.comp(name, dur=end)
    q = c.adjustment('fringe', 0, end); c.effects(q, S.qca(fringe))
    L = c.precomp(inner, 0, end)
    if camera:   # measured content motion: x/y in px, zoom in %, roll in degrees, keys at local frames
        def keys(k, base, f=lambda v: v):
            ks = camera.get(k) or []
            return K(*[(q[0] * F, f(q[1])) for q in ks]) if len(ks) > 1 else None
        xs, ys = camera.get('x') or [(0, 0)], camera.get('y') or [(0, 0)]
        fr = sorted({q[0] for q in xs} | {q[0] for q in ys})
        def at(ks, f):
            ks = sorted(ks); v = ks[0][1]
            for a, b in zip(ks, ks[1:]):
                if a[0] <= f <= b[0]: return a[1] + (b[1] - a[1]) * (f - a[0]) / max(1, b[0] - a[0])
            return ks[-1][1] if f > ks[-1][0] else v
        pos = K(*[(f * F, [540 + at(xs, f), 960 + at(ys, f)]) for f in fr]) if len(fr) > 1 else None
        zk = keys('zoom', 100, lambda v: [v, v]); rk = keys('roll', 0)
        c.transform(L, anchor=[540, 960], pos=pos or [540, 960], scale=zk, rot=rk)
    if out_blur:
        c.effects(L, lens_blur(K((out_blur[0] * F, 0), (out_blur[1] * F, 30))))
    c.finalize()
    return c
