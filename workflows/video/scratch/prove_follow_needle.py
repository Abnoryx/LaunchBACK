"""Prove template 'follow_needle' against reel S9 (f845-933)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import follow_needle
p = Project(); follow_needle.build(p, 'S9')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's9_tpl.json'); p.dump(out); print(out)
