"""Preview an animated GLB at several times: comp 'HP', frames every 3 f for 2 s, model 3/4 view."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library import style as S
f, sc, ry, rx = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
p = Project(); c = p.comp('HP', dur=2.2)
c.camera('camera', 0, 2.2, [(0, 540, 960, -1050, 1050)])
L = c.model(p.model(f), 0, 2.2)
c.transform(L, pos=[540, 1200, 0], scale=[sc, sc, sc], ry=ry, rx=rx)
c.footage(p.solid('#8a8a8a'), 0, 2.2)
c.finalize()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_preview.json'); p.dump(out); print(out)
