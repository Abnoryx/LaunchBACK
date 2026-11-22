"""Route A step 5: one self-contained template per shot, with the scene kept exactly and the content exposed as params.
usage: python3 -m extract.aep_template make  <dump.json> <shots.json> <out_dir>     -> <out_dir>/shot_NN.json
       python3 -m extract.aep_template apply <shot_NN.json> <params.json> <out.json>  -> project JSON for render.mjs
A template is a project JSON holding only the comps and footage that shot needs, plus `template`:
  window [from, to] in seconds (render with --from/--to; times are kept as in the project, so nothing is re-timed),
  params: texts (comp/layer -> string, font, size, fill), accent (hue band + default colour), footage (id -> file).
Params are applied by `apply`; everything not exposed stays locked. Templates hold their files' data: they live in
the private template folder, never in git."""
import sys, os, re, json, copy, colorsys

ACCENT_BAND = (100, 170)   # hue degrees treated as the project's accent (green family); measured per project


def is_col(v):
    return isinstance(v, list) and len(v) in (3, 4) and all(isinstance(x, (int, float)) for x in v) and all(0 <= x <= 1 for x in v[:3])


def in_band(v, band):
    h, l, s = colorsys.rgb_to_hls(*v[:3])
    return s > 0.45 and 0.08 < l < 0.92 and band[0] <= h * 360 <= band[1]


def comp_refs(c, by_id, by_name):
    out = set()
    for l in c['layers']:
        if l.get('src_type') == 'CompItem' and l.get('src_id') in by_id: out.add(l['src_id'])
    for name in re.findall(r'comp\("([^"]+)"\)', json.dumps(c)):
        if name in by_name: out.add(by_name[name]['id'])
    return out


def make(dump, shots_path, out_dir):
    d = json.load(open(dump)); sh = json.load(open(shots_path))
    by_id = {c['id']: c for c in d['comps']}; by_name = {c['name']: c for c in d['comps']}
    root = by_name[sh['root']]; fps = sh['fps']
    os.makedirs(out_dir, exist_ok=True)
    for s in sh['shots']:
        t0, t1 = s['start'] / fps, s['end'] / fps
        keep = [l for l in root['layers'] if l['in_point'] < t1 and l['out_point'] > t0]
        idx = {l['i'] for l in keep}
        changed = True
        while changed:   # parents and track mattes of kept layers come along
            changed = False
            for l in list(keep):
                for j in (l.get('parent'), l.get('matte_layer')):
                    if j is not None and j not in idx:
                        keep.append(next(x for x in root['layers'] if x['i'] == j)); idx.add(j); changed = True
        r2 = {**root, 'layers': sorted(keep, key=lambda l: l['i'])}
        need, stack = {root['id']}, list(comp_refs(r2, by_id, by_name))
        while stack:
            cid = stack.pop()
            if cid in need: continue
            need.add(cid); stack += list(comp_refs(by_id[cid], by_id, by_name))
        comps = [r2 if c['id'] == root['id'] else c for c in d['comps'] if c['id'] in need]
        used_f = {l.get('src_id') for c in comps for l in c['layers'] if l.get('src_type') == 'FootageItem'}
        footage = [f for f in d['footage'] if f['id'] in used_f]
        texts = []
        for c in comps:
            for l in c['layers']:
                t = l.get('text')
                if t and l.get('enabled') is True and (c is not r2 or l['in_point'] < t1 and l['out_point'] > t0):
                    texts.append({'id': f"{c['name']}/{l['i']}", 'layer': l['name'], 'text': t['text'], 'font': t['font'],
                                  'size': t['font_size'], 'fill': t['fill_color']})
        acc = []
        def scan(ps):
            for p in ps:
                if p.get('syn') or p.get('off'): continue
                for v in [p.get('v')] + [k['v'] for k in p.get('k', [])]:
                    if is_col(v) and in_band(v, ACCENT_BAND): acc.append(v[:3])
                scan(p.get('c', []))
        for c in comps:
            for l in c['layers']: scan(l['props'])
        tpl = {'file': d['file'], 'ae_version': d.get('ae_version'), 'comps': comps, 'footage': footage,
               'template': {'shot': s['shot'], 'root': sh['root'], 'window': [round(t0, 5), round(t1, 5)], 'frames': s['frames'],
                            'source': s['source'], 'params': {
                                'texts': texts, 'accent': {'band': ACCENT_BAND, 'uses': len(acc), 'default': max(acc, key=acc.count) if acc else None},
                                'footage': [{'id': f['id'], 'name': f['name'], 'file': f.get('file')} for f in footage if f.get('file')]}}}
        p = f"{out_dir}/shot_{s['shot']:02d}.json"
        json.dump(tpl, open(p, 'w'))
        print(f"shot {s['shot']:>2} {s['frames']:>4}f  comps {len(comps):>2}  footage {len(footage):>3}  texts {len(texts):>2}  accent uses {len(acc):>3}  {s['source'][:40]}")


