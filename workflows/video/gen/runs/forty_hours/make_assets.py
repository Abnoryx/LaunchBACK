"""Flat stand-in props for forty_hours (ours, generated in code; no third-party marks). Prop A = 'the clean 8 seconds' card."""
from PIL import Image, ImageDraw, ImageFont
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'library', 'assets')
FONT = '/home/user/tpl/fonts/coolvetica_rg.ttf'
W, H = 540, 960
card = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
d.rounded_rectangle([0, 0, W - 1, H - 1], 44, fill=(240, 238, 232, 255))
f = lambda s: ImageFont.truetype(FONT, s)
d.text((W // 2, 300), '00:08', font=f(150), fill=(20, 20, 20, 255), anchor='mm')
d.rounded_rectangle([60, 430, W - 60, 446], 8, fill=(200, 196, 188, 255))
d.rounded_rectangle([60, 430, 60 + int((W - 120) * 0.97), 446], 8, fill=(225, 6, 0, 255))
d.text((W // 2, 520), 'the clean part', font=f(54), fill=(80, 78, 72, 255), anchor='mm')
mk = Image.open(os.path.join(A, 'launchback_mark.png')).convert('RGBA'); mk.thumbnail((190, 190))
card.alpha_composite(mk, ((W - mk.size[0]) // 2, 640))
d.text((W // 2, 880), 'launch.back', font=f(46), fill=(20, 20, 20, 255), anchor='mm')
card.save(os.path.join(A, 'fh_reel_card.png')); print('ok')

# background 'documents' (replace the third-party census doc / chart): a version-file list and a flat waveform with a red playhead
import random
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
doc = Image.new('RGB', (1128, 893), 'white'); d = ImageDraw.Draw(doc)
F2 = lambda p, s: ImageFont.truetype(p, s)
d.text((40, 40), 'Project versions: launch.back', font=F2(FB, 58), fill='black')
d.text((40, 125), 'Every export, in order. Only the last one ships.', font=F2(FR, 30), fill=(70, 70, 70))
d.text((40, 200), 'Files', font=F2(FB, 44), fill='black')
for i, n in enumerate(['reel_v1.mov', 'reel_v2.mov', 'reel_v3_fixaudio.mov', 'reel_v4_DELETED.mov', 'reel_v7.mov', 'reel_v9_FINAL_final.mov']):
    d.text((70, 275 + i * 52), '•  ' + n, font=F2(FR, 34), fill='black')
d.text((40, 620), 'Layers', font=F2(FB, 44), fill='black')
for i, n in enumerate(['layer_01 ... layer_40', 'audio_vo.wav (moved 0.5 s)']):
    d.text((70, 695 + i * 52), '•  ' + n, font=F2(FR, 34), fill='black')
doc.save(os.path.join(A, 'fh_versions_doc.png'))
random.seed(8)
ch = Image.new('RGB', (932, 600), 'white'); d = ImageDraw.Draw(ch)
d.text((30, 24), 'audio_vo.wav', font=F2(FB, 40), fill='black')
for i in range(60):
    h = int(40 + 220 * abs(random.gauss(0, 0.45))) if i % 7 else 40; x = 30 + i * 14.5
    d.rounded_rectangle([x, 330 - min(h, 250), x + 8, 330 + min(h, 250)], 4, fill='black')
d.rectangle([420, 90, 426, 570], fill=(225, 6, 0))
d.text((30, 540), '00:00:08', font=F2(FR, 30), fill=(70, 70, 70))
ch.save(os.path.join(A, 'fh_wave_chart.png')); print('docs ok')

# scan strip for statement_flip: same card without text (words stay readable)
sc = Image.open(os.path.join(A, 'mri_a.png')).size
cl = Image.new('RGB', sc, (240, 238, 232)); d = ImageDraw.Draw(cl)
m2 = Image.open(os.path.join(A, 'launchback_mark.png')).convert('RGBA'); m2.thumbnail((int(sc[0] * 0.5), int(sc[1] * 0.5)))
cl.paste(m2, ((sc[0] - m2.size[0]) // 2, (sc[1] - m2.size[1]) // 2), m2)
cl.save(os.path.join(A, 'fh_scan_card.png')); print('scan ok', sc)
