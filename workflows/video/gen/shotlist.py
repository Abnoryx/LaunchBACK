"""Rank EVERY library shot for each beat by how well it fits the script — nothing else.
No SSIM, no approval stats, no status: those never touch the score (gen.library doesn't even read them).
  relevance = CLIP similarity(beat text, the shot's 3 preview frames) + similarity(beat text, its words or its notes)
            + role match (hook / number / payoff prompt vs the shot) + fit rules (words fit its text slots,
              digits -> a shot that shows numbers, prop wanted -> a shot with a prop, --world)
  pick      = MMR: relevance - lambda * similarity to shots already picked (gen/config.json select.mmr_lambda),
              never the same shot twice. The list is the menu: the brief still decides, the final pick is judgement.
Arxiv refs: CLIP sentence<->shot scoring 2412.09276, 2605.04733; MMR 1506.01273; script-driven selection 2505.03319.
usage: python3 -m gen.shotlist <beats.json> [--world dark|paper] [--top 3] [--plan draft_plan.json]
       python3 -m gen.shotlist --assets tyre book        (search every asset in the library)"""
import json, os, sys
import numpy as np
from . import library as LIB, embed
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')))['select']


def _z(x):
    """z-score across shots (NaN = no data -> 0, i.e. average) so image/text/role terms add on one scale."""
    m = ~np.isnan(x)
    if m.sum() < 2: return np.zeros_like(x)
    z = (x - x[m].mean()) / (x[m].std() + 1e-6); z[~m] = 0
    return z


def roles(beat):
    r = [beat['role']] if beat.get('role') in ('hook', 'payoff') else []
    return r + (['number'] if any(ch.isdigit() for ch in beat['text']) else [])


def rank(beats, world=None):
    """-> per beat: [(mmr score, id, relevance)] best first, and the greedy MMR pick sequence."""
    S = LIB.shots(); E = embed.update(S, quiet=True)
    ids = [k for k in S if k != 'logo_reveal']   # the logo sting is always last, never ranked
    W, F, lam = CFG['weights'], CFG['fit'], CFG['mmr_lambda']
    img = np.stack([E[k]['img'] for k in ids]); has = np.array([E[k]['has_img'] for k in ids]); txt = np.stack([E[k]['txt'] for k in ids])
    tok = np.abs(txt).sum(2) > 0                                                # which captions exist (words, notes)
    vec = embed._norm(np.where(has[:, None], img.mean(1), 0) + txt.sum(1) + 1e-6)   # one vector per shot, for MMR novelty
    best = lambda v: np.where(tok, txt @ v, -np.inf).max(1)                     # best-matching caption, -inf if none
    rp = {r: embed.text([p])[0] for r, p in CFG['role_prompts'].items()}
    bt = embed.text([b['text'] for b in beats]); out, picked = [], []
    for b, e in zip(beats, bt):
        s_img = np.where(has, (img @ e).max(1), np.nan); s_txt = best(e); s_txt[np.isinf(s_txt)] = np.nan
        rel = W['image'] * _z(s_img) + W['text'] * _z(s_txt)
        for r in roles(b):
            sr = np.where(has, (img @ rp[r]).max(1), best(rp[r])); sr[np.isinf(sr)] = np.nan
            rel += W['role'] * _z(sr)
        n = len(b['text'].split())
        for i, k in enumerate(ids):
            s = S[k]
            if s['capacity'] and n > s['capacity']: rel[i] -= F['over_capacity'] * (n - s['capacity'])   # 0 = unknown
            if 'number' in roles(b) and s['numeric']: rel[i] += F['number']
            if b.get('role') == 'hook' and s['hero']: rel[i] += F['hero_hook']
            if b.get('prop') and s['prop']: rel[i] += F['prop']
            if world and E[k]['light'] >= 0 and ('paper' if E[k]['light'] > 0.5 else 'dark') != world: rel[i] -= F['world']
        nov = (vec @ vec[picked].T).max(1) if picked else np.zeros(len(ids))
        mmr = rel - lam * nov; mmr[picked] = -np.inf                            # never the same shot twice
        order = np.argsort(-mmr); picked.append(int(order[0]))
        out.append([(round(float(mmr[i]), 2), ids[i], round(float(rel[i]), 2)) for i in order])
    return out, S, E


def draft_plan(beats, ranked, S, E):
    """Top MMR pick per beat + the logo sting, in gen.score's plan format (a starting point to edit, not the decision)."""
    shots = []
    for b, r in zip(beats, ranked):
        k = r[0][1]; lt = E[k]['light']
        shots.append(dict(template=k, text=b['text'], seconds=round(b['end'] - b['start'], 2),
                          world='any' if lt < 0 else 'paper' if lt > 0.5 else 'dark'))
    return dict(shots=shots + [dict(template='logo_reveal', text='', seconds=3.5, world='dark')])


if __name__ == '__main__':
    if sys.argv[1] == '--assets':
        for h in LIB.find_assets(sys.argv[2:])[:12]: print(h)
        sys.exit()
    arg = lambda f, d=None: sys.argv[sys.argv.index(f) + 1] if f in sys.argv else d
    beats = json.load(open(sys.argv[1])); ranked, S, E = rank(beats, arg('--world')); top = int(arg('--top', 3))
    nop = sorted(k for k in S if not LIB.has_preview(S[k]))
    if nop: print(f'{len(nop)} shot(s) without a preview (ranked on words/notes only; run gen.previews): {", ".join(nop)}\n')
    for b, r in zip(beats, ranked):
        print(f"{b['text']!r:42} -> " + ' | '.join(f'{k} ({s})' for s, k, _ in r[:top]))
    if arg('--plan'):
        json.dump(draft_plan(beats, ranked, S, E), open(arg('--plan'), 'w'), indent=1); print('draft plan ->', arg('--plan'))
