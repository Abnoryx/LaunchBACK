"""Render comps of a project on the Kaggle T4 and download the stitched MP4.
usage: python3 -m kgl.render <project.json> <out.mp4> <comp[:dur]> ... [--extra "--samples 1 --preview 480"] [--crf 17]
       [--shots shots.json [--only s01,s06]]  (render <comp> scene by scene: cuts/names json as parity uses; each scene
       comes back as <out dir>/<name>.mp4 and <out.mp4> is them stitched. Rule: v1 and v2 at --preview 540, final full res)
       [--footage DIR]  (extra footage folder, e.g. a harvested .aep project's assets; private upload)
Durations default to the comp's 'dur' in the project. Uploads engine, package*.json, the project and library/assets."""
import argparse, json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('out'); ap.add_argument('comps', nargs='+')
ap.add_argument('--extra', default='--samples 1'); ap.add_argument('--crf', type=int, default=17); ap.add_argument('--footage'); ap.add_argument('--shots'); ap.add_argument('--only')
a = ap.parse_args()
proj = json.load(open(a.project)); durs = {c['name']: c['dur'] for c in proj['comps']}
comps = [[c.split(':')[0], float(c.split(':')[1]) if ':' in c else durs[c]] for c in a.comps]
if a.shots:   # one entry per scene of the (single) comp
    sj = json.load(open(a.shots)); cu, nm = sj['cuts'], sj['names']; fps = sj.get('fps', 30)
    want = set(a.only.split(',')) if a.only else None
    comps = [[comps[0][0], cu[i] / fps, cu[i + 1] / fps, nm[i].split(' ')[0]] for i in range(len(nm)) if not want or nm[i].split(' ')[0] in want]
tmp = tempfile.mkdtemp(); v = os.path.join(tmp, 'video')
for d in ('engine', 'library/assets'): shutil.copytree(os.path.join(VID, d), os.path.join(v, d))
for f in ('package.json', 'package-lock.json'): shutil.copy(os.path.join(VID, f), v)
TPL = '/home/user/tpl/fonts'   # licensed fonts the page loads by absolute path (/file/home/user/tpl/fonts/...); private upload only
if os.path.isdir(TPL): shutil.copytree(TPL, os.path.join(v, 'tplfonts'), ignore=shutil.ignore_patterns('*zip*'))
if a.footage: shutil.copytree(a.footage, os.path.join(v, 'footage'))
rel = os.path.relpath(os.path.abspath(a.project), VID)
if rel.startswith('..'): rel = 'project/' + os.path.basename(a.project)   # private project outside the repo
os.makedirs(os.path.dirname(os.path.join(v, rel)), exist_ok=True)
shutil.copy(a.project, os.path.join(v, rel))
json.dump(dict(project=rel, footage='library/assets,footage' if a.footage else 'library/assets', comps=comps, extra=a.extra.split(), out=os.path.basename(a.out), crf=a.crf),
          open(os.path.join(tmp, 'render.json'), 'w'))
res = os.path.join(tmp, 'res')
r = subprocess.run([sys.executable, '-m', 'kgl.run', os.path.join(HERE, 'jobs', 'render.py'), res, v, os.path.join(tmp, 'render.json'),
                    '--name', 'render-job'], cwd=VID)
print(open(os.path.join(res, 'kaggle.log')).read()[-3000:] if os.path.exists(os.path.join(res, 'kaggle.log')) else '')
od = os.path.dirname(os.path.abspath(a.out)); os.makedirs(od, exist_ok=True)
for f in os.listdir(res) if os.path.isdir(res) else []:
    if f.endswith('.mp4'): shutil.move(os.path.join(res, f), os.path.join(od, f)); print('->', os.path.join(od, f))
if not os.path.exists(a.out): sys.exit('render failed (scenes that finished are kept above)')
