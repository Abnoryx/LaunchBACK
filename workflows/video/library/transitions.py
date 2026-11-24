"""Transitions as separate assets. Each transition type is saved as `library/transitions/<id>.json` (spec: type, params, where it was
measured) plus `library/transitions/<id>.mp4` (preview on two neutral cards, A = paper, B = dark: once at real speed, then 4x slow, so
the user can judge the move itself, never the reel's pixels). Previews are rendered with ffmpeg xfade expressions (no GPU, a few seconds).
usage (code): export(id, tag, params, meta) ; (CLI) python3 -m extract.transitions_export <run name>
Recipes (tag -> default params): hard_cut, whip{dir}, zoom_punch, flash_white, dip_black, invert, blur, rgb_split."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'transitions')
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
W, H = 540, 960
DEFAULTS = {'hard_cut': dict(frames=1), 'whip': dict(frames=4, dir='left', blur=0.018), 'zoom_punch': dict(frames=4), 'flash_white': dict(frames=3),
            'dip_black': dict(frames=8), 'invert': dict(frames=2), 'blur': dict(frames=6), 'rgb_split': dict(frames=3, shift=18)}
FMT = {'invert': 'gbrp', 'rgb_split': 'gbrp'}   # everything else is judged in yuv420p
Q = '(1-P)'                                       # ffmpeg's xfade P runs 1 -> 0; Q = 0 -> 1
E = f'(1-pow(1-{Q},3))'                           # ease-out cubic: fast in, decelerating hold
TAPS = tuple(range(-4, 5))


def smp(f, x, y):
    x = f'min(max({x},0),W-1)'; y = f'min(max({y},0),H-1)'
    return f'if(eq(PLANE,0),{f}0({x},{y}),if(eq(PLANE,1),{f}1({x},{y}),{f}2({x},{y})))'


def push(d, blur):
    ax, n = ('X', 'W') if d in ('left', 'right') else ('Y', 'H'); sgn = '+' if d in ('left', 'up') else '-'; bl = f'({n}*{blur}*sin(PI*{Q}))'; ts = []
    for k in TAPS:
        pos = f'({ax}{sgn}{E}*{n}+({k})*{bl})'; cond = f'lt({pos},{n})' if sgn == '+' else f'gte({pos},0)'; alt = f'({pos}-{n})' if sgn == '+' else f'({pos}+{n})'
        xa, ya = (pos, 'Y') if ax == 'X' else ('X', pos); xb, yb = (alt, 'Y') if ax == 'X' else ('X', alt)
        ts.append(f"if({cond},{smp('a', xa, ya)},{smp('b', xb, yb)})")
    return '(' + '+'.join(ts) + ')/9'


def zoom():
    u = f'if(lt({Q},0.5),2*{Q},2*(1-{Q}))'; sc = f'(1+2*pow({u},2))'; ts = []
    for k in TAPS:
        s_k = f'({sc}*(1+({k})*0.025*{u}))'; x = f'(W/2+(X-W/2)/{s_k})'; y = f'(H/2+(Y-H/2)/{s_k})'
        ts.append(f"if(lt({Q},0.5),{smp('a', x, y)},{smp('b', x, y)})")
    return '(' + '+'.join(ts) + ')/9'


def expr(tag, p, fmt):
    pk = f'(1-abs(2*{Q}-1))'                      # 0 at the ends, 1 at the middle
    hold = 'if(lt(%s,0.5),A,B)' % Q
    white = '255' if fmt == 'gbrp' else 'if(eq(PLANE,0),255,128)'; black = '0' if fmt == 'gbrp' else 'if(eq(PLANE,0),0,128)'
    if tag == 'hard_cut': return 'if(gt(P,0.5),A,B)'
    if tag == 'whip': return push(p['dir'], p['blur'])
    if tag == 'zoom_punch': return zoom()
    if tag == 'flash_white': return f'({hold})*(1-{pk})+{white}*{pk}'
    if tag == 'dip_black': return f'({hold})*(1-{pk})+{black}*{pk}'
    if tag == 'invert': return f'if(between({Q},0.34,0.66),255-({hold}),{hold})'
    if tag == 'blur':
        s = f'(W*0.02*sin(PI*{Q}))'; ts = []
        for k in TAPS:
            ts.append(f"if(lt({Q},0.5),{smp('a', f'X+({k})*{s}', 'Y')},{smp('b', f'X+({k})*{s}', 'Y')})")
            ts.append(f"if(lt({Q},0.5),{smp('a', 'X', f'Y+({k})*{s}')},{smp('b', 'X', f'Y+({k})*{s}')})")
        return '(' + '+'.join(ts) + ')/18'
    if tag == 'rgb_split':
        dx = f"(if(eq(PLANE,1),{p['shift']},if(eq(PLANE,2),-{p['shift']},0))*sin(PI*{Q}))"
        return f"if(lt({Q},0.5),{smp('a', f'X+{dx}', 'Y')},{smp('b', f'X+{dx}', 'Y')})"
    raise ValueError(tag)


def preview(tag, params, out, label=''):
    """Neutral A/B cards -> the transition -> mp4 (real speed, then 4x slow)."""
    p = {**DEFAULTS[tag], **(params or {})}; fmt = FMT.get(tag, 'yuv420p'); fr = int(p['frames']); td = fr / 30; hold = 0.5; dur = hold + td + 0.05
    def card(color, ink, ch):
        return (f'color=c={color}:s={W}x{H}:r=30:d={dur:.3f},drawtext=fontfile={FONT}:text={ch}:fontsize=560:fontcolor={ink}:x=(w-text_w)/2:y=(h-text_h)/2-60,'
                f'drawbox=x=40:y=120:w=460:h=6:color={ink}@0.6:t=fill,format={fmt}')
    ex = expr(tag, p, fmt)
    fc = (f"{card('0xEFEDE6', 'black', 'A')}[a];{card('0x101010', '0xE10600', 'B')}[b];"
          f"[a][b]xfade=transition=custom:expr='{ex}':duration={td:.4f}:offset={hold:.3f},format=yuv420p,fps=30,split[r][s];"
          f"[s]setpts=4*PTS[slow];[r][slow]concat=n=2:v=1[c];"
          f"[c]drawtext=fontfile={FONT}:text='{label or tag} / {fr} frames':fontsize=26:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8:x=20:y=h-70[o]")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    scr = out + '.filter.txt'; open(scr, 'w').write(fc)
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-filter_complex_script', scr, '-map', '[o]', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out], capture_output=True, text=True)
    os.remove(scr)
    if r.returncode: raise RuntimeError(r.stderr[-400:])
    return p


def export(tid, tag, params=None, meta=None, out_dir=OUT):
    """Save one transition as its own asset: <out_dir>/<id>.json + <id>.mp4 (id may contain '/': <reel>/<tag>)."""
    base = os.path.join(out_dir, tid); mp4 = base + '.mp4'; p = preview(tag, params, mp4, tid)
    spec = {'id': tid, 'tag': tag, 'params': p, 'preview': os.path.relpath(mp4, HERE), 'status': 'draft', **(meta or {})}
    json.dump(spec, open(base + '.json', 'w'), indent=1); return spec
