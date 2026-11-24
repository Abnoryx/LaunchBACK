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
            'dip_black': dict(frames=8), 'invert': dict(frames=2), 'blur': dict(frames=6), 'rgb_split': dict(frames=3, shift=18),
            # the five/six moves taught in reel DVR92iPjRIw (user's transitions reference, 2026-11-24)
            'swipe': dict(frames=12, skew=0.3), 'mask_zoom': dict(frames=16), 'shape_reveal': dict(frames=16), 'match_cut': dict(frames=15, posterize=True), 'diff_glitch': dict(frames=8)}
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


EIO = 'if(lt(Q,0.5),4*pow(Q,3),1-pow(2-2*Q,3)/2)'.replace('Q', Q)   # ease-in-out cubic (peak speed mid-move)
CLIP = lambda v, lo, hi: f'min(max({v},{lo}),{hi})'


def swipe(p):
    """Foreground object swipe (reel DVR92 'swipe/occlusion'): a dark slanted band crosses right->left; at full cover the shot changes."""
    sk = p['skew']; wt = f'(W+{sk}*H)'; xs = f'(X+{sk}*Y)'; lft = f'({wt}*(1-2*{EIO}))'; sp = f'(W*0.03*(1-abs(2*{Q}-1)))'; occ = 'if(eq(PLANE,0),18,128)'; ts = []
    for k in TAPS:
        l = f'({lft}+({k})*{sp}/4)'
        ts.append(f'if(lt({xs},{l}),A,if(gt({xs},{l}+{wt}),B,{occ}))')
    return '(' + '+'.join(ts) + ')/9'


def mask_zoom(p):
    """Negative-space zoom (reel DVR92): the outgoing shot punches in, the incoming shot grows through a round hole (20% -> 100%)."""
    e = EIO; rmin = '(W*0.03)'; rmax = '(H*0.6)'; r = f'({rmin}*pow({rmax}/{rmin},{e}))'; sa = f'(1+4*{e}*{e})'; sb = f'(0.25+0.75*{e})'
    d = 'hypot(X-W/2,Y-H/2)'; m = CLIP(f'(({r}-{d})/2+0.5)', 0, 1)
    a = smp('a', f'(W/2+(X-W/2)/{sa})', f'(H/2+(Y-H/2)/{sa})'); b = smp('b', f'(W/2+(X-W/2)/{sb})', f'(H/2+(Y-H/2)/{sb})')
    return f'({a})*(1-{m})+({b})*{m}'


def shape_reveal(p):
    """Geometric shape reveal (reel DVR92 'shape scale'): a triangle scales 0 -> 2500% from the centre as an alpha matte onto the next shot."""
    r = f'(W*0.02*pow(H*2.8/(W*0.02),{EIO}))'; dx = '(X-W/2)'; dy = '(Y-H/2)'
    f1 = f'(0.5*{r}-{dy})'; f2 = f'(0.866*{dx}+0.5*({dy}+{r}))'; f3 = f'(-0.866*{dx}+0.5*({dy}+{r}))'
    m = CLIP(f'(min(min({f1},{f2}),{f3})/1.5+0.5)', 0, 1)
    return f'A*(1-{m})+B*{m}'


def match_cut(p):
    """Momentum match cut (reel DVR92 / DaDhD 'cutting the curve'): outgoing accelerates in (1/3 of the frames), the cut lands at peak
    speed, the incoming decelerates out of the same scale (2/3) - 1:2 ratio, radial blur follows the speed."""
    n = p['frames']; qq = f'(floor({Q}*{n}/2.5)*2.5/{n})' if p.get('posterize') else Q   # Posterize Time 12 fps: hold every 2.5 frames (reel DaDhD)
    u1 = f'(3*{qq})'; u2 = f'(({qq}-1/3)*1.5)'; early = f'lt({qq},1/3)'
    sc = f'if({early},1+0.55*pow({u1},3),1+0.55*pow(1-{u2},3))'; g = f'if({early},0.05*{u1}*{u1},0.05*pow(1-{u2},2))'; ts = []
    for k in TAPS:
        s_k = f'(({sc})*(1+({k})*({g})*0.5))'; x = f'(W/2+(X-W/2)/{s_k})'; y = f'(H/2+(Y-H/2)/{s_k})'
        ts.append(f"if({early},{smp('a', x, y)},{smp('b', x, y)})")
    return '(' + '+'.join(ts) + ')/9'


def diff_glitch(p, fmt='yuv420p'):
    """Difference-blend strobe (reel DVR92 glitch): 3 inverted pulses (frames ~0-1, 3-4, 6-7) then the next shot. Use sparingly."""
    pulse = f'(lt({Q},0.12)+between({Q},0.3,0.4)+between({Q},0.6,0.75))'; hold = f'if(lt({Q},0.5),A,B)'
    inv = f'(255-({hold}))' if fmt == 'gbrp' else f'(if(eq(PLANE,0),255,256)-({hold}))'
    return f'if(gt({pulse},0),{inv},{hold})'


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
    if tag == 'swipe': return swipe(p)
    if tag == 'mask_zoom': return mask_zoom(p)
    if tag == 'shape_reveal': return shape_reveal(p)
    if tag == 'match_cut': return match_cut(p)
    if tag == 'diff_glitch': return diff_glitch(p, fmt)
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
