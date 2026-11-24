"""Stitch v2: hold each shot long enough to read, burn the script line under it, real transitions (xfade whips, white flash on
the invert-flash shots), a synthesised whoosh on every cut. usage: stitch2.py <dir with NN.mp4> <out.mp4>"""
import glob, json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
d, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CAP = ["A tyre company has more", "power over chefs", "than any food critic alive.", "And it started as a free giveaway.", "1900. Michelin sold tyres.",
       "The problem:", "almost nobody in France owned a car.", "A tyre business needs movement.", "They didn't have an ad budget.", "They had a map.",
       "So they gave a guide away. Free.", "Where to fill up. Where to sleep. Where to eat.", "A small red book that said: yes, this road goes somewhere.",
       "The map wasn't the crazy part. The eating was.", "One anonymous meal. One rating. No appeal.", "Chefs now spend their whole lives chasing a mark",
       "a tyre company invented.", "They sold tyres.", "First they gave people somewhere to go.", "Every business you love has", "a guidebook like this.",
       "We're finding them one at a time.", ""]
FLASH = {11, 13, 15}; TD = 0.25
CYC = ['slideleft', 'slideup', 'wipeleft', 'slideright', 'smoothleft', 'slidedown']
fs = sorted(glob.glob(f'{d}/[0-9][0-9].mp4')); n = len(fs); assert n == len(CAP)
dur = lambda f: float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)
nat = [dur(f) for f in fs]
tgt = [nat[i] if not CAP[i] else max(nat[i], 0.32 * len(CAP[i].split()) + 0.7, 1.8) for i in range(n)]
tmp = os.path.join(d, 'cap'); os.makedirs(tmp, exist_ok=True)
font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 38)
for i, t in enumerate(CAP):
    im = Image.new('RGBA', (540, 960), (0, 0, 0, 0))
    if t:
        dr = ImageDraw.Draw(im); words, lines, cur = t.split(), [], ''
        for w in words:
            if dr.textlength((cur + ' ' + w).strip(), font=font) > 470 and cur: lines.append(cur); cur = w
            else: cur = (cur + ' ' + w).strip()
        lines.append(cur); y = 800 - 24 * len(lines)
        for l in lines:
            dr.text((270, y), l, font=font, fill='white', anchor='mm', stroke_width=5, stroke_fill='black'); y += 48
    im.save(f'{tmp}/{i + 1:02d}.png')
cmd = ['ffmpeg', '-v', 'error', '-y']
for i, f in enumerate(fs): cmd += ['-i', f]
for i in range(n): cmd += ['-loop', '1', '-framerate', '30', '-t', f'{tgt[i]:.3f}', '-i', f'{tmp}/{i + 1:02d}.png']
fc = []
for i in range(n):
    fc.append(f'[{i}:v]tpad=stop_mode=clone:stop_duration={max(0, tgt[i] - nat[i]):.3f},fps=30,scale=540:960,setsar=1,format=yuv420p[a{i}];'
              f'[a{i}][{n + i}:v]overlay=0:0:shortest=1,format=yuv420p[v{i}]')
cur, L, cuts = 'v0', tgt[0], []
for i in range(1, n):
    tr = 'fadewhite' if (i + 1) in FLASH else CYC[(i - 1) % len(CYC)]
    fc.append(f'[{cur}][v{i}]xfade=transition={tr}:duration={TD}:offset={L - TD:.3f}[x{i}]'); cuts.append(L - TD); cur = f'x{i}'; L += tgt[i] - TD
fc_s = ';'.join(fc)
# whoosh track
sr = 44100; rng = np.random.default_rng(7); aud = np.zeros(int((L + 1) * sr), dtype=np.float32)
wl = int(0.42 * sr); t = np.linspace(0, 1, wl); env = np.sin(np.pi * t) ** 2 * np.exp(-1.2 * t)
noise = rng.standard_normal(wl).astype(np.float32); hp = np.diff(noise, prepend=0)
sweep = np.convolve(hp * env, np.ones(6) / 6, mode='same') * 0.35
for c in cuts:
    s = int(max(0, c + TD / 2 - 0.12) * sr); aud[s:s + wl] += sweep[:len(aud) - s]
aud = np.clip(aud, -1, 1); wp = f'{d}/whoosh.wav'
with wave.open(wp, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((aud * 32767).astype('<i2').tobytes())
cmd += ['-i', wp, '-filter_complex', fc_s, '-map', f'[{cur}]', '-map', f'{2 * n}:a', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:v', 'libx264', '-crf', '17',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out]
subprocess.run(cmd, check=True); print(f'{n} shots, {L:.1f}s, {len(cuts)} transitions ->', out)
