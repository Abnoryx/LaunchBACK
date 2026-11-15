"""Prove template 'share_card' against reel S10 (f934-991)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import share_card
p = Project(); share_card.build(p, 'S10')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's10_tpl.json'); p.dump(out); print(out)
