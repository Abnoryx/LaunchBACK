import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import pill_diagram
p = Project(); pill_diagram.build(p, 'PILL')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pill_tpl.json'); p.dump(out); print(out)