def recolor(v, band, hue):
    h, l, s = colorsys.rgb_to_hls(*v[:3])
    r = list(colorsys.hls_to_rgb(hue / 360, l, s))
    return [round(x, 5) for x in r] + v[3:]


def apply(tpl_path, params_path, out):
    """params: {"texts": {"<comp>/<i>": "new text" | {text, font, size, fill}}, "accent": [r,g,b] (0-1) or "#rrggbb",
               "footage": {"<id>": "/path/to/new/file"}}"""
    tpl = json.load(open(tpl_path)); P = json.load(open(params_path)); d = copy.deepcopy(tpl)
    band = tuple(d['template']['params']['accent']['band'])
    acc = P.get('accent')
    if isinstance(acc, str): acc = [int(acc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    hue = colorsys.rgb_to_hls(*acc)[0] * 360 if acc else None
    def walk(ps):
        for p in ps:
            if hue is not None and not p.get('syn'):
                if is_col(p.get('v')) and in_band(p['v'], band): p['v'] = recolor(p['v'], band, hue)
                for k in p.get('k', []):
                    if is_col(k['v']) and in_band(k['v'], band): k['v'] = recolor(k['v'], band, hue)
                if isinstance(p.get('v'), dict) and p['v'].get('_text') and is_col(p['v'].get('fill')) and in_band(p['v']['fill'], band):
                    p['v']['fill'] = recolor(p['v']['fill'], band, hue)
            walk(p.get('c', []))
    for c in d['comps']:
        for l in c['layers']:
            walk(l['props'])
            t = l.get('text')
            if not t: continue
            new = P.get('texts', {}).get(f"{c['name']}/{l['i']}")
            if new is not None:
                new = {'text': new} if isinstance(new, str) else new
                t['text'] = new.get('text', t['text']); t['font'] = new.get('font', t['font'])
                t['font_size'] = new.get('size', t['font_size']); t['fill_color'] = new.get('fill', t['fill_color'])
                t.pop('lines', None); t.pop('runs', None)   # AE's stored layout no longer matches the new string
                for p in l['props']:
                    for q in p.get('c', []):
                        if q['m'] == 'ADBE Text Document' and isinstance(q.get('v'), dict):
                            q['v'].update(text=t['text'], font=t['font'], size=t['font_size'], fill=t['fill_color'])
            if hue is not None:
                if is_col(t.get('fill_color')) and in_band(t['fill_color'], band): t['fill_color'] = recolor(t['fill_color'], band, hue)
                for r in t.get('runs', []):
                    if is_col(r.get('fill')) and in_band(r['fill'], band): r['fill'] = recolor(r['fill'], band, hue)
    for f in d['footage']:
        if str(f['id']) in P.get('footage', {}): f['file'] = P['footage'][str(f['id'])]
    json.dump(d, open(out, 'w'))
    print('wrote', out)


if __name__ == '__main__':
    {'make': make, 'apply': apply}[sys.argv[1]](*sys.argv[2:5])
