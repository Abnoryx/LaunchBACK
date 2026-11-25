"""New on-topic assets for the Michelin reel (replace the Generation Effect originals in the exact animated slots).
Inputs (Higgsfield stills, assets_gen/*.png) -> assets_gen/out/*: sticker cut-outs (grabCut), chef sticker (magenta key + white die-cut outline),
B-roll clips from stills (animated in ffmpeg, not generated video), a red 'book' bezel, UI cards (post, profile) with the handle launch.back,
red verified tick, desktop icons, notification badges. usage: python3 make_assets.py"""
import os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, 'assets_gen'); O = os.path.join(G, 'out'); os.makedirs(O, exist_ok=True)
TPL = '/home/user/tpl/lib/gen/assets'; HANDLE = 'launch.back'
BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'; REG = '/usr/share/fonts/opentype/inter/Inter-Regular.otf'
RED = (225, 6, 0); CREAM = (243, 237, 225)
F = lambda p, s: ImageFont.truetype(p, s)

def trim(im):
    bb = im.getchannel('A').getbbox(); return im.crop(bb) if bb else im

# 1) stickers: grabCut each cell of the 3x2 sheet
sheet = cv2.imread(os.path.join(G, 'sheet.png')); H, W = sheet.shape[:2]; names = ['tyre', 'toque', 'book', 'cutlery', 'pin', 'pump']
for i, n in enumerate(names):
    r, c = divmod(i, 3); x0, x1, y0, y1 = int(c * W / 3), int((c + 1) * W / 3), int(r * H / 2), int((r + 1) * H / 2)
    cell = sheet[y0:y1, x0:x1].copy(); h, w = cell.shape[:2]; m = np.zeros((h, w), np.uint8); rect = (int(w * .06), int(h * .06), int(w * .88), int(h * .88))
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65)); cv2.grabCut(cell, m, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    a = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8); a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); a = cv2.GaussianBlur(a, (0, 0), 1.2)
    rgba = np.dstack([cv2.cvtColor(cell, cv2.COLOR_BGR2RGB), a]); trim(Image.fromarray(rgba, 'RGBA')).save(os.path.join(O, f'sticker_{n}.png'))

# 2) chef sticker: key magenta, white die-cut outline
im = np.asarray(Image.open(os.path.join(G, 'chef_fig.png')).convert('RGB')).astype(float)
dist = np.sqrt((im[..., 0] - 255) ** 2 + im[..., 1] ** 2 + (im[..., 2] - 255) ** 2); a = np.clip((dist - 70) / 90, 0, 1)
a = cv2.erode(a, np.ones((3, 3), np.uint8)); chef = Image.fromarray(np.dstack([im, a * 255]).astype(np.uint8), 'RGBA')
chef = trim(chef); chef.thumbnail((900, 1600)); al = np.asarray(chef.getchannel('A'))
d = cv2.dilate(al, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))); out = Image.new('RGBA', chef.size, (0, 0, 0, 0))
out.paste(Image.new('RGBA', chef.size, (255, 255, 255, 255)), mask=Image.fromarray(d)); out.alpha_composite(chef); out.save(os.path.join(O, 'chef_sticker.png'))

# 3) B-roll clips from stills (camera moves, 1620x1080 landscape like the original slot / 720x1280 portrait)
def clip(src, out, w, h, secs, pan, period=None):   # period: the move repeats (the original clips are long and the scenes seek deep into them)
    ph = f"mod(t,{period})/{period}" if period else f"t/{secs}"
    fc = f"scale=w='trunc({w}*(1.0+0.16*{ph})/2)*2':h=-2:eval=frame,crop={w}:{h}:x='(iw-{w})/2':y='{pan.replace('PH', ph)}'"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-i', src, '-t', str(secs), '-vf', fc + ',format=yuv420p', '-c:v', 'libx264', '-crf', '17', '-an', out], check=True)
clip(os.path.join(G, 'wallpaper.png'), os.path.join(O, 'broll_road.mp4'), 1620, 1080, 150, "(ih-1080)*(1-PH)", period=16)           # tilt up from the road to the tower
clip(os.path.join(G, 'chef_broll.png'), os.path.join(O, 'broll_chef.mp4'), 720, 1280, 30, "(ih-1280)/2", period=15)                 # slow push-in on the chef

