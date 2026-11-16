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


def viewfinder(name='viewfinder.png'):
    """Camera viewfinder surround (reel S6): black frame x 3-1077, y 155-1766 with a rounded window x 159-998, y 306-1588,
    cream exposure strip on the left (x 94-136, y 446-1526), aperture scale along the bottom (x 230-760, y 1602-1635)."""
    W, H = 1080, 1920
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 155, 1077, 1766), 14, fill=(6, 6, 6, 255))
    d.rounded_rectangle((159, 306, 998, 1588), 8, fill=(0, 0, 0, 0))
    d.rectangle((94, 446, 136, 1526), fill=(0xAF, 0xAB, 0x9E, 255))
    f = ImageFont.truetype(BOLD, 22)
    nums = '30 15 8 4 2 1 2 4 8 15 30 60 125 250 500 1000 B'.split()
    for i, t in enumerate(nums):
        y = 456 + i * (1060 / (len(nums) - 1))
        tw = f.getlength(t); d.text((115 - tw / 2, y - 11), t, fill=(10, 10, 10, 255), font=f)
    d.rectangle((230, 1602, 760, 1635), fill=(0xAF, 0xAB, 0x9E, 255))
    d.rectangle((230, 1602, 262, 1635), fill=(0x9B, 0x01, 0x05, 255)); d.rectangle((728, 1602, 760, 1635), fill=(0x9B, 0x01, 0x05, 255))
    ap = '1.2   2   2.8   4   5.6  |  8   11   16   22'
    d.text((280, 1606), ap, fill=(10, 10, 10, 255), font=ImageFont.truetype(BOLD, 20))
    im.save(os.path.join(OUT, name))


def chart_doc(name='chart_doc.png'):
    """White document with a black line chart (reel S7: rising revenue curve + flat earnings line, axis numerals),
    later tinted green and screened, so white disappears and ink glows."""
    import math
    W, H = 466 * 2, 300 * 2
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(BOLD, 22); fs = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 18)
    d.text((40, 20), 'Revenue and Net Earnings', fill='black', font=f)
    x0, y0, x1, y1 = 90, 80, W - 40, H - 70
    for i in range(6):
        y = y1 - (y1 - y0) * i / 5; d.line((x0, y, x1, y), fill=(200, 200, 200), width=1)
        d.text((20, y - 10), f'{i * 20}', fill='black', font=fs)
    for i, yr in enumerate(range(1996, 2005)):
        x = x0 + (x1 - x0) * i / 8; d.text((x - 20, y1 + 12), str(yr), fill='black', font=fs)
    pts = [(x0 + (x1 - x0) * t / 40, y1 - (y1 - y0) * (0.15 + 0.7 * (t / 40) ** 1.6 + 0.04 * math.sin(t * 0.9))) for t in range(41)]
    d.line(pts, fill='black', width=7)
    flat = [(x0 + (x1 - x0) * t / 40, y1 - (y1 - y0) * (0.12 + 0.02 * math.sin(t * 0.6))) for t in range(41)]
    d.line(flat, fill='black', width=4)
    d.line((x0, y0, x0, y1, x1, y1), fill='black', width=3)
    im.save(os.path.join(OUT, name))


def census_doc(name='census_doc.png'):
    """White web-page style document (reel S7): big title, 'Datasets' list, 'Record Layouts' section."""
    W, H = 1128, 893
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    tf = ImageFont.truetype(BOLD, 64); hf = ImageFont.truetype(BOLD, 40); bf = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 28)
    d.text((40, 40), 'County Business Patterns: 2004', fill='black', font=tf)
    d.text((40, 150), 'Data are released annually for the nation, states and counties.', fill=(60, 60, 60), font=bf)
    d.text((40, 230), 'Datasets', fill='black', font=hf)
    for i, t in enumerate(['U.S. totals by industry', 'State totals by industry', 'County totals by industry',
                           'Metropolitan areas', 'ZIP code business patterns', 'Employment size class detail']):
        d.text((70, 300 + i * 52), '•  ' + t, fill='black', font=bf)
    d.text((40, 640), 'Record Layouts', fill='black', font=hf)
    for i, t in enumerate(['Field names and descriptions', 'Industry codes (NAICS)', 'Geography codes']):
        d.text((70, 710 + i * 52), '•  ' + t, fill='black', font=bf)
    im.save(os.path.join(OUT, name))


def cutout(src, name, trim=True):
    """Cut a studio shot out of its flat background (colour unmixing, keeps soft shadows semi-transparent), trimmed."""
    import numpy as np
    im = np.asarray(Image.open(src).convert('RGB')).astype(np.float64) / 255
    bg = np.median(np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3)]), 0)
    a = np.max(np.maximum((bg - im) / np.maximum(bg, 1e-3), (im - bg) / np.maximum(1 - bg, 1e-3)), axis=2)
    a = np.clip((a - 0.04) / 0.96, 0, 1)
    col = np.clip((im - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 1e-3), 0, 1)
    out = Image.fromarray(np.dstack([col * 255, a * 255]).astype(np.uint8), 'RGBA')
    if trim:
        out = out.crop(out.getbbox())
    out.save(os.path.join(OUT, name))
    return out.size


def graph_paper(name='graph_paper.png', unit=63, half=5.6):
    """Graph paper (reel S1b): 1-unit grid, axis cross with ticks and +-5 labels, edges fading out."""
    import numpy as np
    N = int(2 * half * unit) + 40
    im = Image.new('L', (N, N), 255); d = ImageDraw.Draw(im); c0 = N // 2
    for k in range(-6, 7):
        x = c0 + k * unit
        d.line((x, 0, x, N), fill=170, width=2); d.line((0, x, N, x), fill=170, width=2)
    d.line((c0, 0, c0, N), fill=110, width=4); d.line((0, c0, N, c0), fill=110, width=4)
    for k in range(-5, 6):
        d.line((c0 + k * unit, c0 - 10, c0 + k * unit, c0 + 10), fill=90, width=3); d.line((c0 - 10, c0 + k * unit, c0 + 10, c0 + k * unit), fill=90, width=3)
    f = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 26)
    for t, (x, y) in (('-5', (c0 - 5 * unit - 26, c0 + 14)), ('5', (c0 + 5 * unit + 6, c0 + 14)), ('5', (c0 + 14, c0 - 5 * unit - 16)), ('-5', (c0 + 14, c0 + 5 * unit - 16))):
        d.text((x, y), t, fill=90, font=f)
    a = np.asarray(im).astype(float)
    yy, xx = np.mgrid[0:N, 0:N] / N
    edge = np.clip(np.minimum.reduce([xx, 1 - xx, yy, 1 - yy]) / 0.12, 0, 1)  # feathered edges
    ink = (255 - a) * edge
    Image.fromarray((255 - ink).astype(np.uint8)).convert('RGB').save(os.path.join(OUT, name))
    return N


if __name__ == '__main__':
    film_edge()
    film_edge_dark()
    viewfinder()
    chart_doc()
    census_doc()
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
