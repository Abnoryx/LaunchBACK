"""Finishing pass per shot, from the user's tutorial reels:
 camera (DQu3nYiCepd): camera never still - slow eased dolly push-in (+6%) with a small truck drift, alternating direction (2.5D shots already move);
 texturising (DL24UePpHWN, DdB21JrTK6w): never lower opacity - remap the TEXTURE with curves, then the blend mode that fits it:
   paper world -> folded-paper texture on WHITE -> Darken group (Multiply); dark world -> scuff/dust on BLACK -> Lighten group (Screen);
   plus Displacement Map by the texture's luma (~2 px) so edges follow the fibres; light film grain last (own finish).
usage: finish.py <in dir with NN.mp4> <out dir> [labels,...]"""
import glob, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = '/home/user/tpl/lib/sells/assets'
PAPER = f'{TEX}/Texturelabs_Paper_361M.jpg'; GRUNGE = f'{TEX}/grunge.jpg'
DUST = glob.glob(f'{TEX}/y2mate*dirt_vintage_film_dust*.mp4')[0] if glob.glob(f'{TEX}/y2mate*dirt_vintage_film_dust*.mp4') else None
WORLD = {int(k): v for k, v in enumerate([s['world'] for s in json.load(open(os.path.join(HERE, 'plan.json')))['shots']], 1)}
WORLD[10] = 'dark'; WORLD[12] = 'paper'   # the 2.5D scenes (red / cream backdrops)
SKIP_CAM = {10, 12, 23}                  # 2.5D shots carry their own camera; the logo sting keeps its own push
W, H = 540, 960
dur = lambda f: float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)


def run(n, src, out):
    d = dur(src); world = WORLD[n]; sgn = 1 if n % 2 else -1
    z = 'pow(t/%.3f,0.8)' % d
    cam = f"scale=w='trunc({W}*(1+0.06*{z})/2)*2':h='trunc({H}*(1+0.06*{z})/2)*2':eval=frame,crop={W}:{H}:x='(iw-{W})/2+{sgn * 10}*{z}':y='(ih-{H})/2'" if n not in SKIP_CAM else f'scale={W}:{H}'
    if n == 23:   # logo sting: no texture
        fc = f'[0:v]{cam},format=yuv420p[o]'; ins = ['-i', src]
    elif world == 'paper':
        fc = (f"[0:v]{cam},format=gbrp[c];[1:v]scale=-2:{H},crop={W}:{H},split=3[tm][tb][tx];"
              f"[tm]format=gray,gblur=sigma=25[bl];[tb]format=gray[g];[g][bl]blend=all_expr='128+(A-B)*0.10',format=gbrp,split[mx][my];"
              f"[c]format=gbrp[c2];[c2][mx][my]displace=edge=smear,format=gbrp[d];"
              f"[tx]format=gbrp,curves=all='0/0.55 0.5/0.86 0.8/1 1/1'[t];"
              f"[d][t]blend=all_mode=multiply,noise=alls=5:allf=t,format=yuv420p[o]")
        ins = ['-i', src, '-loop', '1', '-i', PAPER]
    else:
        fc = (f"[0:v]{cam},format=gbrp[c];[1:v]scale=-2:{H},crop={W}:{H},split=3[tm][tb][tx];"
              f"[tm]format=gray,gblur=sigma=25[bl];[tb]format=gray[g];[g][bl]blend=all_expr='128+(A-B)*0.03',format=gbrp,split[mx][my];"
              f"[c][mx][my]displace=edge=smear,format=gbrp[d];"
              f"[tx]format=gbrp,curves=all='0/0 0.55/0.03 0.8/0.18 1/0.4'[g2];"
              f"[d][g2]blend=all_mode=screen[s1];")
        ins = ['-i', src, '-loop', '1', '-i', GRUNGE]
        if DUST:
            fc += f"[2:v]scale=-2:{H},crop={W}:{H},format=gbrp,curves=all='0/0 0.5/0.35 1/0.95'[du];[s1][du]blend=all_mode=screen,noise=alls=5:allf=t,format=yuv420p[o]"
            ins += ['-stream_loop', '-1', '-i', DUST]
        else: fc += '[s1]noise=alls=5:allf=t,format=yuv420p[o]'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-map', '[o]', '-t', f'{d:.3f}', '-r', '30', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out], capture_output=True, text=True)
    print(n, world, 'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-400:], flush=True)


if __name__ == '__main__':
    src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(dst, exist_ok=True)
    only = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
    for f in sorted(glob.glob(f'{src}/[0-9][0-9].mp4')):
        n = int(os.path.basename(f)[:2])
        if only and os.path.basename(f)[:2] not in only: continue
        run(n, f, f'{dst}/{n:02d}.mp4')
