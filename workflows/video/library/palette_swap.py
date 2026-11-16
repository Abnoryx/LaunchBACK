"""Re-hue a built project for another accent: every saturated green colour value in the dumped scene JSON (text
fills/strokes, shape fills/strokes, solids, Fill/Tint/Light Sweep colours) is rotated to the target hue, keeping its
lightness and saturation. Templates keep their proven original colours; a video swaps them in one pass."""
import colorsys

COLOR_KEYS = ('fill_color', 'stroke_color', 'fill', 'color')


def _is_rgb(v):
    return isinstance(v, list) and len(v) in (3, 4) and all(isinstance(x, (int, float)) for x in v) and all(-0.01 <= x <= 1.01 for x in v[:3])


def swap(rgb, hue_from=(70, 175), hue_to=1.0, sat_min=0.18, sat_boost=1.08):
    r, g, b = rgb[:3]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if not (hue_from[0] <= h * 360 <= hue_from[1]) or s < sat_min or max(r, g, b) - min(r, g, b) < 0.06:
        return rgb
    r2, g2, b2 = colorsys.hls_to_rgb(hue_to / 360, l, min(1.0, s * sat_boost))
    return [r2, g2, b2] + list(rgb[3:])


def apply(node, **kw):
    """Walk the project JSON in place."""
    n = 0
    if isinstance(node, dict):
        m = str(node.get('m', ''))
        colorish = 'Color' in m or m.startswith(('ADBE Fill-', 'ADBE Tint-', 'CC Light Sweep-0008'))
        if colorish:
            if _is_rgb(node.get('v')):
                new = swap(node['v'], **kw); n += new != node['v']; node['v'] = new
            for k in node.get('k') or []:
                if _is_rgb(k.get('v')):
                    new = swap(k['v'], **kw); n += new != k['v']; k['v'] = new
        for key in COLOR_KEYS:
            if _is_rgb(node.get(key)):
                new = swap(node[key], **kw); n += new != node[key]; node[key] = new
        for v in node.values():
            n += apply(v, **kw)
    elif isinstance(node, list):
        for v in node:
            n += apply(v, **kw)
    return n
