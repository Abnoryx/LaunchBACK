"""Automatic learning — the last step of EVERY /gen run (this is how /gen gets better each use).
usage:
  python3 -m gen.learn pick <run>                       plan built: record the picked shots/assets in the run log
  python3 -m gen.learn note <run> "<user note>" "<what I changed>" [--rule "<expr over s>" --why "<rule text>"]
        note -> run log + LEARNINGS.md; --rule also adds an automatic check to gen/score.py (rules.json)
  python3 -m gen.learn outcome <run> approved|rejected  user verdict -> run log (gen.check keeps approved plans passing)
  python3 -m gen.learn shot <run> <template> approved|rejected   per-shot verdict -> run log
Learning happens through the user's notes -> rules, never through popularity stats: verdicts are logged, but nothing
here feeds shot ranking (gen.shotlist ranks by fit to the script only)."""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))


def run_dir(name): return os.path.join(HERE, 'runs', name)


def log(name):
    p = os.path.join(run_dir(name), 'log.json')
    return (json.load(open(p)) if os.path.exists(p) else dict(run=name, notes=[], status='draft')), p


def plan(name):
    p = json.load(open(os.path.join(run_dir(name), 'plan.json')))
    if 'shots' not in p: return [x['scene'] for x in p['scenes']], []   # group plan: the group's scenes
    return [s['template'] for s in p['shots']], sorted({a for s in p['shots'] for a in s.get('assets', [])})


if __name__ == '__main__':
    cmd, name = sys.argv[1], sys.argv[2]; L, lp = log(name); today = datetime.date.today().isoformat()
    if cmd == 'pick':
        L['picked'], L['assets'] = plan(name)
    elif cmd == 'note':
        note, change = sys.argv[3], sys.argv[4]
        L['notes'].append(dict(date=today, note=note, change=change))
        open(os.path.join(HERE, 'LEARNINGS.md'), 'a').write(f"- {today} {name}: \"{note}\" -> {change}\n")
        if '--rule' in sys.argv:
            rp = os.path.join(HERE, 'rules.json'); R = json.load(open(rp))
            R.append(dict(check=sys.argv[sys.argv.index('--rule') + 1], note=sys.argv[sys.argv.index('--why') + 1], from_run=name, date=today))
            json.dump(R, open(rp, 'w'), indent=1)
    elif cmd == 'outcome':
        L['status'] = sys.argv[3]
    elif cmd == 'shot':
        L.setdefault('shots', {})[sys.argv[3]] = sys.argv[4]
    os.makedirs(run_dir(name), exist_ok=True); json.dump(L, open(lp, 'w'), indent=1); print('learned:', cmd, name)
