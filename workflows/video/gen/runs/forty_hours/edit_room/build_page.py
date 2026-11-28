"""forty_hours: writes room.json from build.py SHOTS + scenes.json + clips.json, then the SHARED edit_room/build.py makes the page.
usage (from workflows/video): python3 gen/runs/forty_hours/edit_room/build_page.py <out.html> [round-label]"""
import importlib.util, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.dirname(HERE); VID = os.path.abspath(os.path.join(RUN, '..', '..', '..'))
spec = importlib.util.spec_from_file_location('forty_build', os.path.join(RUN, 'build.py')); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
sc = json.load(open(os.path.join(RUN, 'scenes.json')))
clips = json.load(open(os.path.join(HERE, 'clips.json'))) if os.path.exists(os.path.join(HERE, 'clips.json')) else {}
data = []
for i, (name, tpl, params) in enumerate(B.SHOTS):
    n = f'{i + 1:02d}'
    words = [{'k': k, 'v': v} for k, v in params.get('words', {}).items()]
    data.append({'id': 's' + n, 'n': n, 'sec': sc['durs'][i], 'clip': clips.get(n, ''), 'words': words, 'chrome': []})
cuts = [round(sum(sc['durs'][:i + 1]), 3) for i in range(len(sc['durs']) - 1)]
room = {'title': 'Forty hours reel', 'run': 'forty_hours', 'sub': 'forty_hours · ' + (sys.argv[2] if len(sys.argv) > 2 else 'round 1'), 'scenes': data, 'reel': clips.get('reel', ''), 'cuts': cuts}
tmp = os.path.join(HERE, 'room.json'); json.dump(room, open(tmp, 'w'), ensure_ascii=False)
subprocess.run([sys.executable, os.path.join(VID, 'edit_room', 'build.py'), tmp, sys.argv[1]], check=True)
