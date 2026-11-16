"""Prove template 'calendar_flip' against reel S5 (f455-546)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import calendar_flip
p = Project(); calendar_flip.build(p, 'S5')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's5_tpl.json'); p.dump(out); print(out)
