"""aeb: author our own scenes, from scratch, in the scene format our engine renders.

Nothing here reads the reference project: values are typed in by hand from measurements of the posted reel.
Eases are written as cubic-beziers cb(x1, y1, x2, y2) and converted to AE speed/influence keys.
"""
import json

LIN, BEZ, HOLD = 6612, 6613, 6614
NORMAL, MULTIPLY, SCREEN, OVERLAY, ADD, DIFFERENCE, EXCLUSION, STENCIL_ALPHA = 5212, 5216, 5222, 5226, 5220, 5233, 5235, 5240
MATTE_ALPHA, MATTE_ALPHA_INV, MATTE_LUMA, MATTE_LUMA_INV = 5013, 5014, 5015, 5016
LEFT, RIGHT, CENTER = 7413, 7414, 7415


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


# ---------------------------------------------------------------- keyframes
def K(*keys):
    """K((t, v), (t, v, ease), ...): ease of a key applies to the segment that STARTS at it:
    'lin', 'hold', or a cubic-bezier tuple (x1, y1, x2, y2). Default 'lin'."""
    return list(keys)


def _speed(dv, dt, slope):
    return slope * dv / dt if dt > 0 else 0.0


EASE_OVERRIDE = None   # e.g. QUAD_OUT: every bezier ease in the comps built while set becomes this curve


def keep(e):
    """Mark an ease so EASE_OVERRIDE leaves it alone (deliberate ease-ins on handoffs)."""
    return ('keep',) + tuple(e)


def build_keys(keys):
    keys = [k if len(k) == 3 else (k[0], k[1], 'lin') for k in keys]
    keys = [(t, v, e[1:] if isinstance(e, tuple) and e and e[0] == 'keep' else (EASE_OVERRIDE if EASE_OVERRIDE and isinstance(e, tuple) else e))
            for t, v, e in keys]
    out = []
    for i, (t, v, e) in enumerate(keys):
        dims = len(v) if isinstance(v, (list, tuple)) else 1
        k = {'t': round(t, 5), 'v': list(v) if isinstance(v, (list, tuple)) else v,
             'in': LIN, 'out': LIN, 'ie': [[0.0, 16.667]] * dims, 'oe': [[0.0, 16.667]] * dims}
        out.append(k)
    for i in range(len(keys) - 1):
        (t0, v0, e), (t1, v1, _) = keys[i], keys[i + 1]
        a, b = out[i], out[i + 1]
        if e == 'hold':
            a['out'] = HOLD; b['in'] = HOLD; continue
        if e == 'lin':
            continue
        x1, y1, x2, y2 = e
        a['out'] = BEZ; b['in'] = BEZ
        vs0 = v0 if isinstance(v0, (list, tuple)) else [v0]
        vs1 = v1 if isinstance(v1, (list, tuple)) else [v1]
        dt = t1 - t0
        a['oe'] = [[_speed(q - p, dt, y1 / x1 if x1 > 0 else 0), max(0.1, x1 * 100)] for p, q in zip(vs0, vs1)]
        b['ie'] = [[_speed(q - p, dt, (1 - y2) / (1 - x2) if x2 < 1 else 0), max(0.1, (1 - x2) * 100)] for p, q in zip(vs0, vs1)]
    return out


def P(n, m, v=None, keys=None, expr=None, children=None):
    p = {'n': n, 'm': m}
    if keys is not None:
        p['k'] = build_keys(keys)
        p['v'] = p['k'][0]['v']
    elif v is not None:
        p['v'] = v
    if expr:
        p['x'] = expr
    if children is not None:
        p['c'] = children
    return p


def val(n, m, x):
    """x is a plain value or a K(...) list."""
    if isinstance(x, list) and x and isinstance(x[0], tuple):
        return P(n, m, keys=x)
    return P(n, m, v=x)


