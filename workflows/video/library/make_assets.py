"""Our own assets for the from-scratch rebuild, drawn in code. Positions measured on the reel (@720, x1.5 for 1080)."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), 'assets')
os.makedirs(OUT, exist_ok=True)
BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def film_edge(ink=(52, 52, 52), name='film_edge.png'):
    """White sheet with film-edge markings, used as a MULTIPLY overlay. Left: 'KODAK  PORTRA 400' reading upward
    (x 69-80 @720, runs y 86-364 and 837-1114), frame numbers '43' / '12'; right: triangle marks (x 679-689)."""
    W, H = 1080, 1920
    im = Image.new('RGB', (W, H), 'white')
    f = ImageFont.truetype(BOLD, 26)
    def vtext(s, cx, y_top, y_bot, font=f):
        # render horizontally then rotate 90 deg CCW so it reads bottom -> top
        L = y_bot - y_top
        tw = sum(font.getlength(c) for c in s)
        gap = (L - tw) / max(1, len(s) - 1)
        strip = Image.new('L', (int(L) + 4, 30), 0)
        d = ImageDraw.Draw(strip); x = 2
        for c in s:
            d.text((x, 3), c, fill=255, font=font); x += font.getlength(c) + gap
        strip = strip.rotate(90, expand=True)
        im.paste(Image.new('RGB', strip.size, ink), (int(cx - strip.size[0] / 2), int(y_top)), strip)
    vtext('KODAK  PORTRA 400', 112, 129, 546)
    vtext('KODAK  PORTRA 400', 113, 1255, 1671)
    vtext('43', 112, 755, 800, ImageFont.truetype(BOLD, 24))
    vtext('12', 113, 1878, 1918, ImageFont.truetype(BOLD, 24))
    d = ImageDraw.Draw(im)
    for yc in (98, 726, 1373):  # triangles pointing up, ~15 x 26 px
        d.polygon([(1026, yc - 13), (1019, yc + 13), (1033, yc + 13)], fill=ink)
    two = Image.new('L', (40, 30), 0); ImageDraw.Draw(two).text((4, 2), '2', fill=255, font=ImageFont.truetype(BOLD, 22))
    two = two.rotate(90, expand=True); im.paste(Image.new('RGB', two.size, ink), (1012, 1300), two)
    im = im.filter(ImageFilter.GaussianBlur(1.2))  # the reel's marks are soft
    im.save(os.path.join(OUT, name))


def film_edge_dark(name='film_edge_dark.png', ink=(0x99, 0x83, 0x50)):
    """Dark-shot version: amber marks on black, used with SCREEN blend (reel S2: amber #998350 on black)."""
    film_edge(name='_fe_tmp.png')
    from PIL import ImageOps
    im = Image.open(os.path.join(OUT, '_fe_tmp.png')).convert('L')
    a = ImageOps.invert(im)  # ink strength
    col = Image.new('RGB', im.size, ink)
    out = Image.composite(col, Image.new('RGB', im.size, 'black'), a)
    out.save(os.path.join(OUT, name)); os.remove(os.path.join(OUT, '_fe_tmp.png'))


if __name__ == '__main__':
    film_edge()
    film_edge_dark()
    print('assets ->', OUT)


def car_cutout(src, name='car.png', body_target=(0x15, 0x64, 0x22)):
    """Cut a studio car shot out of its flat grey background, keeping the soft contact shadow as semi-transparent
    dark pixels (colour unmixing against the background), then shift its green to the reel's body colour."""
    import numpy as np
    im = np.asarray(Image.open(src).convert('RGB')).astype(np.float64) / 255
    bg = np.median(np.concatenate([im[:20].reshape(-1, 3), im[-20:].reshape(-1, 3)]), 0)
    a = np.max(np.maximum((bg - im) / np.maximum(bg, 1e-3), (im - bg) / np.maximum(1 - bg, 1e-3)), axis=2)
    a = np.clip((a - 0.03) / 0.97, 0, 1)
    col = np.clip((im - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 1e-3), 0, 1)
    # recolour the green paint: scale so the median body green maps to the target
    g = (col[..., 1] > col[..., 0] * 1.15) & (col[..., 1] > col[..., 2] * 1.1) & (a > 0.95)
    med = np.median(col[g], 0)
    tgt = np.array(body_target) / 255
    gain = tgt / np.maximum(med, 12 / 255)
    w = np.clip((col[..., 1] - np.maximum(col[..., 0], col[..., 2])) / 0.05, 0, 1)[..., None]  # only greenish pixels
    col = np.clip(col * (1 - w) + np.clip(col * gain, 0, 1) * w, 0, 1)
    out = np.dstack([col * 255, a * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, name))
    print('car body median', (med * 255).round(), '-> gain', gain.round(2))
