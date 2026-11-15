"""Style system for the 'Psychology Trick' look. Every template pulls from here, so a fix lands everywhere.
All values were measured on the posted reel (see research/shots_*/REPORT.md); none are copied from the project file."""
import csv
from .aeb import (K, hexc, reveal, gaussian, lens_blur, minimax, qca, mask, MULTIPLY)

F = 1 / 30

# ---------------------------------------------------------------- palettes (original green / ours red)
PALETTES = {
    'original': {'accent': '#0DBE00', 'accent_dark': '#186000', 'accent_mark': '#3DC037', 'mark_side': '#001A00',
                 'mark_stroke': '#002B01', 'ink': '#242424', 'ink_soft': '#2F2A26', 'paper': '#E8E8E8', 'white': '#FFFFFF'},
    'red': {'accent': '#E10600', 'accent_dark': '#8A1C1C', 'accent_mark': '#FF1A1A', 'mark_side': '#2A0000',
            'mark_stroke': '#3A0303', 'ink': '#242424', 'ink_soft': '#2F2A26', 'paper': '#E8E8E8', 'white': '#FFFFFF'},
}

# ---------------------------------------------------------------- fonts (role -> engine font name)
# Arimo = metric-compatible Helvetica; Anton scored best for Coolvetica HeavyComp (user's free Coolvetica lacks Heavy cuts);
# CoolCondensed = the user's Coolvetica Condensed (the reel's SHARE pill).
FONTS = {'sans_bold': 'Arimo', 'hero_condensed': 'Anton', 'pill': 'CoolCondensed', 'serif_italic': 'Kokila-BoldItalic',
         'didot_italic': 'DidotLTPro-BoldItalic', 'hand': 'BradleyHand', 'fine_serif': 'TimesNewRomanPSMT'}

# ---------------------------------------------------------------- eases (cubic-bezier, from the reel's motion analysis)
EASE = {'standard': (0.8, 0, 0.2, 1), 'out': (0.333, 0, 0, 1), 'snap': (0, 0, 0, 1), 'whip': (1, 0, 1, 1),
        'push': (0.167, 0, 0, 1), 'dolly': (0.9, 0, 0.1, 1)}

# ---------------------------------------------------------------- text styles
TEXT = {
    # word reveal: opacity 0 -> 1 with blur 10, offset -100 -> 100 over ~10 frames (visible 3-4 f after first key)
    'word_reveal': dict(based_on=3, opacity=0, blur=10),
    'char_reveal': dict(based_on=1, opacity=0, blur=10),
    'rise_reveal': dict(based_on=2, opacity=0, blur=0, dy=115),
    'tracking': -80,
}


def word_reveal(t0, t1, **kw):
    return reveal(t0, t1, **{**TEXT['word_reveal'], **kw})


def char_reveal(t0, t1, **kw):
    return reveal(t0, t1, **{**TEXT['char_reveal'], **kw})


# ---------------------------------------------------------------- finish stack (paper shots)
def paper_finish(proj, comp, t_in, t_out, film=True, fringe=0.8, edge_blur=14, edge_fringe=3, edge_feather=150, diamond=1.0):
    """Adjustments + overlays that sit on top of every paper shot: edge blur (inverted diamond), radial fringing,
    film-edge print (multiply). Call FIRST so they end up on top of the stack."""
    if film:  # film-edge print sits ABOVE the edge blur / fringing (reel: it prints crisp over the content)
        f = proj.still('film_edge.png', 1080, 1920)
        comp.footage(f, t_in, t_out, blend=MULTIPLY)
    edge = comp.adjustment('edge blur', t_in, t_out)
    comp.masks(edge, mask([[540 + (x - 540) * diamond, 960 + (y - 960) * diamond] for x, y in ([540, 60], [70, 960], [540, 1860], [1010, 960])], inv=True, feather=edge_feather))
    comp.effects(edge, gaussian(edge_blur), qca(edge_fringe))
    q = comp.adjustment('fringe', t_in, t_out)
    comp.effects(q, qca(fringe))


def paper(proj, comp, t_in, t_out, color=None):
    """Flat paper background. Call LAST (bottom of the stack)."""
    s = proj.solid(color or PALETTES['original']['paper'], name='paper')
    return comp.footage(s, t_in, t_out)


# ---------------------------------------------------------------- transition kit
def minimax_flash(comp, frame, frames=2, radius=31):
    """One/two-frame horizontal minimax smear on a cut (reel f67-68, f96-98, f140-142)."""
    L = comp.adjustment(f'minimax {frame}', frame * F, (frame + frames) * F)
    comp.effects(L, minimax(radius))
    return L


def lens_blur_in(comp, t0=0.0, frames=20, radius=20):
    L = comp.adjustment('lens blur in', t0, t0 + (frames + 1) * F)
    comp.effects(L, lens_blur(K((t0, float(radius)), (t0 + frames * F, 0.0))))
    return L


def lens_blur_out(comp, t1, frames=10, radius=20):
    L = comp.adjustment('lens blur out', t1 - frames * F, t1)
    comp.effects(L, lens_blur(K((t1 - frames * F, 0.0), (t1, float(radius)))))
    return L


# ---------------------------------------------------------------- camera
CAM_TSV = '/home/user/tpl/an/research/camera/cam_all.tsv'


def solved_camera(comp_name, f0, f1, offset=0):
    """Per-frame camera solved against the reel (x, y, z, zoom). offset shifts reel frames to local time."""
    rows = [r for r in csv.DictReader(open(CAM_TSV), delimiter='\t') if r['comp'] == comp_name and f0 <= int(r['frame']) <= f1]
    return [((int(r['frame']) - offset) * F, float(r['x']), float(r['y']), float(r['z']), float(r['zoom'])) for r in rows]


# ---------------------------------------------------------------- elements
def stacked_mark(comp, name, char, t_in, t_out, pos, scale, rot, pal, n=15, step=(-3.5, 2.5), size=466, font=None):
    """Extruded 3D-looking glyph (the floating '?'): n stacked copies offset down-left, dark sides, accent face + stroke."""
    layers = []
    for k in range(n):
        front = k == 0
        L = comp.text(f'{name} {k}', char, t_in, t_out, font or FONTS['sans_bold'], size,
                      pal['accent_mark'] if front else pal['mark_side'], justify=7415,
                      stroke=pal['mark_stroke'] if front else None, stroke_w=4 if front else 0, three_d_layer=True)
        comp.transform(L, pos=[pos[0] + k * step[0], pos[1] + k * step[1], pos[2]], scale=[scale, scale, scale], rot=rot)
        layers.append(L)
    return layers
