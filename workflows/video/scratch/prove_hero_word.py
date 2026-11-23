"""Prove template 'hero_word' against reel S1: fill it with the original's content, dump the scene for render/fit."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library.aeb import Project
from library.templates import hero_word

tw = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hero_word_tweaks.json')
p = Project()
hero_word.build(p, 'S1')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's1_tpl.json')
p.dump(out)
print(out)