# ---------------------------------------------------------------- project
class Project:
    def __init__(self):
        self.comps, self.footage, self._id = [], [], 100

    def nid(self):
        self._id += 1
        return self._id

    def comp(self, name, w=1080, h=1920, dur=10.0, fps=30.0, motion_blur=False):
        c = Comp(self, name, w, h, dur, fps, motion_blur)
        self.comps.append(c)
        return c

    def still(self, file, w, h):
        f = {'id': self.nid(), 'name': file, 'width': w, 'height': h, 'duration': 0.0, 'has_video': True,
             'source_type': 'FileSource', 'is_still': True, 'file': file}
        self.footage.append(f)
        return f

    def video(self, file, w, h, duration, loop=1, fps=30.0):
        f = {'id': self.nid(), 'name': file, 'width': w, 'height': h, 'duration': duration, 'frame_rate': fps,
             'has_video': True, 'source_type': 'FileSource', 'is_still': False, 'loop': loop, 'file': file}
        self.footage.append(f)
        return f

    def model(self, file):
        """A glTF/GLB model source (rendered by the engine with three.js; 1 glTF unit = 508 px at 100 %)."""
        f = {'id': self.nid(), 'name': file, 'width': 1080, 'height': 1920, 'has_video': True,
             'source_type': 'FileSource', 'is_still': True, 'file': file}
        self.footage.append(f)
        return f

    def solid(self, color, w=1080, h=1920, name='solid'):
        f = {'id': self.nid(), 'name': name, 'width': w, 'height': h, 'has_video': True,
             'source_type': 'SolidSource', 'is_still': True, 'color': hexc(color)[:3] if isinstance(color, str) else color}
        self.footage.append(f)
        return f

    def dump(self, path):
        d = {'file': 'scratch', 'comps': [c.json() for c in self.comps], 'footage': self.footage}
        json.dump(d, open(path, 'w'))
        return path


class Comp:
    def __init__(self, proj, name, w, h, dur, fps, mb):
        self.proj, self.name, self.w, self.h, self.dur, self.fps, self.mb = proj, name, w, h, dur, fps, mb
        self.id = proj.nid()
        self.layers = []  # top first

    def json(self):
        return {'id': self.id, 'name': self.name, 'w': self.w, 'h': self.h, 'fps': self.fps, 'dur': self.dur,
                'bg_color': [0, 0, 0], 'motion_blur': self.mb, 'shutter_angle': 180, 'shutter_phase': -90,
                'layers': [dict(L, i=i) for i, L in enumerate(self.layers)]}

    # all add_* append BELOW existing layers (call in top-to-bottom order); returns the layer dict
    def _layer(self, typ, name, inp, out, start=0.0, **kw):
        L = {'name': name, 'type': typ, 'in_point': inp, 'out_point': min(out, self.dur), 'start_time': start,
             'stretch': 100.0, 'blending_mode': kw.pop('blend', NORMAL), 'track_matte_type': 5012, 'enabled': True,
             'props': []}
        for k in ('three_d_layer', 'adjustment_layer', 'motion_blur', 'collapse_transformation', 'null_layer'):
            if kw.pop(k[:4] if False else k, False):
                L[k] = True
        if kw.pop('d3', False):
            L['three_d_layer'] = True
        matte = kw.pop('matte', None)
        if matte is not None:
            L['has_track_matte'] = True; L['track_matte_type'] = matte[1]; L['_matte_ref'] = matte[0]
        parent = kw.pop('parent', None)
        if parent is not None:
            L['_parent_ref'] = parent
        L.update(kw)
        self.layers.append(L)
        return L

    def finalize(self):
        """Resolve parent / matte references (layer dicts) to indices."""
        for L in self.layers:
            if '_parent_ref' in L:
                L['parent'] = self.layers.index(L.pop('_parent_ref'))
            if '_matte_ref' in L:
                M = L.pop('_matte_ref')
                L['matte_layer'] = self.layers.index(M); M['is_track_matte'] = True
        return self

    def transform(self, L, pos=None, anchor=None, scale=None, rot=None, rx=None, ry=None, ori=None, op=None,
                  px=None, py=None, pz=None):
        c = []
        if anchor is not None: c.append(val('Anchor Point', 'ADBE Anchor Point', anchor))
        if pos is not None: c.append(val('Position', 'ADBE Position', pos))
        for n, m, x in (('X Position', 'ADBE Position_0', px), ('Y Position', 'ADBE Position_1', py), ('Z Position', 'ADBE Position_2', pz)):
            if x is not None: c.append(val(n, m, x))
        if scale is not None: c.append(val('Scale', 'ADBE Scale', scale))
        if ori is not None: c.append(val('Orientation', 'ADBE Orientation', ori))
        if rx is not None: c.append(val('X Rotation', 'ADBE Rotate X', rx))
        if ry is not None: c.append(val('Y Rotation', 'ADBE Rotate Y', ry))
        if rot is not None: c.append(val('Rotation', 'ADBE Rotate Z', rot))
        if op is not None: c.append(val('Opacity', 'ADBE Opacity', op))
        L['props'].append(P('Transform', 'ADBE Transform Group', children=c))
        return L

    def effects(self, L, *fx):
        L['props'].append(P('Effects', 'ADBE Effect Parade', children=list(fx)))
        return L

    def masks(self, L, *ms):
        L['props'].append(P('Masks', 'ADBE Mask Parade', children=list(ms)))
        return L

    # ---- layer kinds
    def footage(self, f, inp, out, start=0.0, **kw):
        return self._layer('AVLayer', f['name'], inp, out, start, src_id=f['id'], **kw)

    def model(self, f, inp, out, **kw):
        """3D model layer (AE ThreeDModelLayer); always 3D. Scale % maps 1 glTF unit -> 5.08 px per %."""
        return self._layer('ThreeDModelLayer', f['name'], inp, out, src_id=f['id'], three_d_layer=True, **kw)

    def precomp(self, c, inp, out, start=0.0, **kw):
        return self._layer('AVLayer', c.name, inp, out, start, src_id=c.id, **kw)

    def null(self, name, inp, out, **kw):
        return self._layer('AVLayer', name, inp, out, null_layer=True, **kw)

    def adjustment(self, name, inp, out, **kw):
        f = self.proj.solid([1, 1, 1], self.w, self.h, 'adj')
        return self._layer('AVLayer', name, inp, out, src_id=f['id'], adjustment_layer=True, **kw)

    def camera(self, name, inp, out, frames, zoom=None):
        """frames: list of (t, x, y, z[, zoom]) sampled every frame -> linear keys."""
        L = self._layer('CameraLayer', name, inp, out)
        L['three_d_layer'] = True
        pos = [(t, [x, y, z]) for t, x, y, z, *_ in frames]
        L['props'].append(P('Transform', 'ADBE Transform Group', children=[P('Position', 'ADBE Position', keys=pos)]))
        zk = [(f[0], f[4]) for f in frames if len(f) > 4]
        zp = P('Zoom', 'ADBE Camera Zoom', keys=zk) if zk else P('Zoom', 'ADBE Camera Zoom', v=zoom or self.w * 1.38889)
        L['props'].append(P('Camera Options', 'ADBE Camera Options Group', children=[zp]))
        return L

    def text(self, name, s, inp, out, font, size, color, tracking=0, justify=LEFT, leading=None, hscale=1.0, vscale=1.0,
             stroke=None, stroke_w=0, reveal=None, box=None, **kw):
        doc = {'text': s, 'font': font, 'font_size': size, 'fill_color': hexc(color)[:3], 'tracking': tracking,
               'justification': justify, 'apply_fill': True, 'horizontal_scale': hscale, 'vertical_scale': vscale}
        if box: doc.update(box_text=True, box_text_size=list(box))
        if leading: doc['leading'] = leading
        if stroke: doc.update(apply_stroke=True, stroke_color=hexc(stroke)[:3], stroke_width=stroke_w)
        L = self._layer('TextLayer', name, inp, out, text=doc, **kw)
        tp = [P('Source Text', 'ADBE Text Document', v=dict(doc, _text=1, size=size, fill=doc['fill_color']))]
        if reveal:
            tp.append(P('Animators', 'ADBE Text Animators', children=[reveal]))
        L['props'].append(P('Text', 'ADBE Text Properties', children=tp))
        return L

    def shape(self, name, inp, out, groups, **kw):
        L = self._layer('ShapeLayer', name, inp, out, **kw)
        L['props'].append(P('Contents', 'ADBE Root Vectors Group', children=groups))
        return L


