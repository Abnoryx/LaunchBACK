"""Turntable sheet for several GLBs: one comp per model, 4 frames each (Y 0/90/180/270) through a real camera.
usage: python3 model_turntable_all.py name:scale[:rx] ...  -> scratch/turntable_tpl.json (comps TT_<name>)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project, K
from library import style as S
p = Project()
for arg in sys.argv[1:]:
    parts = arg.split(':'); n, sc = parts[0], float(parts[1]); rx = float(parts[2]) if len(parts) > 2 else 0.0
    c = p.comp(f'TT_{n}', dur=4 * S.F)
    c.camera('camera', 0, 4 * S.F, [(0, 540, 960, -1050, 1050)])
    L = c.model(p.model(f'{n}.glb'), 0, 4 * S.F)
    c.transform(L, pos=[540, 960, 0], scale=[sc, sc, sc], rx=rx, ry=K(*[(k * S.F, 90.0 * k, 'hold') for k in range(4)]))
    c.footage(p.solid('#808080'), 0, 4 * S.F)
    c.finalize()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'turntable_tpl.json'); p.dump(out); print(out)
