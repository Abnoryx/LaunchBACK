"""Standalone LaunchBack logo animation on the dark plate."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import logo_reveal
p = Project(); logo_reveal.build(p, 'LOGO', bg='#0B0B0B')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo_tpl.json'); p.dump(out); print(out)
