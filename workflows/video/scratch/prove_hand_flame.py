"""Prove template 'hand_flame' against reel S2b (f200-248)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import hand_flame
p = Project(); hand_flame.build(p, 'S2b')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's2b_tpl.json'); p.dump(out); print(out)
