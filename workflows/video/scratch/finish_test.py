import json, os, sys
sys.path.insert(0, '..')
from library.aeb import Project
from library.templates import hero_word
fin = json.loads(sys.argv[1]); p = Project(); hero_word.build(p, 'S1', finish=fin); p.dump(sys.argv[2])
