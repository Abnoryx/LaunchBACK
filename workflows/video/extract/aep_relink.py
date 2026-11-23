"""Route A: relink re-imported renders to their live comps.
usage: python3 -m extract.aep_relink <dump.json>          (rewrites the dump in place, lists what it changed)
Creators often render a comp (e.g. "Comp 1" -> "Comp 1_2.mp4"), re-import the render into a final comp ("sound design")
and add overlays there (light leaks, bokeh). The posted reel is that final comp. Rendering only the inner comp drops
those overlays (gen: the bokeh flash into the football shot). A footage layer whose file is named after a comp
("<comp>.mp4", "<comp>_2.mov", ...) and matches its size becomes a precomp layer of that comp, so the final comp can be
rendered live. Render the comp that holds the relinked layer as the root."""
import json, os, re, sys


def main(path):
    d = json.load(open(path))
    comps = {c['name']: c for c in d['comps']}
    foot = {f['id']: f for f in d['footage']}
    changed = []
    for c in d['comps']:
        for L in c['layers']:
            f = foot.get(L.get('src_id')) if L.get('src_type') == 'FootageItem' else None
            if not f or not f.get('file'): continue
            stem = os.path.splitext(re.split(r'[\\/]', f['file'])[-1])[0]
            m = re.match(r'^(.*?)(?:_\d+)?$', stem)
            target = comps.get(m.group(1)) if m else None
            if not target or target is c or (f.get('width'), f.get('height')) != (target['w'], target['h']): continue
            L['src_type'], L['src_id'], L['relinked_from'] = 'CompItem', target['id'], f['file']
            changed.append((c['name'], L['name'], target['name']))
    d['relinked'] = changed
    json.dump(d, open(path, 'w'))
    for x in changed: print(f'{x[0]} / {x[1]} -> comp "{x[2]}"')
    print(len(changed), 'relinked')


if __name__ == '__main__':
    main(sys.argv[1])
