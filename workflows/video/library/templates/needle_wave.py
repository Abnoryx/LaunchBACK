"""Template 'needle_wave' (reel S9, f845-933, 89 frames): follow_needle's whip-in + CTA reveal (f845-882), then the
user-supplied 'move_the_needle' recreation from f883 (wavy white reveal with soft halo, arm swinging in to grip the
needle, dark wave wipe-out). The second part is a 720x1280 comp scaled 150% into the 1080x1920 shot.
Params: everything follow_needle takes, plus `needle` = nested overrides for move_the_needle/shot.json (words, assets,
layout, timing, wave). CTA words default to follow_needle's so the handoff at f883 shows the same text."""
import importlib.util, os
from . import follow_needle
from .. import style as S
from ..aeb import K

DUR_F = 89
CUT_F = 38   # reel f883: where move_the_needle starts
XFADE_F = 3
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('move_the_needle_adapter', os.path.join(HERE, 'move_the_needle', 'claude', 'follow_needle.py'))
_mtn = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mtn)


def build(p, name, needle=None, **params):
    F = S.F
    words = params.get('words', {})
    nw = {'cta': words.get('cta', 'follow for more'), 'accent': words.get('accent', 'insight'),
          'small': words.get('small', 'that\nmove the'), 'big': words.get('big', 'Needle')}
    if 'watermark' in params: nw['watermark'] = params['watermark']
    if 'fineprint' in params: nw['fineprint'] = params['fineprint']
    ov = dict(needle or {}); ov['words'] = {**nw, **ov.get('words', {})}
    head = follow_needle.build(p, name + ' head', **params)
    tail = _mtn.build(p, name + ' needle', **ov)
    c = p.comp(name, dur=DUR_F * F)
    t = CUT_F * F
    H = c.precomp(head, 0, (CUT_F + XFADE_F) * F)   # on top, dissolving into the needle part (glow and arm differ)
    c.transform(H, op=K((t, 100.0), ((CUT_F + XFADE_F) * F, 0.0)))
    L = c.precomp(tail, t, DUR_F * F, start=t)
    c.transform(L, pos=[540, 960], anchor=[360, 640], scale=[150, 150])
    return c.finalize()
