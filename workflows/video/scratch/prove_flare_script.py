"""Prove template 'flare_script' against Zeigarnik shot 2a (f99-152)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import flare_script
p = Project(); flare_script.build(p, 'Z2A')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'z2a_tpl.json'); p.dump(out); print(out)