# ---------------------------------------------------------------- text animators
def reveal(t0, t1, based_on=3, ease=(0.8, 0, 0.2, 1), opacity=0, blur=10, dy=0, ease_high=47, ease_low=100, shape=2, scale=None, random_seed=None):
    """AE-style range-selector reveal: offset -100 -> 100 between t0 and t1 (comp time).
    based_on: 1 characters, 2 characters excl. spaces, 3 words, 4 lines. shape 2 = ramp up."""
    props = [P('Opacity', 'ADBE Text Opacity', v=opacity)]
    if blur: props.append(P('Blur', 'ADBE Text Blur', v=[blur, blur]))
    if dy: props.append(P('Position', 'ADBE Text Position 3D', v=[0, dy, 0]))
    if scale is not None: props.append(P('Scale', 'ADBE Text Scale 3D', v=[scale, scale, 100]))
    sel = P('Range Selector 1', 'ADBE Text Selector', children=[
        P('Offset', 'ADBE Text Percent Offset', keys=[(t0, -100.0, ease), (t1, 100.0)]),
        P('Advanced', 'ADBE Text Range Advanced', children=[
            P('Based On', 'ADBE Text Range Type2', v=based_on), P('Shape', 'ADBE Text Range Shape', v=shape),
            P('Ease High', 'ADBE Text Levels Max Ease', v=ease_high), P('Ease Low', 'ADBE Text Levels Min Ease', v=ease_low)]
            + ([P('Randomize Order', 'ADBE Text Randomize Order', v=1), P('Random Seed', 'ADBE Text Random Seed', v=random_seed)] if random_seed is not None else []))])
    return P('Animator 1', 'ADBE Text Animator', children=[
        P('Selectors', 'ADBE Text Selectors', children=[sel]), P('Properties', 'ADBE Text Animator Properties', children=props)])


