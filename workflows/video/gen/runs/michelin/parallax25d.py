"""2.5D shots (lesson from reel DQu3nYiCepd): flat cut-out planes at different depths + ONE moving camera.
- every plane is scale-compensated: at the camera's start position it has exactly its authored size (the flat design is intact)
- dolly (Z push-in), truck (X) and a little tilt (Y) make near planes move/scale faster than far ones = parallax; near planes leave the frame
- depth of field: blur radius grows with |1/(z-camz) - 1/(zfocus-camz)| (foreground and far plane soft, hero plane sharp)
usage: python3 parallax25d.py <scene: map|stay> <out.mp4> [seconds] [--full]   (540x960 unless --full)"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
VID = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')); A = os.path.join(VID, 'library', 'assets')
FONT_SERIF = '/home/user/tpl/fonts/kokila.ttf'; FONT_SANS = '/home/user/tpl/fonts/coolvetica_rg.ttf'
W, H, FPS, F = 1080, 1920, 30, 1000.0


def ease(t): return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def load(n, w):
    im = Image.open(os.path.join(A, n)).convert('RGBA'); return im.resize((int(w), int(im.height * w / im.width)), Image.LANCZOS)
def text(s, size, color, font=FONT_SERIF):
    f = ImageFont.truetype(font, size); b = f.getbbox(s); im = Image.new('RGBA', (b[2] + 40, b[3] + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 10), s, font=f, fill=color); return im
def gradient(c0, c1, w=int(W * 2.2), h=int(H * 2.2)):   # oversize: the camera trucks, the backdrop must never run out
    t = np.linspace(0, 1, h)[:, None, None]; a = np.array(c0, float)[None, None, :]; b = np.array(c1, float)[None, None, :]
    return Image.fromarray(np.broadcast_to(a * (1 - t) + b * t, (h, w, 3)).astype('uint8')).convert('RGBA')


class Plane:
    def __init__(s, img, z, x=0, y=0, rot=0, name=''): s.img, s.z, s.x, s.y, s.rot, s.name = img, z, x, y, rot, name


def render(planes, cam, secs, zfocus, out, scale_out):
    n = int(secs * FPS); cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                '-vf', f'scale={scale_out}:flags=lanczos', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); cz0 = cam(0)[2]
    for i in range(n):
        cx, cy, cz = cam(i / max(1, n - 1)); frame = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        for pl in sorted(planes, key=lambda q: -q.z):
            if pl.z - cz < 60: continue   # behind / through the camera: gone
            k = (pl.z - cz0) / (pl.z - cz)                       # perspective scale, 1.0 at the start = scale compensation
            sw, sh = pl.img.width * k, pl.img.height * k
            if sw > 5200 or sh > 5200 or sw < 4: continue
            im = pl.img.resize((max(1, int(sw)), max(1, int(sh))), Image.LANCZOS)
            blur = 55 * abs(1 / (pl.z - cz) - 1 / (zfocus - cz)) * F / 4
            if pl.rot: im = im.rotate(pl.rot, expand=True, resample=Image.BICUBIC)
            if blur > .8: im = im.convert('RGBa').filter(ImageFilter.GaussianBlur(min(blur, 40))).convert('RGBA')
            dcx, dcy = cx - cam(0)[0], cy - cam(0)[1]          # truck / tilt in world px; the shift on screen is F/(z-camz): far planes barely move
            px = W / 2 + pl.x * k - dcx * F / (pl.z - cz) - im.width / 2
            py = H / 2 + pl.y * k - dcy * F / (pl.z - cz) - im.height / 2
            frame.alpha_composite(im, (int(px), int(py))) if -im.width < px < W and -im.height < py < H else None
        p.stdin.write(frame.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


def scene_map(secs):
    bg = gradient((120, 14, 10), (32, 4, 3))
    planes = [Plane(bg, 12000, name='bg'),
              Plane(text('A MAP.', 330, (243, 232, 214, 255)), 2200, 0, -520, name='title'),
              Plane(load('m_ledger.png', 700), 1700, 0, 120, rot=-6, name='ledger'),
              Plane(load('m_map.png', 980), 1200, 0, 160, rot=3, name='map'),
              Plane(load('m_book.png', 330), 900, -330, 620, rot=-8, name='book'),
              Plane(load('m_tyre.png', 520), 420, 360, 700, rot=10, name='tyre')]
    cam = lambda t: (300 * ease(t), -70 * ease(t), 520 * ease(t) ** 0.9)
    return planes, cam, 1200


def scene_stay(secs):
    bg = gradient((236, 228, 212), (206, 192, 170))
    planes = [Plane(bg, 12000, name='bg'),
              Plane(text('EAT', 210, (150, 20, 15, 255), FONT_SANS), 2300, 880, -380, name='t_eat'), Plane(load('m_cloche.png', 560), 2300, 880, 60, name='cloche'),
              Plane(text('SLEEP', 210, (30, 30, 30, 255), FONT_SANS), 1500, 140, -380, name='t_sleep'), Plane(load('m_bed.png' if os.path.exists(os.path.join(A, 'm_bed.png')) else 'bed.png', 640), 1500, 140, 60, name='bed'),
              Plane(text('FUEL', 210, (150, 20, 15, 255), FONT_SANS), 1000, -380, -300, name='t_fuel'), Plane(load('m_pump.png', 300), 1000, -380, 120, name='pump')]
    cam = lambda t: (2024 * ease(t), 0 * ease(t), 520 * ease(t))
    return planes, cam, 1500


SCENES = {'map': scene_map, 'stay': scene_stay}
if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; full = '--full' in sys.argv
    secs = float(a[2]) if len(a) > 2 else 3.0; planes, cam, zf = SCENES[a[0]](secs)
    render(planes, cam, secs, zf, a[1], '1080:1920' if full else '540:960'); print('wrote', a[1])
