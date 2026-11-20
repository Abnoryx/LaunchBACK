"""S9 two ways for the user: A = spin-into handoffs with the template's own curves; B = the pro's advice:
quad-out on every curve + seamless (matched-speed quad-in -> quad-out) handoffs + props never fully still."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from library import aeb, style as S, palette_swap
from library.aeb import Project
from library.templates import brand_box
import michelin
params = dict(next(p for n, t, p in michelin.SHOTS if n == 'S9'))
p = Project()
brand_box.build(p, 'S9A', **params)                       # A: spin into each other, template curves
aeb.EASE_OVERRIDE = S.QUAD_OUT                            # B: quad out on every bezier curve in this comp
brand_box.build(p, 'S9B', **params, swap_ease=(S.QUAD_IN, S.QUAD_OUT), idle_turn=8.0)
aeb.EASE_OVERRIDE = None
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's9_ab.json'); p.dump(out)
d = json.load(open(out)); palette_swap.apply(d); json.dump(d, open(out, 'w')); print(out)

# C: like B but a stronger curve (cubic out, 3x start speed; cubic-in handoffs at the same 3x)
p2 = Project()
aeb.EASE_OVERRIDE = S.CUBIC_OUT
brand_box.build(p2, 'S9C', **params, swap_ease=(S.CUBIC_IN, S.CUBIC_OUT), idle_turn=8.0)
aeb.EASE_OVERRIDE = None
out2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's9_c.json'); p2.dump(out2)
d = json.load(open(out2)); palette_swap.apply(d); json.dump(d, open(out2, 'w')); print(out2)
