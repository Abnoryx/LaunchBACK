"""Template 'needle_solo' (reel S9 f883-933, 51 frames = 1.7 s): the user's move_the_needle shot on its own, no follow_needle
head: wavy white reveal with soft halo, arm swinging in to grip the needle, dark wave wipe-out. The 720x1280 comp is scaled
150% into the 1080x1920 frame. Params: `needle` = nested overrides for move_the_needle/shot.json (words, assets, layout,
timing, wave); `words` = {cta, accent, small, big}. Added 2026-11-23 to replace needle_wave in /gen plans (user)."""
import importlib.util, os
from .. import style as S

DUR_F = 51
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('move_the_needle_adapter', os.path.join(HERE, 'move_the_needle', 'claude', 'follow_needle.py'))
_mtn = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mtn)
DEFAULTS = {'words': {'cta': 'follow for more', 'accent': 'insight', 'small': 'that\nmove the', 'big': 'Needle'}}


def build(p, name, needle=None, **params):
    F = S.F
    words = {**DEFAULTS['words'], **params.get('words', {})}
    for k in ('watermark', 'fineprint'):
        if k in params: words[k] = params[k]
    ov = dict(needle or {}); ov['words'] = {**words, **ov.get('words', {})}
    tail = _mtn.build(p, name + ' needle', **ov)
    c = p.comp(name, dur=DUR_F * F)
    L = c.precomp(tail, 0, DUR_F * F)
    c.transform(L, pos=[540, 960], anchor=[360, 640], scale=[150, 150])
    return c.finalize()
