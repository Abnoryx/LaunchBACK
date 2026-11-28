"""forty_hours_sells: room.json from slots.json + the sells templates (words each scene shows) + clips.json, then the SHARED edit_room/build.py.
usage (from workflows/video): python3 gen/runs/forty_hours_sells/edit_room/build_page.py <out.html> [round-label]"""
import json, os, subprocess, sys, glob, re
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.dirname(HERE); VID = os.path.abspath(os.path.join(RUN, '..', '..', '..'))
slots = json.load(open(os.path.join(RUN, 'slots.json'))); man = json.load(open(os.path.join(RUN, 'work', 'manifest.json')))
plan = json.load(open(os.path.join(RUN, 'plan.json')))
clips = json.load(open(os.path.join(HERE, 'clips.json'))) if os.path.exists(os.path.join(HERE, 'clips.json')) else {}
CHROME = {'1', 'st', '+', '| |', '2 min ago', 'Follow', 'View all notification', 'Earnera.co', 'earnera.co', 'earnera', 'iMessage', 'Today, 11:11'}
data = []
KEEP = int(os.environ.get('KEEP', '17'))   # scenes after the voice-over ends are dropped (user, 2026-11-28)
for e, s in list(zip(man['entries'], plan['scenes']))[:KEEP]:
    n = e['label']; words, chrome = [], []
    for k in dict.fromkeys(x.strip() for x in s.get('original', [])):
        if k in slots: (chrome if k in CHROME else words).append({'k': k, 'v': slots[k]})
    data.append({'id': 's' + n, 'n': n, 'sec': round(e['to'] - e['from'], 3), 'clip': clips.get(n, ''), 'words': words, 'chrome': chrome})
dur = [d['sec'] for d in data]; cuts = [round(sum(dur[:i + 1]), 3) for i in range(len(dur) - 1)]
room = {'title': 'Forty hours reel (sells)', 'run': 'forty_hours_sells', 'sub': 'forty_hours_sells · ' + (sys.argv[2] if len(sys.argv) > 2 else 'round 1'),
        'scenes': data, 'reel': clips.get('reel', ''), 'cuts': cuts}
tmp = os.path.join(HERE, 'room.json'); json.dump(room, open(tmp, 'w'), ensure_ascii=False)
subprocess.run([sys.executable, os.path.join(VID, 'edit_room', 'build.py'), tmp, sys.argv[1]], check=True)
