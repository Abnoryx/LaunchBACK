"""Prove template 'brand_box' against reel S4 (f345-454)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import brand_box
p = Project(); brand_box.build(p, 'S4')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's4_tpl.json'); p.dump(out); print(out)
