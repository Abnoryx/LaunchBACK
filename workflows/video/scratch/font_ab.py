import json, sys
sys.path.insert(0, '..')
from library.aeb import Project
from library import style as S
from library.templates import share_card, hero_word
sans, serif, tpl, comp, out = sys.argv[1:6]
S.FONTS['sans_bold'] = sans; S.FONTS['serif_italic'] = serif
p = Project(); (share_card if tpl == 'share' else hero_word).build(p, comp); p.dump(out)
