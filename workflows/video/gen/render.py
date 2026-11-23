"""Swappable render backend (gen/config.json 'render_backend'). Add a new platform as one function here.
usage: python3 -m gen.render <project.json> <out.mp4> <comp> [<comp> ...]
(from code: render(project, out, comps, opts) with opts = extra kgl.render options)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)


def kaggle(project, out, comps, opts=()):   # opts: extra kgl.render options, e.g. ['--extra', '--preview 540', '--shots', f]
    return subprocess.run([sys.executable, '-m', 'kgl.render', project, out, *comps, *opts], cwd=VID).returncode


def local(project, out, comps, opts=()):   # this CPU (slow): same options as kgl.render (--extra, --footage, --shots, --only)
    o = dict(zip(opts[::2], opts[1::2])); proj = json.load(open(project)); durs = {c['name']: c['dur'] for c in proj['comps']}
    jobs = [(c.split(':')[0], 0.0, float(c.split(':')[1]) if ':' in c else durs[c], c.split(':')[0]) for c in comps]
    if '--shots' in o:   # one scene per entry of shots.json (cuts in frames)
        sj = json.load(open(o['--shots'])); cu, nm, fps = sj['cuts'], sj['names'], sj.get('fps', 30)
        want = set(o['--only'].split(',')) if '--only' in o else None
        jobs = [(jobs[0][0], cu[i] / fps, cu[i + 1] / fps, nm[i].split(' ')[0]) for i in range(len(nm)) if not want or nm[i].split(' ')[0] in want]
    od = os.path.dirname(os.path.abspath(out)); parts = []
    footage = 'library/assets' + (',' + os.path.abspath(o['--footage']) if '--footage' in o else '')
    extra = o.get('--extra', '--samples 1').replace('footage/', os.path.abspath(o.get('--footage', '.')) + '/').split()
    for c, a, b, label in jobs:
        f = os.path.join(od, label + '.mp4')
        r = subprocess.run(['node', 'engine/render.mjs', '--project', os.path.abspath(project), '--footage', footage, '--comp', c,
                            '--from', str(a), '--to', str(b), '--fps', '30', *extra, '--out', f], cwd=VID)
        print(label, 'ok' if r.returncode == 0 else 'FAILED', flush=True)
        if r.returncode == 0: parts.append(f)
    open(os.path.join(od, 'list.txt'), 'w').write('\n'.join(f"file '{p}'" for p in parts))
    return subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(od, 'list.txt'),
                           '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out]).returncode if parts else 1


BACKENDS = {'kaggle': kaggle, 'local': local}


def render(project, out, comps, opts=()):
    return BACKENDS[json.load(open(os.path.join(HERE, 'config.json')))['render_backend']](project, out, comps, opts)

if __name__ == '__main__':
    sys.exit(render(sys.argv[1], sys.argv[2], sys.argv[3:]))
