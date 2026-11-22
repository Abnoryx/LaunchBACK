"""Route A step 2: what in a dumped project the engine can't draw yet — before spending any render time.
usage: python3 -m extract.aep_coverage <dump.json> [out.json]
Lists effects, expressions, blend modes, matte types, mask modes and layer types, with the comps that use them, and
flags the unsupported ones. Only enabled layers inside comps reachable from the render root count."""
import sys, json, re, subprocess, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, '..', 'engine')
src = open(os.path.join(ENGINE, 'engine.js')).read()
FX_OK = set(re.findall(r"case '([^']+)'", src))
BLEND_OK = {int(k) for k in re.findall(r'(\d{4}):', re.search(r'export const BLEND = \{([^}]*)\}', open(os.path.join(ENGINE, 'gl.js')).read()).group(1))} | {5240, 5242}
MATTE_OK = {5012, 5013, 5014, 5015, 5016}
MASK_OK = {6812, 6813, 6814, 6815}
LAYER_OK = {'AVLayer', 'TextLayer', 'ShapeLayer', 'CameraLayer', 'ThreeDModelLayer'}
AUDIO_FX = re.compile(r'^ADBE Aud')


def classify(exprs):
    """Run the engine's own expression classifier (anim.js) so the report can't drift from the engine."""
    js = "import {classifyExpression} from './anim.js'; const xs = JSON.parse(require('fs').readFileSync(0,'utf8'));" \
         "process.stdout.write(JSON.stringify(xs.map((x) => (classifyExpression(x) || {}).kind || null)));"
    js = js.replace("require('fs')", "(await import('fs')).default")
    r = subprocess.run(['node', '--input-type=module', '-e', js], input=json.dumps(exprs), capture_output=True, text=True, cwd=ENGINE)
    if r.returncode: raise SystemExit(r.stderr)
    return json.loads(r.stdout)


def main(path, out=None):
    d = json.load(open(path))
    comps = {c['id']: c for c in d['comps']}
    by_name = {c['name']: c for c in d['comps']}
    use = collections.defaultdict(lambda: collections.defaultdict(set))   # kind -> key -> comps
    exprs = {}

    def walk(props, comp):
        for p in props:
            if p.get('off'): continue
            if p.get('x'): exprs.setdefault(p['x'], set()).add(comp)
            if p.get('m') == 'ADBE Effect Parade':
                for e in p.get('c') or []:
                    if not e.get('off'): use['effect'][e['m'] + ' (' + str(e.get('n')) + ')'].add(comp) if e['m'] not in FX_OK and not AUDIO_FX.match(e['m']) and not e['m'].startswith('Pseudo/') else None
            if p.get('m') == 'ADBE Mask Atom' and p.get('mode') not in MASK_OK: use['mask_mode'][p.get('mode')].add(comp)
            walk(p.get('c') or [], comp)

    # comps reachable from the root (comp nobody else uses as a layer source)
    used = {l.get('src_id') for c in d['comps'] for l in c['layers'] if l.get('src_type') == 'CompItem'}
    roots = [c for c in d['comps'] if c['id'] not in used and c['layers']]
    seen, stack = set(), [c['id'] for c in roots]
    while stack:
        cid = stack.pop()
        if cid in seen or cid not in comps: continue
        seen.add(cid); c = comps[cid]
        for l in c['layers']:
            if l.get('enabled') is not True: continue
            if l.get('src_type') == 'CompItem': stack.append(l['src_id'])
            if l['type'] not in LAYER_OK: use['layer_type'][l['type']].add(c['name'])
            if l.get('blending_mode') not in BLEND_OK and l.get('blending_mode') is not None: use['blend_mode'][l['blending_mode']].add(c['name'])
            if l.get('track_matte_type') not in MATTE_OK and l.get('track_matte_type') is not None: use['matte'][l['track_matte_type']].add(c['name'])
            walk(l.get('props') or [], c['name'])
    xs = list(exprs)
    for x, k in zip(xs, classify(xs)):
        if k in (None, 'unknown'): use['expression'][x.replace('\n', ' ')[:100]] |= exprs[x]
    rep = {'roots': [c['name'] for c in roots], 'comps_reached': len(seen), 'comps_total': len(comps),
           'unsupported': {k: {str(kk): sorted(v) for kk, v in sorted(m.items(), key=lambda i: -len(i[1]))} for k, m in use.items()}}
    if out: json.dump(rep, open(out, 'w'), indent=1)
    print(f"roots {rep['roots']}  comps reached {rep['comps_reached']}/{rep['comps_total']}")
    for k, m in rep['unsupported'].items():
        print(f"\n{k}: {len(m)} unsupported")
        for kk, v in m.items(): print(f"  {kk}  <- {len(v)} comp(s): {', '.join(v[:4])}{' ...' if len(v) > 4 else ''}")
    return rep


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
