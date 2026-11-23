"""Render many (project, comp, window) entries in ONE Kaggle job; each comes back as <out dir>/<label>.mp4.
usage: python3 -m kgl.render_multi <manifest.json> <out dir>
manifest: {"footage": {"gen": "/abs/dir", ...}, "entries": [{"project": "/abs/p.json", "comp": "Comp 1", "from": 0, "to": 1.5, "label": "s08",
           "footage": ["gen"] | [], "extra": "--samples 1 --preview 540"}, ...], "fps": 30}
Projects and footage folders are uploaded privately (bought-scene files never go to git)."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)
man = json.load(open(sys.argv[1])); outdir = os.path.abspath(sys.argv[2]); os.makedirs(outdir, exist_ok=True)
tmp = tempfile.mkdtemp(); v = os.path.join(tmp, 'video')
for d in ('engine', 'library/assets'): shutil.copytree(os.path.join(VID, d), os.path.join(v, d))
for f in ('package.json', 'package-lock.json'): shutil.copy(os.path.join(VID, f), v)
TPL = '/home/user/tpl/fonts'
if os.path.isdir(TPL): shutil.copytree(TPL, os.path.join(v, 'tplfonts'), ignore=shutil.ignore_patterns('*zip*'))
for k, d in man.get('footage', {}).items(): shutil.copytree(d, os.path.join(v, 'footage', k))
entries = []
os.makedirs(os.path.join(v, 'project'))
for i, e in enumerate(man['entries']):
    rel = f"project/{i:02d}_{os.path.basename(e['project'])}"; shutil.copy(e['project'], os.path.join(v, rel))
    foot = ','.join(['library/assets'] + [f'footage/{k}' for k in e.get('footage', [])])
    extra = e.get('extra', '--samples 1 --preview 540').replace('footage/', 'footage/')
    entries.append(dict(project=rel, comp=e['comp'], **{'from': e['from'], 'to': e['to']}, label=e['label'], footage=foot, extra=extra.split()))
json.dump(dict(comps=entries, fps=man.get('fps', 30)), open(os.path.join(tmp, 'render.json'), 'w'))
res = os.path.join(tmp, 'res')
subprocess.run([sys.executable, '-m', 'kgl.run', os.path.join(HERE, 'jobs', 'render.py'), res, v, os.path.join(tmp, 'render.json'), '--name', 'render-job'], cwd=VID)
print(open(os.path.join(res, 'kaggle.log')).read()[-3000:] if os.path.exists(os.path.join(res, 'kaggle.log')) else '')
for f in os.listdir(res) if os.path.isdir(res) else []:
    if f.endswith('.mp4'): shutil.move(os.path.join(res, f), os.path.join(outdir, f)); print('->', os.path.join(outdir, f))
