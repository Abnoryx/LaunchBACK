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


def cutout(src, name, trim=True, solid=False, tol=0.06):
    """Cut a studio shot out of its flat background, trimmed.
    solid=False: colour unmixing (keeps soft shadows semi-transparent; right for dark objects + contact shadows).
    solid=True: flood-fill matte - background = near-bg pixels connected to the border, everything else opaque
    (right for light objects on white, which unmixing would make see-through)."""
    import numpy as np
    from scipy import ndimage
    im = np.asarray(Image.open(src).convert('RGB')).astype(np.float64) / 255
    bg = np.median(np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3)]), 0)
    if solid:
        near = np.abs(im - bg).max(2) < tol
        lab, _ = ndimage.label(near)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        bgm = np.isin(lab, list(border))
        a = ndimage.gaussian_filter((~bgm).astype(float), 0.8)
        col = im
    else:
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


def calendar_card(num, name=None, brand='Casper', para=None, fonts_dir='/home/user/tpl/fonts/helv'):
    """Calendar page (reel S5): 'Day' + mattress line icon + black tabs, huge bold-oblique number (horizontally
    condensed), navy wordmark under its right side, thick rule, 6-line condensed serif paragraph. 827x956 off-white
    card. Layout measured on reel f485/f530 (card-local px)."""
    W, H = 827, 956
    im = Image.new('RGB', (W, H), (0xF5, 0xF5, 0xF2)); d = ImageDraw.Draw(im)
    bold = os.path.join(fonts_dir, 'Helvetica-Bold.ttf'); obl = os.path.join(fonts_dir, 'Helvetica-BoldOblique.ttf')
    if not os.path.exists(bold): bold = obl = BOLD
    ink = (21, 21, 21)
    d.text((77, 142), 'Day', fill=ink, font=ImageFont.truetype(bold, 104))
    teal = (0x5A, 0xA8, 0xB0)  # mattress line icon: top face, slab, slatted base
    d.polygon([(305, 212), (345, 148), (455, 148), (492, 212)], outline=teal, width=4)
    d.polygon([(318, 205), (352, 156), (448, 156), (480, 205)], outline=teal, width=2)
    d.rectangle((300, 212, 495, 236), outline=teal, width=4)
    d.rectangle((310, 236, 485, 262), outline=teal, width=3)
    for x in range(322, 485, 13): d.line((x, 238, x, 260), fill=teal, width=2)
    d.rectangle((630, 38, 800, 80), fill=(10, 10, 10)); d.rectangle((615, 85, 790, 94), fill=(10, 10, 10))
    # number: drawn big then condensed to 92 % width; 3-digit numbers a size smaller and further left
    n = str(num); three = len(n) >= 3
    size = 434 if three else 518
    f = ImageFont.truetype(obl, size); bb = f.getbbox(n)
    lay = Image.new('L', (bb[2] + 40, bb[3] + 20), 0); ImageDraw.Draw(lay).text((20, 0), n, fill=255, font=f)
    lay = lay.resize((int(lay.width * 0.92), lay.height), Image.LANCZOS)
    x0, top = (79, 279) if three else (137 if len(n) == 2 else 190, 292)
    im.paste(Image.new('RGB', lay.size, ink), (x0 - int(20 * 0.92), top - bb[1]), lay)
    d.text((568, 667), brand, fill=(0x18, 0x32, 0x4D), font=ImageFont.truetype(bold, 69))
    d.rectangle((36, 736, 655, 750), fill=(10, 10, 10))
    lines = para or ["Casper gives you 100 nights to sleep on their", "mattress because it's a risk-free,",
                     "confidence-building strategy that allows your", "body enough time to properly adjust and",
                     "ensures you're truly happy with such an", "important purchase."]
    pf = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf', 30)
    for i, ln in enumerate(lines):
        w = int(pf.getlength(ln)) + 4
        lay = Image.new('L', (w, 36), 0); ImageDraw.Draw(lay).text((0, 0), ln, fill=255, font=pf)
        lay = lay.resize((int(w * 0.88), 36), Image.LANCZOS)
        im.paste(Image.new('RGB', lay.size, (25, 25, 25)), (36, 770 + i * 22), lay)
    im.save(os.path.join(OUT, name or f'calendar_{num}.png'))

HAND = os.path.join(os.path.dirname(__file__), '..', 'node_modules/@fontsource/patrick-hand/files/patrick-hand-latin-400-normal.woff')


def math_graph(name='math_graph.png', unit=120, half=10):
    """Big maths graph sheet (reel S8a): thin grey 1-unit grid, black axis cross with ticks, +-10 end labels.
    Transparent background so cards behind show through between the lines."""
    N = int(2 * half * unit + 2 * unit)
    im = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c0 = N // 2
    for k in range(-half - 1, half + 2):
        x = c0 + k * unit
        d.line((x, 0, x, N), fill=(0x77, 0x7D, 0x7D, 255), width=3); d.line((0, x, N, x), fill=(0x77, 0x7D, 0x7D, 255), width=3)
    d.line((c0, 0, c0, N), fill=(20, 20, 20, 255), width=6); d.line((0, c0, N, c0), fill=(20, 20, 20, 255), width=6)
    for k in range(-half, half + 1):
        d.line((c0 + k * unit, c0 - 16, c0 + k * unit, c0 + 16), fill=(20, 20, 20, 255), width=5)
        d.line((c0 - 16, c0 + k * unit, c0 + 16, c0 + k * unit), fill=(20, 20, 20, 255), width=5)
    f = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 52)
    d.text((c0 - half * unit - 10, c0 + 24), '-10', fill=(20, 20, 20, 255), font=f)
    d.text((c0 + 22, c0 - half * unit - 30), '10', fill=(20, 20, 20, 255), font=f)
    im.save(os.path.join(OUT, name))


