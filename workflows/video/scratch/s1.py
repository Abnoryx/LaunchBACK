"""S1 (reel f0-96): 'ever WONDER why test drive' + car + two 3D '?' marks. Written from reel measurements only."""
import csv, os
from aeb import (Project, K, hexc, reveal, fx, gaussian, drop_shadow, lens_blur, minimax, qca, mask,
                 MULTIPLY, LEFT, CENTER)

HERE = os.path.dirname(os.path.abspath(__file__))
CAM_TSV = '/home/user/tpl/an/research/camera/cam_all.tsv'  # per-frame camera solved against the reel
F = 1 / 30
OUT_T = 97 / 30  # cut at f97
EASE = (0.8, 0, 0.2, 1)
GREEN = '#0DBE00'
HELV = 'Helvetica-Bold'


def camera_frames(comp_name='Comp 1', f0=0, f1=97):
    rows = [r for r in csv.DictReader(open(CAM_TSV), delimiter='\t') if r['comp'] == comp_name and f0 <= int(r['frame']) <= f1]
    return [(int(r['frame']) * F, float(r['x']), float(r['y']), float(r['z']), float(r['zoom'])) for r in rows]


def question(c, name, pos, scale, rot, tilt=0, n=15, step=(1.6, 2.2), size=466, front='#3DC037', side='#001A00', stroke='#002B01'):
    """Extruded '?' faked the way motion designers do it: n stacked copies offset down-right, dark sides, green face."""
    layers = []
    for k in range(n):  # top of stack = front face
        is_front = k == 0
        L = c.text(f'{name} {k}', '?', 0, OUT_T, HELV, size, front if is_front else side, justify=CENTER,
                   stroke=stroke if is_front else None, stroke_w=4 if is_front else 0, three_d_layer=True)
        c.transform(L, pos=[pos[0] + k * step[0], pos[1] + k * step[1], pos[2]], scale=[scale, scale, scale], rot=rot,
                    rx=tilt)
        layers.append(L)
    return layers


def build(car=True):
    p = Project()
    c = p.comp('S1', dur=OUT_T, motion_blur=False)
    film = p.still('film_edge.png', 1080, 1920)
    paper = p.solid('#E8E8E8', name='paper')

    # ---- adjustments (top)
    mm1 = c.adjustment('minimax 1', 67 * F, 69 * F); c.effects(mm1, minimax(31))
    mm2 = c.adjustment('minimax 2', 96 * F, 99 * F); c.effects(mm2, minimax(35))
    lb = c.adjustment('lens blur in', 0, 21 * F); c.effects(lb, lens_blur(K((0, 20.0), (20 * F, 0.0))))
    edge = c.adjustment('edge blur', 0, OUT_T)
    c.masks(edge, mask([[540, 60], [70, 960], [540, 1860], [1010, 960]], inv=True, feather=150))
    c.effects(edge, gaussian(14), qca(3))
    q = c.adjustment('fringe', 0, OUT_T); c.effects(q, qca(0.8))
    # ---- film edge prints over everything (multiply)
    fl = c.footage(film, 0, OUT_T, blend=MULTIPLY)

    # ---- content (3D, depth-sorted by the engine)
    cam = c.camera('camera', 0, OUT_T, camera_frames())

    ever = c.text('ever', 'ever', 0, OUT_T, HELV, 131, '#2F2A26', tracking=-80, three_d_layer=True,
                  reveal=reveal(0.367, 0.7, based_on=3))
    c.transform(ever, pos=[-185, 669, 671])
    wonder = c.text('WONDER', 'WONDER', 0, OUT_T, 'Anton', 430, '#186000', hscale=1.0, three_d_layer=True,
                    reveal=reveal(0.567, 0.9, based_on=1))
    c.transform(wonder, pos=[-174, 1235, 671], scale=[163, 163, 100])
    why = c.text('why', 'why', 0, OUT_T, HELV, 78, '#FFFFFF', tracking=-80, three_d_layer=True,
                 reveal=reveal(35 * F, 45 * F, based_on=3))
    c.transform(why, pos=[590, 1110, -264])
    DOF = K((67 * F, 0.0), (74 * F, 40.0))
    c.effects(why, drop_shadow('#000000', 35, 315, 21, 16), gaussian(DOF))
    td = c.text('test drive', 'test drive', 0, OUT_T, HELV, 78, GREEN, tracking=-80, hscale=0.89, three_d_layer=True,
                reveal=reveal(42 * F, 52 * F, based_on=3))
    c.transform(td, pos=[707, 1110, -264])
    c.effects(td, drop_shadow('#000000', 35, 305, 15, 40), gaussian(DOF))
    ws = c.text('work so', 'work so', 67 * F, OUT_T, HELV, 98, '#242424', tracking=-80, three_d_layer=True)
    c.transform(ws, pos=[318, 1028, 582]); c.effects(ws, drop_shadow('#000000', 40, 331, 8, 26))
    we = c.text('well', 'well', 67 * F, OUT_T, HELV, 171, GREEN, tracking=-80, three_d_layer=True)
    c.transform(we, pos=[318, 1153, 582]); c.effects(we, drop_shadow('#000000', 40, 331, 8, 26))

    question(c, '?B', [977.6, 85, 1049], 150, rot=8)
    question(c, '?A', [433, 1850, 99], 150, rot=-16)

    if car and os.path.exists(os.path.join(HERE, 'assets', 'car.png')):
        carf = p.still('car.png', 1024, 688)
        cl = c.footage(carf, 0, OUT_T, three_d_layer=True)
        c.transform(cl, pos=K((0, [1693, 1090, 193], EASE), (0.9, [530, 1090, 193]), (61 * F, [530, 1090, 193], EASE), (81 * F, [-1100, 1090, 193])),
                    scale=[102, 102, 102])

    pl = c.footage(paper, 0, OUT_T)
    c.finalize()
    return p.dump(os.path.join(HERE, 's1.json'))


if __name__ == '__main__':
    print(build())
