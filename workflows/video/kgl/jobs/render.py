# Render comps on the Kaggle T4. Inputs (from kgl/render.py): video/ (engine, package*.json, project, assets), render.json
# render.json: {"project": "scratch/x.json", "footage": "library/assets", "comps": [[name, dur], ...],
#               "extra": ["--samples", "1"], "out": "name.mp4", "crf": 17}
import json, time
cfg = json.load(open('render.json'))
sh('apt-get install -y -qq nodejs npm ffmpeg')
os.chdir('video'); r = sh('npm ci --silent && npx playwright install --with-deps chromium'); print('setup', r.returncode, r.stderr[-300:])
os.environ['RENDER_GPU'] = '1'
lst = []
for name, dur in cfg['comps']:
    t = time.time(); o = f'/kaggle/working/shots/{name}.mp4'; os.makedirs('/kaggle/working/shots', exist_ok=True)
    r = subprocess.run(['node', 'engine/render.mjs', '--project', cfg['project'], '--footage', cfg['footage'], '--comp', name, '--from', '0',
                        '--to', str(dur), '--fps', '30', *cfg.get('extra', []), '--out', o], capture_output=True, text=True)
    print(name, r.returncode, f'{time.time() - t:.0f}s', r.stdout[-200:].replace('\n', ' | '), r.stderr[-300:], flush=True)
    lst.append(f"file '{o}'")
open('/kaggle/working/list.txt', 'w').write('\n'.join(lst))
sh(f"ffmpeg -v error -y -f concat -safe 0 -i /kaggle/working/list.txt -c:v libx264 -crf {cfg.get('crf', 17)} -pix_fmt yuv420p {os.environ['OUT']}/{cfg['out']}")
print('done', os.listdir(os.environ['OUT']))
