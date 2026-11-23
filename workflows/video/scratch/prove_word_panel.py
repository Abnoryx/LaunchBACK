"""Prove template 'word_panel' against reel S2 type section (f141-200)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import word_panel
p = Project(); word_panel.build(p, 'S2a')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's2a_tpl.json'); p.dump(out); print(out)
