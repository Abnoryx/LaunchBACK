"""Turntable check for a GLB in library/assets: four views (0/90/180/270 deg Y) on grey, model ~600 px wide.
usage: python3 model_turntable.py brain.glb [scale%] [rx]  -> scratch/turntable_tpl.json (comp 'TT', 4 frames)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project, K
from library import style as S
f, sc = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
rx = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
p = Project(); c = p.comp('TT', dur=4 * S.F)
L = c.model(p.model(f), 0, 4 * S.F)
c.transform(L, pos=[540, 960, 0], scale=[sc, sc, sc], rx=rx, ry=K(*[(k * S.F, 90.0 * k, 'hold') for k in range(4)]))
c.footage(p.solid('#808080'), 0, 4 * S.F)
c.finalize()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'turntable_tpl.json'); p.dump(out); print(out)
