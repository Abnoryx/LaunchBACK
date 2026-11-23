"""Dump an After Effects .aep to the JSON the WebGL engine reads (Route A step 1).
usage: python3 -m extract.aep_dump <project.aep> <out.json>
Format = the one the engine already plays (tpl/an/json/psych.json): comps -> layers -> props tree of
{n: name, m: match name, v: value, k: keyframes, x: expression, c: children, syn/off/mode/inv flags}."""
import sys, json, enum
import py_aep
from py_aep.models.text import ranges as _tr

R = lambda v: round(v, 5) if isinstance(v, float) else v
errors = {'n': 0, 'kinds': {}}


def get(o, a, default=None):
    try:
        return getattr(o, a)
    except Exception as e:  # undecodable field: record, keep going
        k = f'{a}:{type(e).__name__}'; errors['n'] += 1; errors['kinds'][k] = errors['kinds'].get(k, 0) + 1
        return default


def val(v):
    if isinstance(v, enum.Enum): return v.value
    if isinstance(v, (bool, int, str)) or v is None: return v
    if isinstance(v, float): return R(v)
    if isinstance(v, (list, tuple)): return [val(x) for x in v]
    if isinstance(v, py_aep.Shape):
        return {'_shape': 1, 'closed': bool(v.closed), 'vtx': val(v.vertices), 'in': val(v.in_tangents), 'out': val(v.out_tangents)}
    if isinstance(v, py_aep.TextDocument):
        return {'_text': 1, 'text': v.text, 'font': v.font, 'size': R(v.font_size), 'fill': val(get(v, 'fill_color')), 'tracking': val(get(v, 'tracking'))}
    if isinstance(v, py_aep.MarkerValue): return {'_marker': 1, 'comment': v.comment, 'duration': R(v.duration)}
    if type(v).__name__ == 'Gradient':
        return {'_gradient': 1, 'colors': [[R(c._offset), R(c._midpoint), *val(list(c._color))] for c in v.color_stops],
                'alphas': [[R(a._offset), R(a._midpoint), R(a._alpha)] for a in v.alpha_stops]}
    if type(v).__name__ == 'Curves':
        return {'_curves': 1, 'channels': {k: [list(p) for p in c.points] for k, c in v.channels.items() if not c.is_identity}}
    if hasattr(v, 'tolist'): return val(v.tolist())
    return str(v)


def ease(e):
    return [[R(x.speed), R(x.influence)] for x in (e or [])]


def prop(p):
    d = {'n': get(p, 'name'), 'm': p.match_name}
    if isinstance(p, py_aep.PropertyGroup):
        kids = [k for k in (prop(c) for c in (get(p, 'properties') or [])) if k]
        if not kids and not get(p, 'is_mask'): return None   # empty groups were never in the format
        d['c'] = kids
        if get(p, 'is_mask'):
            mm = get(p, 'mask_mode'); d['mode'] = val(mm) if mm is not None else None
            if get(p, 'inverted'): d['inv'] = True
    else:
        if not get(p, 'is_modified', True): d['syn'] = True
        keys = get(p, 'keyframes') or []
        if not keys: d['v'] = val(get(p, 'value'))   # keyed props carry their values in k
        if keys:
            d['k'] = [{'t': R(k.time), 'v': val(k.value), 'in': val(k.in_interpolation_type), 'out': val(k.out_interpolation_type),
                       'ie': ease(k.in_temporal_ease), 'oe': ease(k.out_temporal_ease),
                       **({'in_st': val(k.in_spatial_tangent), 'out_st': val(k.out_spatial_tangent)} if get(p, 'is_spatial') and k.in_spatial_tangent is not None else {})}
                      for k in keys]
        x = get(p, 'expression')
        if x and get(p, 'expression_enabled', True): d['x'] = x
    if get(p, 'enabled', True) is False: d['off'] = True
    return {k: v for k, v in d.items() if v is not None or k == 'v'}