# 4) red leather 'book' bezel in place of the phone frame (same alpha: the screen stays transparent)
ph = Image.open(os.path.join(TPL, 'iphone.png')).convert('RGBA'); al = np.asarray(ph.getchannel('A')); h, w = al.shape
yy = np.linspace(0, 1, h)[:, None]; base = np.dstack([150 + 60 * yy * np.ones((h, w)), 8 + 10 * yy * np.ones((h, w)), 6 * np.ones((h, w))])
noise = np.random.default_rng(3).normal(0, 7, (h, w))[..., None]; leather = np.clip(base + noise, 0, 255)
edge = cv2.dilate(al, np.ones((9, 9), np.uint8)) - cv2.erode(al, np.ones((9, 9), np.uint8)); gold = np.array([226, 178, 76])
rgb = np.where(edge[..., None] > 0, gold, leather); book = Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), 'RGBA'); book.save(os.path.join(O, 'phone_book.png'))

# 5) logo avatar (the real LaunchBack mark lifted from the logo sting), red tick, badges, icons
mark = Image.open(os.path.join(O, 'launchback_mark.png')).convert('RGBA')
def avatar(sz):
    a = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(a); d.ellipse((0, 0, sz - 1, sz - 1), fill=(14, 14, 14, 255))
    m = mark.copy(); m.thumbnail((int(sz * .62), int(sz * .62))); a.alpha_composite(m, ((sz - m.width) // 2, (sz - m.height) // 2)); return a
avatar(1024).save(os.path.join(O, 'avatar.png'))
def seal(sz):   # red 12-point verified seal with a white check
    s = Image.new('RGBA', (sz, sz), (255, 255, 255, 0)); d = ImageDraw.Draw(s); cx = cy = sz / 2; pts = []
    for k in range(48):
        rr = sz * (.48 if k % 4 < 2 else .41); ang = k * np.pi * 2 / 48; pts.append((cx + rr * np.cos(ang), cy + rr * np.sin(ang)))
    d.polygon(pts, fill=RED + (255,)); d.line([(sz * .30, sz * .52), (sz * .45, sz * .66), (sz * .72, sz * .36)], fill=(255, 255, 255, 255), width=int(sz * .09), joint='curve'); return s
t = seal(1200); bgw = Image.new('RGB', (1200, 1200), (255, 255, 255)); bgw.paste(t, mask=t.getchannel('A')); bgw.save(os.path.join(O, 'tick_red.jpg'), quality=95); t.save(os.path.join(O, 'tick_red.png'))
def badge(sticker, sz, out):
    b = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(b); d.rounded_rectangle((0, 0, sz - 1, sz - 1), int(sz * .22), fill=RED + (255,))
    d.rounded_rectangle((int(sz * .035),) * 2 + (int(sz * .965),) * 2, int(sz * .19), outline=(255, 255, 255, 120), width=max(2, sz // 90))
    s = Image.open(os.path.join(O, f'sticker_{sticker}.png')).convert('RGBA'); s.thumbnail((int(sz * .82), int(sz * .82))); b.alpha_composite(s, ((sz - s.width) // 2, (sz - s.height) // 2)); b.save(out)
badge('tyre', 736, os.path.join(O, 'badge_tyre.png')); badge('book', 1024, os.path.join(O, 'badge_book.png')); badge('pin', 1024, os.path.join(O, 'badge_pin.png'))
ic = Image.new('RGBA', (600, 600), (0, 0, 0, 0))   # desktop icons grid
for i, n in enumerate(['tyre', 'toque', 'book', 'cutlery', 'pin', 'pump']):
    s = Image.open(os.path.join(O, f'sticker_{n}.png')).convert('RGBA'); s.thumbnail((150, 150)); r, c = divmod(i, 3); ic.alpha_composite(s, (20 + c * 190 + (150 - s.width) // 2, 40 + r * 250 + (150 - s.height) // 2))
ic.save(os.path.join(O, 'desktop_icons.png'))

# 6) UI cards with the handle: a post (1080x2400) and a profile (1620x2160)
def fit(path, sz):
    im = Image.open(path).convert('RGB'); s = max(sz[0] / im.width, sz[1] / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    return im.crop(((im.width - sz[0]) // 2, (im.height - sz[1]) // 2, (im.width + sz[0]) // 2, (im.height + sz[1]) // 2))
def heart(d, x, y, s, col):
    d.ellipse((x, y, x + s * .55, y + s * .55), fill=col); d.ellipse((x + s * .45, y, x + s, y + s * .55), fill=col); d.polygon([(x + s * .03, y + s * .38), (x + s * .97, y + s * .38), (x + s * .5, y + s)], fill=col)
post = Image.new('RGB', (1080, 2400), (255, 255, 255)); d = ImageDraw.Draw(post)
post.paste(avatar(120).resize((120, 120)), (36, 40), avatar(120).resize((120, 120))); d.text((184, 44), HANDLE, font=F(BOLD, 44), fill=(20, 20, 20)); d.text((184, 98), 'Original audio', font=F(REG, 32), fill=(110, 110, 110))
d.rounded_rectangle((820, 54, 1030, 126), 18, outline=RED, width=4); d.text((862, 66), 'Follow', font=F(BOLD, 38), fill=RED)
post.paste(fit(os.path.join(G, 'chef_broll.png'), (1080, 1080)), (0, 180))
heart(d, 44, 1306, 70, RED); d.text((136, 1306), '11K', font=F(BOLD, 44), fill=(20, 20, 20)); d.ellipse((330, 1306, 400, 1376), outline=(20, 20, 20), width=6); d.text((420, 1306), '95', font=F(BOLD, 44), fill=(20, 20, 20))
d.polygon([(610, 1340), (690, 1306), (670, 1376)], fill=(20, 20, 20)); d.text((710, 1306), '27', font=F(BOLD, 44), fill=(20, 20, 20)); d.text((860, 1306), '858', font=F(BOLD, 44), fill=(20, 20, 20))
d.text((44, 1430), f'{HANDLE}', font=F(BOLD, 44), fill=(20, 20, 20)); d.text((44 + 300, 1430), 'Free. Where to fill up, sleep, eat.', font=F(REG, 40), fill=(40, 40, 40))
d.text((44, 1500), 'View all comments', font=F(REG, 38), fill=(120, 120, 120)); d.text((44, 1556), '4 days ago', font=F(REG, 32), fill=(150, 150, 150))
post.paste(fit(os.path.join(G, 'photo1.png'), (1080, 700)), (0, 1650)); post.save(os.path.join(O, 'ui_post.jpg'), quality=94)
prof = Image.new('RGB', (1620, 2160), (255, 255, 255)); d = ImageDraw.Draw(prof)
d.text((60, 60), HANDLE, font=F(BOLD, 70), fill=(20, 20, 20)); av = avatar(300); prof.paste(av, (60, 220), av)
for i, (n, l) in enumerate([('19', 'posts'), ('2.4K', 'followers'), ('106', 'following')]):
    x = 460 + i * 380; d.text((x, 250), n, font=F(BOLD, 66), fill=(20, 20, 20)); d.text((x, 340), l, font=F(REG, 44), fill=(90, 90, 90))
d.text((60, 560), 'LaunchBack | Finding the guidebook', font=F(BOLD, 50), fill=(20, 20, 20)); d.text((60, 630), 'behind every business you love.', font=F(REG, 50), fill=(40, 40, 40))
d.rounded_rectangle((60, 760, 700, 880), 24, fill=(235, 235, 235)); d.text((110, 786), 'Following', font=F(BOLD, 52), fill=(20, 20, 20)); d.rounded_rectangle((730, 760, 1360, 880), 24, fill=(235, 235, 235)); d.text((860, 786), 'Message', font=F(BOLD, 52), fill=(20, 20, 20))
for i, n in enumerate(['chef_broll', 'photo1', 'photo2']): prof.paste(fit(os.path.join(G, f'{n}.png'), (530, 760)), (i * 540, 1040))
prof.save(os.path.join(O, 'ui_profile.jpg'), quality=94); print('assets:', sorted(os.listdir(O)))
