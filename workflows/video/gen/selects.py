"""'Selects' video for sign-off: the exact library shots a plan picked, untouched (their cached previews), trimmed to
each beat's length, in order, with "<n>. <shot> | <beat text>" burned small at the bottom. No build, no spend.
usage: python3 -m gen.selects <plan.json> [out.mp4]      (default: selects.mp4 next to the plan; prints the shot table)"""
import json, os, shutil, subprocess, sys, tempfile
from . import library as LIB
W, H, FPS = 540, 960, 30


def label(i, s):
    return f"{i + 1}. {s['template']}  |  {s.get('text') or '-'}".replace('\n', ' ')


def segment(i, s, e, tmp):
    sec = float(s['seconds']); o = os.path.join(tmp, f'{i:03d}.mp4'); tf = os.path.join(tmp, f'{i:03d}.txt')
    open(tf, 'w').write(label(i, s) if e and LIB.has_preview(e) else label(i, s) + '\n(no preview yet)')
    text = (f"drawtext=textfile={tf}:font=Sans:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8:"
            f"x=(w-tw)/2:y=h-th-28")
    if e and LIB.has_preview(e):
        src = ['-i', e['preview'] + '.mp4']
        vf = (f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,'
              f'tpad=stop_mode=clone:stop_duration={sec},{text}')   # shorter than the beat: hold its last frame
    else:
        src = ['-f', 'lavfi', '-i', f'color=c=0x202020:s={W}x{H}:r={FPS}:d={sec}']; vf = text
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *src, '-t', f'{sec}', '-vf', vf, '-an', '-r', str(FPS),
                    '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', o], check=True)
    return o


def main(plan_path, out=None):
    P = json.load(open(plan_path)); S = LIB.shots()
    if 'shots' not in P:   # group plan: the group's exact scenes in original order, each over its FULL length (no trimming)
        P['shots'] = [dict(template=x['scene'], text=x.get('text', ''), seconds=x['seconds']) for x in P['scenes']]
    out = out or os.path.join(os.path.dirname(os.path.abspath(plan_path)), 'selects.mp4')
    tmp = tempfile.mkdtemp(); segs = []
    print('| # | shot | beat text | seconds |\n|---|---|---|---|')
    for i, s in enumerate(P['shots']):
        e = S.get(s['template']); segs.append(segment(i, s, e, tmp))
        print(f"| {i + 1} | {s['template']}{'' if e and LIB.has_preview(e) else ' (no preview)'} | {s.get('text', '')} | {s['seconds']} |")
    open(os.path.join(tmp, 'list.txt'), 'w').write(''.join(f"file '{p}'\n" for p in segs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(tmp, 'list.txt'), '-c', 'copy',
                    '-movflags', '+faststart', out], check=True)
    shutil.rmtree(tmp); print('selects ->', out)
    return out


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
