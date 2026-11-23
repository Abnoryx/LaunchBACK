"""Prove template 'brain_words' against Zeigarnik shot 2b (f153-195)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import brain_words
p = Project(); brain_words.build(p, 'Z2B')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'z2b_tpl.json'); p.dump(out); print(out)
