"""Prove template 'statement_flip' against reel S6 (f547-635)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import statement_flip
p = Project(); statement_flip.build(p, 'S6')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's6_tpl.json'); p.dump(out); print(out)
