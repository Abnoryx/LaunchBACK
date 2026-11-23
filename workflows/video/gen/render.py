"""Swappable render backend (gen/config.json 'render_backend'). Add a new platform as one function here.
usage: python3 -m gen.render <project.json> <out.mp4> <comp> [<comp> ...]
(from code: render(project, out, comps, opts) with opts = extra kgl.render options)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)


def kaggle(project, out, comps, opts=()):   # opts: extra kgl.render options, e.g. ['--extra', '--preview 540', '--shots', f]
    return subprocess.run([sys.executable, '-m', 'kgl.render', project, out, *comps, *opts], cwd=VID).returncode


def local(project, out, comps, opts=()):   # CPU fallback, slow (~5-10 s/frame at 1080p)
    if opts: sys.exit(f'local backend does not take {opts}: use kaggle')
    proj = json.load(open(project)); durs = {c['name']: c['dur'] for c in proj['comps']}; parts = []
    for c in comps:
        o = f'/tmp/gen_{c}.mp4'; parts.append(o)
        subprocess.run(['node', 'engine/render.mjs', '--project', project, '--footage', 'library/assets', '--comp', c,
                        '--from', '0', '--to', str(durs[c]), '--fps', '30', '--samples', '1', '--out', o], cwd=VID, check=True)
    open('/tmp/gen_list.txt', 'w').write('\n'.join(f"file '{p}'" for p in parts))
    return subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', '/tmp/gen_list.txt',
                           '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out]).returncode


BACKENDS = {'kaggle': kaggle, 'local': local}


def render(project, out, comps, opts=()):
    return BACKENDS[json.load(open(os.path.join(HERE, 'config.json')))['render_backend']](project, out, comps, opts)

if __name__ == '__main__':
    sys.exit(render(sys.argv[1], sys.argv[2], sys.argv[3:]))
