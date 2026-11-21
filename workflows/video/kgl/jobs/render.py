# Render comps on the Kaggle T4. Inputs (from kgl/render.py): video/ (engine, package*.json, project, assets), render.json
# render.json: {"project": "scratch/x.json", "footage": "library/assets", "comps": [[name, dur], ...],
#               "extra": ["--samples", "1"], "out": "name.mp4", "crf": 17}
import json, time
cfg = json.load(open('render.json'))
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'nodejs-wheel-binaries>=22,<23'], check=True)   # apt's node 18 is too old for playwright
import nodejs_wheel; NW = os.path.dirname(nodejs_wheel.__file__); os.environ['PATH'] = NW + '/bin:' + os.environ['PATH']
NPM = f'node {NW}/lib/node_modules/npm/bin/npm-cli.js'; NPX = f'node {NW}/lib/node_modules/npm/bin/npx-cli.js'   # the wheel's bin/npm shims are broken
print('node', sh('node -v').stdout.strip(), sh('which ffmpeg || apt-get install -y -qq ffmpeg').stdout.strip())
os.makedirs('/home/user/tpl', exist_ok=True)
if os.path.isdir('video/tplfonts') and not os.path.exists('/home/user/tpl/fonts'): os.symlink(os.path.abspath('video/tplfonts'), '/home/user/tpl/fonts')
os.chdir('video'); r = sh(f'{NPM} ci --silent && {NPM} i --no-save --silent playwright@1.63.0 && {NPX} playwright install --with-deps chromium')   # playwright is global locally, not in package.json; print('setup', r.returncode, r.stderr[-300:])
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
