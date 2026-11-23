"""Render manifest entries on this CPU, N at a time. usage: render_local.py <manifest.json> <out dir> [jobs=3] [only,labels]"""
import json, os, subprocess, sys, concurrent.futures as cf
VID = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
man = json.load(open(sys.argv[1])); out = os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 3; only = set(sys.argv[4].split(',')) if len(sys.argv) > 4 else None
def run(e):
    o = f"{out}/{e['label']}.mp4"
    foot = ','.join([os.path.join(VID, 'library/assets')] + [man['footage'][k] for k in e['footage']])
    extra = e['extra'].replace('footage/', '/home/user/tpl/lib/').replace('/luts.json', '/assets/luts.json') if '--luts' in e['extra'] else e['extra']
    cmd = ['node', 'engine/render.mjs', '--project', e['project'], '--footage', foot, '--comp', e['comp'], '--from', str(e['from']), '--to', str(e['to']),
           '--fps', '30', *extra.split(), '--out', o]
    r = subprocess.run(cmd, cwd=VID, capture_output=True, text=True)
    print(e['label'], 'ok' if r.returncode == 0 and os.path.exists(o) else 'FAILED ' + r.stderr[-300:], flush=True); return e['label']
es = [e for e in man['entries'] if not only or e['label'] in only]
with cf.ThreadPoolExecutor(jobs) as ex: list(ex.map(run, es))
print('ALL DONE', flush=True)
