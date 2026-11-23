"""Automatic learning — the last step of EVERY /gen run (this is how /gen gets better each use).
usage:
  python3 -m gen.learn pick <run>                       plan built: count picked templates/assets
  python3 -m gen.learn note <run> "<user note>" "<what I changed>" [--rule "<expr over s>" --why "<rule text>"]
        note -> run log + LEARNINGS.md; --rule also adds an automatic check to gen/score.py (rules.json)
  python3 -m gen.learn outcome <run> approved|rejected  user verdict -> template/asset stats (ranking priors)
  python3 -m gen.learn shot <run> <template> approved|rejected   per-shot verdict"""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE)
CAT = os.path.join(VID, 'library', 'catalog.json'); IDX = os.path.join(VID, 'library', 'assets', 'index.json')


def run_dir(name): return os.path.join(HERE, 'runs', name)


def log(name):
    p = os.path.join(run_dir(name), 'log.json')
    return (json.load(open(p)) if os.path.exists(p) else dict(run=name, notes=[], status='draft')), p


def bump(templates=(), assets=(), key='picked'):
    c = json.load(open(CAT)); I = json.load(open(IDX))
    for t in templates:
        if t in c['templates'] and 'gen' in c['templates'][t]: c['templates'][t]['gen']['stats'][key] = c['templates'][t]['gen']['stats'].get(key, 0) + 1
    akey = 'used' if key == 'picked' else key
    for a in assets:
        if a in I: I[a]['stats'][akey] = I[a]['stats'].get(akey, 0) + 1
    json.dump(c, open(CAT, 'w'), indent=1); json.dump(I, open(IDX, 'w'), indent=1)


def plan(name):
    p = json.load(open(os.path.join(run_dir(name), 'plan.json')))
    return [s['template'] for s in p['shots']], sorted({a for s in p['shots'] for a in s.get('assets', [])})


if __name__ == '__main__':
    cmd, name = sys.argv[1], sys.argv[2]; L, lp = log(name); today = datetime.date.today().isoformat()
    if cmd == 'pick':
        bump(*plan(name), key='picked')
    elif cmd == 'note':
        note, change = sys.argv[3], sys.argv[4]
        L['notes'].append(dict(date=today, note=note, change=change))
        open(os.path.join(HERE, 'LEARNINGS.md'), 'a').write(f"- {today} {name}: \"{note}\" -> {change}\n")
        if '--rule' in sys.argv:
            rp = os.path.join(HERE, 'rules.json'); R = json.load(open(rp))
            R.append(dict(check=sys.argv[sys.argv.index('--rule') + 1], note=sys.argv[sys.argv.index('--why') + 1], from_run=name, date=today))
            json.dump(R, open(rp, 'w'), indent=1)
    elif cmd == 'outcome':
        L['status'] = sys.argv[3]; t, a = plan(name); bump(t, a, key=sys.argv[3])
    elif cmd == 'shot':
        bump([sys.argv[3]], key=sys.argv[4])
    os.makedirs(run_dir(name), exist_ok=True); json.dump(L, open(lp, 'w'), indent=1); print('learned:', cmd, name)
