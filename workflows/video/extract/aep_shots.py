"""Route A step 4: split a dumped project into shots and cross-check them against the posted mp4's cuts.
usage: python3 -m extract.aep_shots <dump.json> <root comp> <run name (extract/runs/<name>/measure.json)> <out.json>
Shot boundaries come from the project: in-points of the root comp's enabled, normal-blend picture layers (precomps,
footage). Overlays (screen/add), audio, adjustment and null layers don't start shots. Each boundary is matched to the
nearest detected cut; the median offset is the time map (mp4 frame = project frame + offset). Detected cuts with no
project boundary are listed as inner cuts (whips, flashes, text swaps inside one shot)."""
import sys, os, json, statistics

NORMAL = 5212
HERE = os.path.dirname(os.path.abspath(__file__))


def main(dump, root, run, out):
    d = json.load(open(dump))
    comp = next(c for c in d['comps'] if c['name'] == root)
    fps = comp['fps']
    footage = {f['id']: f for f in d['footage']}
    m = json.load(open(os.path.join(HERE, 'runs', run, 'measure.json')))
    info = json.load(open(os.path.join(HERE, 'runs', run, 'info.json')))
    n_frames = info.get('n_frames') or info.get('frames') or int(round(info['duration'] * fps))
    cuts = m['cuts']
    layers = []
    for l in comp['layers']:
        if l.get('enabled') is not True or l.get('adjustment_layer') or l.get('null_layer'): continue
        if l.get('blending_mode') not in (NORMAL, None): continue
        if l.get('src_type') == 'FootageItem' and not footage.get(l['src_id'], {}).get('has_video', True): continue
        if l.get('src_type') not in ('CompItem', 'FootageItem'): continue
        a, b = round(l['in_point'] * fps), min(round(l['out_point'] * fps), n_frames)
        if a < n_frames and b > a: layers.append((a, b, l['name'], l['src_type'], l['i']))
    starts = sorted({a for a, *_ in layers})
    # merge boundaries 1 frame apart (precomp overlap handles), keep the later one
    bounds = []
    for s in starts:
        if bounds and s - bounds[-1] <= 1: bounds[-1] = s
        else: bounds.append(s)
    near = lambda f: min(cuts, key=lambda c: abs(c - f)) if cuts else None
    offs = [near(b) - b for b in bounds[1:] if near(b) is not None and abs(near(b) - b) <= 6]
    offset = round(statistics.median(offs)) if offs else 0
    shots = []
    for i, s in enumerate(bounds):
        e = bounds[i + 1] if i + 1 < len(bounds) else n_frames
        main_l = [x for x in layers if x[0] <= s < x[1]]
        main_l.sort(key=lambda x: (x[0] != s, x[4]))   # the layer starting here, topmost first
        c = near(s) if s else 0
        if s and (c is None or abs(c - s - offset) > 6): c = None   # no detected cut here (e.g. a momentum-matched whip)
        shots.append({'shot': i + 1, 'start': s, 'end': e, 'frames': e - s, 'source': main_l[0][2] if main_l else None,
                      'source_type': main_l[0][3] if main_l else None, 'layers': [x[2] for x in main_l],
                      'mp4_cut': c, 'cut_delta': (c - s - offset) if c is not None and s else None})
    matched = {sh['mp4_cut'] for sh in shots}
    inner = [c for c in cuts if c not in matched and c < n_frames - 1]
    rep = {'root': root, 'fps': fps, 'frames': n_frames, 'time_offset': offset, 'shots': shots, 'inner_cuts': inner}
    json.dump(rep, open(out, 'w'), indent=1)
    print(f'{len(shots)} shots, time offset {offset} f, inner cuts {inner}')
    for s in shots:
        flag = '  <- no cut detected in the mp4' if s['start'] and s['mp4_cut'] is None else \
            '' if not s['cut_delta'] or abs(s['cut_delta']) <= 1 else f"  <- mp4 cut {s['mp4_cut']} ({s['cut_delta']:+d} f)"
        print(f"{s['shot']:>3} {s['start']:>5}-{s['end']:<5} {s['frames']:>4}f  {s['source']}{flag}")


if __name__ == '__main__':
    main(*sys.argv[1:5])
