"""Render comps of a project on the Kaggle T4 and download the stitched MP4.
usage: python3 -m kgl.render <project.json> <out.mp4> <comp[:dur]> ... [--extra "--samples 1 --preview 480"] [--crf 17]
Durations default to the comp's 'dur' in the project. Uploads engine, package*.json, the project and library/assets."""
import argparse, json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('out'); ap.add_argument('comps', nargs='+')
ap.add_argument('--extra', default='--samples 1'); ap.add_argument('--crf', type=int, default=17)
a = ap.parse_args()
proj = json.load(open(a.project)); durs = {c['name']: c['dur'] for c in proj['comps']}
comps = [[c.split(':')[0], float(c.split(':')[1]) if ':' in c else durs[c]] for c in a.comps]
tmp = tempfile.mkdtemp(); v = os.path.join(tmp, 'video')
for d in ('engine', 'library/assets'): shutil.copytree(os.path.join(VID, d), os.path.join(v, d))
for f in ('package.json', 'package-lock.json'): shutil.copy(os.path.join(VID, f), v)
rel = os.path.relpath(os.path.abspath(a.project), VID); os.makedirs(os.path.dirname(os.path.join(v, rel)), exist_ok=True)
shutil.copy(a.project, os.path.join(v, rel))
json.dump(dict(project=rel, footage='library/assets', comps=comps, extra=a.extra.split(), out=os.path.basename(a.out), crf=a.crf),
          open(os.path.join(tmp, 'render.json'), 'w'))
res = os.path.join(tmp, 'res')
r = subprocess.run([sys.executable, '-m', 'kgl.run', os.path.join(HERE, 'jobs', 'render.py'), res, v, os.path.join(tmp, 'render.json'),
                    '--name', 'render-job'], cwd=VID)
print(open(os.path.join(res, 'kaggle.log')).read()[-3000:] if os.path.exists(os.path.join(res, 'kaggle.log')) else '')
if os.path.exists(os.path.join(res, os.path.basename(a.out))): shutil.move(os.path.join(res, os.path.basename(a.out)), a.out); print('->', a.out)
else: sys.exit('render failed')
