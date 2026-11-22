"""Score a /gen plan before building (catches weak plans for free). Rules: gen/config.json + learned gen/rules.json.
plan.json: {"shots": [{"template", "text", "seconds", "world", "invert": bool, "text_px", "elements": n}], ...}
usage: python3 -m gen.score <plan.json>  -> prints problems; exit 1 if any"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'config.json')))['rules']
LEARNED = os.path.join(HERE, 'rules.json')


def score(plan):
    S = plan['shots']; bad = []
    lo, hi = R['shot_seconds']
    for i, s in enumerate(S):
        if not lo <= s['seconds'] <= hi + 1.5: bad.append(f"shot {i} is {s['seconds']}s (aim {lo}-{hi}s)")
        if len(s.get('text', '').split()) > R['max_words_per_beat']: bad.append(f"shot {i} has more than {R['max_words_per_beat']} words on screen")
        if s.get('text_px') and s['text_px'] < R['min_text_px']: bad.append(f"shot {i} text {s['text_px']}px < {R['min_text_px']}px (phone)")
        if s.get('elements') and s['seconds'] / s['elements'] > 0.5 + 1e-9 and s['template'] != 'logo_reveal':
            bad.append(f"shot {i}: a new element only every {s['seconds'] / s['elements']:.2f}s (aim <=0.5s)")
        if i and s['template'] == S[i - 1]['template'] and s['template'] != 'cine_scene': bad.append(f"shot {i} repeats template {s['template']}")
    if S and len(S[0].get('text', '').split()) > R['hook_max_words']: bad.append('hook has too many words')
    if sum(bool(s.get('invert')) for s in S) > R['max_invert_flashes']: bad.append('too many invert flashes')
    run = 1
    for i in range(1, len(S)):
        run = run + 1 if S[i].get('world') == S[i - 1].get('world') else 1
        if run > R['world_flip_every_shots'][1]: bad.append(f"shot {i}: {run} {S[i].get('world')} shots in a row (flip paper/dark every 1-3)"); run = 0
    if not S or S[-1]['template'] != 'logo_reveal': bad.append('must end on the LaunchBack logo sting (logo_reveal)')
    for r in (json.load(open(LEARNED)) if os.path.exists(LEARNED) else []):   # learned from the user's notes
        v = [i for i, s in enumerate(S) if eval(r['check'], {}, dict(s=s, plan=plan))]
        if v: bad.append(f"{r['note']} (shots {v})")
    return bad


if __name__ == '__main__':
    b = score(json.load(open(sys.argv[1])))
    print('\n'.join(b) if b else 'OK: plan passes every rule'); sys.exit(1 if b else 0)
