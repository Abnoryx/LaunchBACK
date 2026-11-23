import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import desk_flatlay
p = Project(); desk_flatlay.build(p, 'FLAT')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flat_tpl.json'); p.dump(out); print(out)
