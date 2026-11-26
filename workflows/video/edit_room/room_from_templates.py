"""/rescene -> room.json: one scene per extracted shot template, so a rescened reel gets the same Edit Room as a /gen reel.
usage: python3 edit_room/room_from_templates.py <templates dir (…/lib/<reel>/templates)> <clips.json {"reel": url, "01": url, …}> <room.json> [title]"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from gen.groups import scene_info
d, clips, out = sys.argv[1], (json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}), sys.argv[3]
scenes = []
for f in sorted(glob.glob(f'{d}/shot_*.json')):
    n = '%02d' % int(re.search(r'shot_(\d+)', f).group(1)); i = scene_info(f)
    scenes.append({'id': 's' + n, 'n': n, 'sec': i['seconds'], 'clip': clips.get(n, ''), 'words': [{'k': s, 'v': s} for s in i['strings']], 'chrome': []})
cuts = [round(sum(s['sec'] for s in scenes[:i + 1]), 3) for i in range(len(scenes) - 1)]
json.dump({'title': sys.argv[4] if len(sys.argv) > 4 else 'Rescene', 'run': os.path.basename(os.path.dirname(os.path.abspath(d))), 'sub': 'rescene · ' + os.path.basename(os.path.dirname(os.path.abspath(d))), 'reel': clips.get('reel', ''), 'cuts': cuts, 'scenes': scenes}, open(out, 'w'), ensure_ascii=False)
print(len(scenes), 'scenes ->', out)