def text(l):
    td = get(get(l, 'text'), 'source_text'); td = get(td, 'value') if td is not None else None
    if td is None: return None
    t = {a: val(get(td, b)) for a, b in [('text', 'text'), ('font', 'font'), ('font_size', 'font_size'), ('fill_color', 'fill_color'),
         ('stroke_color', 'stroke_color'), ('stroke_width', 'stroke_width'), ('tracking', 'tracking'), ('leading', 'leading'),
         ('justification', 'justification'), ('all_caps', 'all_caps'), ('apply_fill', 'apply_fill'), ('apply_stroke', 'apply_stroke'),
         ('horizontal_scale', 'horizontal_scale'), ('vertical_scale', 'vertical_scale'), ('baseline_shift', 'baseline_shift'), ('box_text', 'box_text')]}
    if t['box_text']: t['box_text_size'] = val(get(td, 'box_text_size')); t['box_text_pos'] = val(get(td, 'box_text_pos'))
    nodes = _tr._cached_line_nodes(td); data = _tr._line_data_from_nodes(nodes) if nodes else None
    locs = val(get(td, 'baseline_locs')) or []; n = len(td.text)
    t['lines'] = []
    if data:   # AE's persisted layout: pen origin + cumulative per-glyph advances (engine uses them for exact spacing)
        for i, ((s, e), nd) in enumerate(zip(data[0], nodes)):
            x, y = (locs[4 * i], locs[4 * i + 1]) if len(locs) > 4 * i + 1 else (0.0, 0.0)   # layer-space baseline start
            t['lines'].append({'s': s, 'e': min(e, n), 'x': R(x), 'y': R(y), 'adv': [round(a, 3) for a in _tr._line_advances(nd)]})
    spans = _tr._char_run_spans(td)
    if len(spans) > 1:   # mixed-style text: one entry per character style run
        t['runs'] = []
        for s, e, _ in spans:
            e = min(e, n)
            if s >= e: continue
            cr = td.character_range(s, e)
            t['runs'].append({'s': s, 'e': e, 'font': get(cr, 'font'), 'size': R(get(cr, 'font_size')), 'fill': val(get(cr, 'fill_color')),
                              'tracking': val(get(cr, 'tracking')), 'hs': R(get(cr, 'horizontal_scale')), 'vs': R(get(cr, 'vertical_scale')),
                              'bshift': R(get(cr, 'baseline_shift')), 'caps': val(get(cr, 'all_caps'))})
    return t


def layer(i, l, layers):
    d = {'i': i, 'name': get(l, 'name'), 'type': type(l).__name__}
    src = get(l, 'source')
    if src is not None: d.update(src=get(src, 'name'), src_id=get(src, 'id'), src_type=type(src).__name__)
    for a in ['in_point', 'out_point', 'start_time', 'stretch', 'blending_mode', 'track_matte_type', 'quality', 'frame_blending_type',
              'label', 'enabled', 'three_d_layer', 'collapse_transformation', 'audio_enabled', 'adjustment_layer', 'null_layer',
              'motion_blur', 'time_remap_enabled', 'has_track_matte', 'is_track_matte']:
        v = val(get(l, a))
        if v is not None and not (v is False and a in ('adjustment_layer', 'null_layer', 'motion_blur', 'time_remap_enabled', 'has_track_matte', 'is_track_matte', 'three_d_layer')):
            d[a] = v
    par = get(l, 'parent')
    if par is not None: d['parent'] = next(j for j, x in enumerate(layers) if x is par)
    tm = get(l, 'track_matte_layer')
    if tm is not None: d['matte_layer'] = next(j for j, x in enumerate(layers) if x is tm)
    if type(l).__name__ == 'TextLayer':
        t = text(l)
        if t: d['text'] = t
    d['props'] = [x for x in (prop(p) for p in (get(l, 'properties') or [])) if x]
    return d


def footage(f):
    s = get(f, 'main_source')
    d = {'id': f.id, 'name': get(f, 'name'), 'width': get(f, 'width'), 'height': get(f, 'height'), 'duration': R(get(f, 'duration')),
         'frame_rate': R(get(f, 'frame_rate')), 'has_audio': get(f, 'has_audio'), 'has_video': get(f, 'has_video'),
         'pixel_aspect': R(get(f, 'pixel_aspect')), 'source_type': type(s).__name__, 'is_still': get(s, 'is_still'), 'loop': get(s, 'loop')}
    fl = get(s, 'file')
    if fl: d['file'] = str(fl)
    col = get(s, 'color')
    if col is not None: d['color'] = val(col)
    return d


def dump(path):
    pr = py_aep.parse(path).project
    comps = [{'id': c.id, 'name': c.name, 'w': c.width, 'h': c.height, 'fps': R(c.frame_rate), 'dur': R(c.duration),
              'bg_color': val(c.bg_color), 'motion_blur': c.motion_blur, 'shutter_angle': get(c, 'shutter_angle'),
              'shutter_phase': get(c, 'shutter_phase'), 'motion_blur_samples_per_frame': get(c, 'motion_blur_samples_per_frame'),
              'frame_blending': c.frame_blending, 'display_start_time': R(c.display_start_time),
              'layers': [layer(i, l, c.layers) for i, l in enumerate(c.layers)]} for c in pr.compositions]
    return {'file': path, 'ae_version': str(get(pr, 'revision', '')), 'comps': comps, 'footage': [footage(f) for f in pr.footages],
            'decode_errors': errors}


if __name__ == '__main__':
    json.dump(dump(sys.argv[1]), open(sys.argv[2], 'w'))
    print('errors', errors['n'], errors['kinds'])
