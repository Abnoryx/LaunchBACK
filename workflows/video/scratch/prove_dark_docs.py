"""Prove template 'dark_docs' against reel S7 (f636-712)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import dark_docs
p = Project(); dark_docs.build(p, 'S7')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's7_tpl.json'); p.dump(out); print(out)
