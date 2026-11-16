"""Split the LaunchBack logo (user-supplied PNG, white on black) into animatable pieces (white on transparent):
mark_up (the up-arrow L), mark_arrow (diagonal launch arrow + head + B spine), mark_bowl (lower B chevron),
and one PNG per wordmark letter. Writes logo/pieces.json with each piece's box in source px."""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage

D = os.path.join(os.path.dirname(__file__), 'assets', 'logo')


def main():
    g = np.asarray(Image.open(os.path.join(D, 'launchback_src.png')).convert('L')).astype(float)
    alpha = np.clip((g - 20) / 215, 0, 1)
    H, W = g.shape
    yy, xx = np.mgrid[0:H, 0:W]
    mark = (xx >= 150) & (xx <= 430) & (yy >= 255) & (yy <= 510)
    f = (yy - 500) + 0.935 * (xx - 237)   # line through the black stripe between the arrow and the B's lower chevron
    up = mark & ((xx < 229) | ((xx < 275) & (yy < 347)))      # shaft + the whole arrowhead triangle
    regions = {'mark_up': up,
               'mark_bowl': mark & ~up & (f > 0) & (yy >= 396),
               'mark_arrow': mark & ~up & ~((f > 0) & (yy >= 396))}
    lab, k = ndimage.label(g > 128)
    letters = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if sl[1].start > 440 and (lab[sl] == i + 1).sum() > 200:
            letters.append((sl[1].start, i + 1))
    names = 'L A U N C H B A2 C2 K'.split()
    for (x0, idx), nm in zip(sorted(letters), names):
        regions['l_' + nm] = ndimage.binary_dilation(lab == idx, iterations=2)
    out = {}
    for nm, m in regions.items():
        a = alpha * m
        ys, xs = np.where(a > 0.01)
        x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[..., :3] = 255; rgba[..., 3] = (a[y0:y1, x0:x1] * 255).astype(np.uint8)
        Image.fromarray(rgba, 'RGBA').save(os.path.join(D, nm + '.png'))
        out[nm] = [int(x0), int(y0), int(x1), int(y1)]
    json.dump(out, open(os.path.join(D, 'pieces.json'), 'w'), indent=1)
    print(out)


if __name__ == '__main__':
    main()