def ruler(name='ruler.png', W=1280, H=640):
    """Transparent ruler strip (reel S8a): fine black ticks, half and whole marks, numerals 0..10."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, x1, y = 40, W - 40, 250; step = (x1 - x0) / 100
    f = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 46)
    for i in range(101):
        x = x0 + i * step; h = 110 if i % 10 == 0 else 70 if i % 5 == 0 else 45
        d.line((x, y, x, y + h), fill=(15, 15, 15, 255), width=3)
        if i % 10 == 0: d.text((x - 12, y + 125), str(i // 10), fill=(15, 15, 15, 255), font=f)
    d.line((x0, y, x1, y), fill=(15, 15, 15, 255), width=3)
    im.save(os.path.join(OUT, name))


def formula_board(name='formula_board.png', W=1200, H=840):
    """Light-grey sheet of hand-drawn maths (reel S8a): trig formulas, triangles, a hatched bar chart, a parabola."""
    im = Image.new('RGB', (W, H), (0xE4, 0xE5, 0xE5)); d = ImageDraw.Draw(im)
    ink = (25, 25, 25); f = ImageFont.truetype(HAND, 54); s = ImageFont.truetype(HAND, 40)
    for (x, y), t, ft in (((40, 40), 'sin x = 2 sin x cos x', f), ((40, 120), 'y = 2x² - 3x + 1', f), ((640, 40), 'V = 1/3 Bh', f),
                          ((640, 120), 'A = ½ ab', f), ((40, 690), 'S = 6a²', f), ((360, 690), 'S = 4R²', f),
                          ((800, 300), 'cos x', s), ((640, 200), 'x² + y² = r²', s), ((960, 610), '(x)', s)):
        d.text((x, y), t, fill=ink, font=ft)
    d.line((60, 470, 60, 620, 240, 620, 60, 470), fill=ink, width=5); d.text((20, 520), 'a', fill=ink, font=s); d.text((130, 625), 'b', fill=ink, font=s)
    d.line((300, 300, 450, 220, 520, 360, 300, 300), fill=ink, width=5); d.text((380, 330), 'c', fill=ink, font=s)
    for i, h in enumerate((90, 160, 120, 210)):
        x = 600 + i * 70
        d.rectangle((x, 620 - h, x + 50, 620), outline=ink, width=4)
        for k in range(620 - h, 620, 14): d.line((x, k, x + 50, k - 14 if k - 14 > 620 - h else 620 - h), fill=ink, width=2)
    d.line((580, 620, 900, 620), fill=ink, width=4)
    pts = [(900 + t * 7, 600 - (t - 20) ** 2 * 0.8 + 340) for t in range(0, 41)]
    d.line([(x, max(260, y)) for x, y in pts], fill=ink, width=5)
    d.line((60, 230, 260, 230, 160, 380, 60, 230), fill=ink, width=4)
    im.save(os.path.join(OUT, name))


def brain_quad(name='brain_quad.png', src='brain_side.png', S=1024):
    """Four small dark brain renders in a 2x2 grid on transparent (reel S8a 'brain 4.png'), from our side-view brain."""
    import numpy as np
    b = Image.open(os.path.join(OUT, src)).convert('RGBA')
    a = np.asarray(b).astype(float)
    g = a[..., :3].mean(2, keepdims=True)
    dark = np.clip((g - 40) * 0.42 + 20, 0, 255) * np.array([0.92, 1.0, 1.0])  # slate, pale ridges
    b = Image.fromarray(np.dstack([dark, a[..., 3:]]).astype(np.uint8), 'RGBA')
    cell = S // 2; w = int(cell * 0.86); b = b.resize((w, int(w * b.height / b.width)), Image.LANCZOS)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    for i in range(4):
        im.alpha_composite(b, ((i % 2) * cell + (cell - b.width) // 2, (i // 2) * cell + (cell - b.height) // 2))
    im.save(os.path.join(OUT, name))


def e_mark(name='e_mark.png', color=(0x3E, 0xA0, 0x55), W=640, H=440):
    """Round single-stroke lowercase 'e' with a dot after it (reel S9 logo shape), drawn 4x then downsampled."""
    k = 4; im = Image.new('RGBA', (W * k, H * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy, r, w = 230 * k, 230 * k, 190 * k, 44 * k
    d.arc((cx - r, cy - r, cx + r, cy + r), 45, 360, fill=color + (255,), width=w)  # open at the lower right
    d.line((cx - r + w // 2, cy + 10 * k, cx + r - w // 2, cy + 10 * k), fill=color + (255,), width=w)
    d.ellipse((520 * k, 330 * k, 590 * k, 400 * k), fill=color + (255,))
    im.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, name))

if __name__ == '__main__':
    film_edge()
    film_edge_dark()
    viewfinder()
    chart_doc()
    census_doc()
    for n in (1, 10, 30, 50, 100):
        calendar_card(n)
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
