"""Prove template 'disc_brain' against reel S1b (f97-140)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import disc_brain
p = Project(); disc_brain.build(p, 'S1b')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's1b_tpl.json'); p.dump(out); print(out)