# ---------------------------------------------------------------- effects (match names as the engine reads them)
def fx(match, name, **params):
    """params: suffix -> value or K(...) list, e.g. fx('ADBE Fill', 'Fill', **{'0002': hexc('#fff')})."""
    ch = [val(k, f'{match}-{k}', v) for k, v in params.items()]
    return P(name, match, children=ch)


def gaussian(b):
    return P('Gaussian Blur', 'ADBE Gaussian Blur 2', children=[val('Blurriness', 'ADBE Gaussian Blur 2-0001', b)])


def drop_shadow(color='#000000', opacity=50, direction=135, distance=5, softness=0):
    return fx('ADBE Drop Shadow', 'Drop Shadow', **{'0001': hexc(color), '0002': opacity * 2.55, '0003': direction, '0004': distance, '0005': softness})


def fill(color):
    return P('Fill', 'ADBE Fill', children=[P('Color', 'ADBE Fill-0002', v=hexc(color)), P('Opacity', 'ADBE Fill-0007', v=1.0)])


def tint(black='#000000', white='#ffffff', amount=100):
    return fx('ADBE Tint', 'Tint', **{'0001': hexc(black), '0002': hexc(white), '0003': amount})


def lens_blur(radius):
    return fx('ADBE Camera Lens Blur', 'Camera Lens Blur', **{'0001': radius})


def minimax(radius, op=3, direction=2):
    return fx('ADBE Minimax', 'Minimax', **{'0001': op, '0002': radius, '0004': direction})


def qca(amount):
    return fx('PEQCAGL', 'Quick Chromatic Aberration', **{'0002': amount})


def mask(vtx, inv=False, feather=0, mode=6813, inn=None, outt=None):
    sh = {'_shape': 1, 'closed': True, 'vtx': vtx, 'in': inn or [[0, 0]] * len(vtx), 'out': outt or [[0, 0]] * len(vtx)}
    m = P('Mask 1', 'ADBE Mask Atom', children=[P('Mask Path', 'ADBE Mask Shape', v=sh),
                                              P('Mask Feather', 'ADBE Mask Feather', v=[feather, feather])])
    m['mode'], m['inv'] = mode, inv
    return m


# ---------------------------------------------------------------- shapes
def rect_group(w, h, color=None, stroke=None, stroke_w=0, round_=0, pos=(0, 0)):
    items = [P('Rectangle Path 1', 'ADBE Vector Shape - Rect', children=[
        P('Size', 'ADBE Vector Rect Size', v=[w, h]), P('Position', 'ADBE Vector Rect Position', v=list(pos)),
        P('Roundness', 'ADBE Vector Rect Roundness', v=round_)])]
    if stroke: items.append(P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc(stroke)), P('Stroke Width', 'ADBE Vector Stroke Width', v=stroke_w)]))
    if color: items.append(P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(color))]))
    return P('Rectangle 1', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=items)])


def ellipse_group(w, h, color, pos=(0, 0)):
    return P('Ellipse 1', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=[
        P('Ellipse Path 1', 'ADBE Vector Shape - Ellipse', children=[P('Size', 'ADBE Vector Ellipse Size', v=[w, h]),
                                                                     P('Position', 'ADBE Vector Ellipse Position', v=list(pos))]),
        P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(color))])])])


def path_group(vtx, color=None, stroke=None, stroke_w=0, closed=True, inn=None, outt=None):
    sh = {'_shape': 1, 'closed': closed, 'vtx': vtx, 'in': inn or [[0, 0]] * len(vtx), 'out': outt or [[0, 0]] * len(vtx)}
    items = [P('Path 1', 'ADBE Vector Shape - Group', children=[P('Path', 'ADBE Vector Shape', v=sh)])]
    if stroke: items.append(P('Stroke 1', 'ADBE Vector Graphic - Stroke', children=[P('Color', 'ADBE Vector Stroke Color', v=hexc(stroke)), P('Stroke Width', 'ADBE Vector Stroke Width', v=stroke_w)]))
    if color: items.append(P('Fill 1', 'ADBE Vector Graphic - Fill', children=[P('Color', 'ADBE Vector Fill Color', v=hexc(color))]))
    return P('Shape 1', 'ADBE Vector Group', children=[P('Contents', 'ADBE Vectors Group', children=items)])
