"""Prove template 'word_prop_pop' against reel S3 (f249-344)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import word_prop_pop
p = Project(); word_prop_pop.build(p, 'S3')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's3_tpl.json'); p.dump(out); print(out)
