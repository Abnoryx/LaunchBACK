"""Apply the edits saved on the Edit Room page. Read them first:
   ArtifactData list collection=scenes url=<page> out_dir=<dir>   (also collection=project for the whole-reel note)
usage: python3 edit_room/apply_edits.py <dir with scenes/*.json> [--write]
Prints per scene: status, edited lines (was -> now), note. With --write: updates slots.json and writes work/rerender.txt (the labels to re-render)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.dirname(HERE); src = sys.argv[1]; write = '--write' in sys.argv
slots = json.load(open(os.path.join(RUN, 'slots.json'))); rerender, notes, changed = [], [], 0
for f in sorted(glob.glob(os.path.join(src, '**', 's[0-9][0-9].json'), recursive=True)):
    d = json.load(open(f)); d = d.get('data', d); sid = 'gen/' + os.path.basename(f)[:-5]; n = sid.split('/s')[1]
    if sid not in slots: continue
    edits = []
    for w in (d.get('words') or []) + (d.get('chrome') or []):
        if w['k'] in slots[sid] and slots[sid][w['k']] != w['v']: edits.append((w['k'], slots[sid][w['k']], w['v']))
    st = d.get('status', ''); note = (d.get('note') or '').strip()
    if edits or st == 'change' or note: print(f"scene {n}: status={st or '-'}; {len(edits)} line(s) edited" + (f"; note: {note}" if note else ''))
    for k, a, b in edits: print(f"   '{a}' -> '{b}'   (slot: {k!r})")
    if edits or st == 'change': rerender.append(n)
    if note: notes.append((n, note))
    if write:
        for k, a, b in edits: slots[sid][k] = b; changed += 1
if write:
    json.dump(slots, open(os.path.join(RUN, 'slots.json'), 'w'), ensure_ascii=False)
    open(os.path.join(RUN, 'work', 'rerender.txt'), 'w').write(','.join(rerender)); json.dump(notes, open(os.path.join(RUN, 'work', 'edit_notes.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'wrote slots.json ({changed} lines); re-render: {",".join(rerender) or "nothing"}; notes saved to work/edit_notes.json')
