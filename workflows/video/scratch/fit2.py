"""Element fitter v2: find each element in the reel and in our render by its own colour, compare boxes,
and solve position/size corrections directly (screen px -> world units through the per-frame camera solve).
usage: python3 fit2.py <ours_frames_dir> [--apply]   (frames f%05d.png in reel numbering)
Prints per-element corrections for the hero_word template layout; --apply writes them into hero_word_fit.json."""
import csv, json, os, subprocess, sys
import numpy as np
from PIL import Image

REEL = '/home/user/tpl/reels/r1.mp4'
CAM = {int(r['frame']): (float(r['x']), float(r['y']), float(r['z']), float(r['zoom']))
       for r in csv.DictReader(open('/home/user/tpl/an/research/camera/cam_all.tsv'), delimiter='\t') if r['comp'] == 'Comp 1'}

# element: (layout key, world z, colour predicate on int RGB arrays, screen region (y0,y1,x0,x1) or None, frames)
ELEMENTS = {
    'q1':     ('q1', -264, lambda r, g, b: (r > 246) & (g > 246) & (b > 246), (900, 1500, 0, 1080), [45, 50, 55]),
    'q2':     ('q2', -264, lambda r, g, b: (g > 150) & (r < 40) & (b < 40), (1000, 1500, 0, 1080), [55, 60, 64]),  # only fully revealed frames
    'hero':   ('hero', 671, lambda r, g, b: (g > 70) & (g < 120) & (r < 45) & (b < 15), (500, 1400, 0, 1080), [30, 40, 50]),
    'markB':  ('markB', 1049, lambda r, g, b: (g > 160) & (r > 40) & (r < 90) & (b > 25) & (b < 90), (0, 700, 500, 1080), [15, 30, 45]),
    'markA':  ('markA', 99, lambda r, g, b: (g > 160) & (r > 40) & (r < 90) & (b > 25) & (b < 90), (1200, 1920, 0, 700), [15, 30]),
    'sub2':   ('sub2', 582, lambda r, g, b: (g > 150) & (r < 40) & (b < 40), (800, 1300, 0, 700), [70, 80, 90]),
}


def frame(path_or_n, ours_dir=None):
    if ours_dir is None:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str((path_or_n + 0.5) / 30), '-i', REEL, '-frames:v', '1', '-vf', 'scale=1080:1920',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(int)
    return np.asarray(Image.open(f'{ours_dir}/f{path_or_n:05d}.png').convert('RGB')).astype(int)


def box(a, pred, region):
    y0, y1, x0, x1 = region
    m = pred(a[y0:y1, x0:x1, 0], a[y0:y1, x0:x1, 1], a[y0:y1, x0:x1, 2])
    if m.sum() < 150:
        return None
    ys, xs = np.where(m)
    # robust box: 2nd-98th percentile so stray pixels don't dominate
    return (np.percentile(xs, 2) + x0, np.percentile(xs, 98) + x0, np.percentile(ys, 2) + y0, np.percentile(ys, 98) + y0, int(m.sum()))


def main():
    ours = sys.argv[1]
    res = {}
    for name, (key, z, pred, region, frames) in ELEMENTS.items():
        dxs, dys, ss = [], [], []
        for n in frames:
            if not os.path.exists(f'{ours}/f{n:05d}.png'):
                continue
            br, bo = box(frame(n), pred, region), box(frame(n, ours), pred, region)
            if not br or not bo:
                print(f'{name} f{n}: reel {bool(br)} ours {bool(bo)}'); continue
            cx, cy, cz, zoom = CAM[n]
            mag = zoom / (z - cz)
            # centre offset (screen px) -> world, size ratio from box heights (widths depend on font substitutes)
            dxs.append(((br[0] + br[1]) / 2 - (bo[0] + bo[1]) / 2) / mag)
            dys.append(((br[2] + br[3]) / 2 - (bo[2] + bo[3]) / 2) / mag)
            ss.append((br[3] - br[2]) / max(1, bo[3] - bo[2]))
        if dxs:
            res[key] = {'dx': round(float(np.median(dxs)), 1), 'dy': round(float(np.median(dys)), 1), 'scale': round(float(np.median(ss)), 3), 'n': len(dxs)}
            print(name, res[key])
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hero_word_fit.json')
    if '--apply' in sys.argv:
        json.dump(res, open(out, 'w'), indent=1)
        print('->', out)


if __name__ == '__main__':
    main()
