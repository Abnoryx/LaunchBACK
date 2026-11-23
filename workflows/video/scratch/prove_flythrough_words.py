"""Prove template 'flythrough_words' against reel S8b (f774-844)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import flythrough_words
p = Project(); flythrough_words.build(p, 'S8b')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's8b_tpl.json'); p.dump(out); print(out)
