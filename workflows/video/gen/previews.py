"""Shot previews: every library shot rendered once exactly as stored (its own words/props, nothing changed), cached.
Runs at the start of every /gen: only shots without a preview are rendered (Kaggle, 540p, via gen.render).
  ours          -> library/previews/<id>.mp4 + <id>.jpg            (committed)
  bought scenes -> /home/user/tpl/previews/<reel>/sNN.mp4 + .jpg     (private: kgl.tpl_backup only, never git)
<id>.jpg = 3 key frames (20/50/80 %) side by side. Then gen.embed describes the new shots.
usage: python3 -m gen.previews [--dry]     (--dry: only list what is missing)"""
import glob, importlib, json, os, shutil, subprocess, sys, tempfile
from . import library as LIB
from .render import render
VID = LIB.VID; TPL = LIB.TPL
OPTS = '--samples 1 --preview 540'


def strip(mp4, jpg):
    """3 key frames (20/50/80 % of the shot) side by side, 480 px tall."""
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4],
                             capture_output=True, text=True).stdout.strip() or 0)
    tmp = tempfile.mkdtemp(); fr = []
    for i, f in enumerate((0.2, 0.5, 0.8)):
        o = os.path.join(tmp, f'{i}.png'); fr.append(o)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{d * f:.3f}', '-i', mp4, '-frames:v', '1', '-vf', 'scale=-2:480', o], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *sum([['-i', o] for o in fr], []), '-filter_complex', 'hstack=inputs=3', '-q:v', '3', jpg], check=True)
    shutil.rmtree(tmp)


def keep(mp4, e):
    base = e['preview']; os.makedirs(os.path.dirname(base), exist_ok=True)
    shutil.move(mp4, base + '.mp4'); strip(base + '.mp4', base + '.jpg'); print('preview', e['id'], '->', base + '.mp4')


def ours(todo):
    """Build every missing template with its stored defaults into one project; one Kaggle job renders them all."""
    from library.aeb import Project
    from library import style as S
    p, comps = Project(), []
    for e in todo:
        try:
            m = importlib.import_module(f"library.templates.{e['id']}"); m.build(p, e['id']); comps.append(f"{e['id']}:{m.DUR_F * S.F:.5f}")
        except Exception as ex:   # e.g. data-driven templates (cine_scene) store no content of their own
            print(f"no preview for {e['id']}: its stored defaults don't build ({type(ex).__name__}: {str(ex)[:100]})")
    if not comps: return
    tmp = tempfile.mkdtemp(dir=os.path.join(VID, 'scratch')); proj = p.dump(os.path.join(tmp, 'previews.json'))
    render(proj, os.path.join(tmp, 'all.mp4'), comps, ['--extra', OPTS])
    for e in todo:
        if os.path.exists(os.path.join(tmp, e['id'] + '.mp4')): keep(os.path.join(tmp, e['id'] + '.mp4'), e)
    shutil.rmtree(tmp)


def footage(reel):
    """The reel's harvested .aep assets (+ its measured LUTs); unzip + harvest them first if this container lacks them."""
    lib = f'{TPL}/lib/{reel}'; dump = f'{lib}/{reel}.json'; assets = f'{lib}/assets'
    if not os.path.isdir(assets):
        aep = json.load(open(dump))['file']; x = f'{TPL}/x/{reel}'
        if not os.path.isdir(x):
            for z in glob.glob(f'{TPL}/zips/*.zip'):
                if os.path.basename(aep) in subprocess.run(['unzip', '-l', z], capture_output=True, text=True).stdout:
                    subprocess.run(['unzip', '-q', '-o', z, '-d', x], check=True); break
        subprocess.run([sys.executable, '-m', 'extract.aep_harvest', dump, x, reel], cwd=VID, check=True)
    for l in (f'{lib}/luts.json', f'{lib}/render_footage/luts.json'):
        if os.path.exists(l) and not os.path.exists(f'{assets}/luts.json'): shutil.copy(l, f'{assets}/luts.json')
    return assets


def bought(reel, todo):
    """Render the reel's missing scenes straight from its dump (== the scene templates, pixel-identical)."""
    lib = f'{TPL}/lib/{reel}'; assets = footage(reel); tmp = tempfile.mkdtemp()
    extra = OPTS + (' --luts footage/luts.json' if os.path.exists(f'{assets}/luts.json') else '')
    root = json.load(open(f'{lib}/shots.json'))['root']
    render(f'{lib}/{reel}.json', os.path.join(tmp, 'all.mp4'), [root],
           ['--shots', f'{lib}/parity_shots.json', '--only', ','.join(e['id'].split('/')[1] for e in todo), '--footage', assets, '--extra', extra])
    for e in todo:
        f = os.path.join(tmp, e['id'].split('/')[1] + '.mp4')
        if os.path.exists(f): keep(f, e)
    shutil.rmtree(tmp)


def main(dry=False):
    S = LIB.shots(); todo = [e for e in S.values() if not LIB.has_preview(e)]
    mine = [e for e in todo if e['kind'] == 'template' and os.path.exists(os.path.join(VID, e['file']))]
    reels = {}
    for e in todo:
        if e['kind'] == 'aep_scene' and os.path.exists(f"{TPL}/lib/{e.get('reel')}/parity_shots.json"): reels.setdefault(e['reel'], []).append(e)
    print(f"{len(S)} shots; missing previews: {len(mine)} ours" + ''.join(f', {len(v)} {k}' for k, v in reels.items()))
    if dry: return
    if mine: ours(mine)
    for reel, es in reels.items(): bought(reel, es)
    from . import embed
    embed.update()
    if reels: subprocess.run([sys.executable, '-m', 'kgl.tpl_backup', 'backup'], cwd=VID)   # private previews survive the container


if __name__ == '__main__':
    main('--dry' in sys.argv)
