"""Prove template 'brain_collage' against reel S8a (f713-773)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import brain_collage
p = Project(); brain_collage.build(p, 'S8a')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's8a_tpl.json'); p.dump(out); print(out)
