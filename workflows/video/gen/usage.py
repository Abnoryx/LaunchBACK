"""Which reel (group of scenes) each /gen run used, and when. Rule (user, 2026-11-28): never build two reels in a row from the same source reel's shots;
a reel is available again after `group.cooldown_days` (7) days. The planner (gen.groups) skips blocked reels unless forced with --ignore-cooldown.
usage: python3 -m gen.usage            show the ledger and what is blocked now
       python3 -m gen.usage record <group> <run> [YYYY-MM-DD]     (call once the run's reel is delivered / approved)"""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'usage.json')
def load(): return json.load(open(P)) if os.path.exists(P) else []
def cooldown(): return json.load(open(os.path.join(HERE, 'config.json'))).get('group', {}).get('cooldown_days', 7)
def blocked(today=None):
    """{group: date it becomes available again} for every reel used inside the cooldown window"""
    today = today or datetime.date.today(); out = {}
    for e in load():
        d = datetime.date.fromisoformat(e['date']); free = d + datetime.timedelta(days=cooldown())
        if free > today: out[e['group']] = max(free, out.get(e['group'], free))
    return out
def record(group, run, date=None):
    L = load(); L.append(dict(group=group, run=run, date=date or datetime.date.today().isoformat())); json.dump(L, open(P, 'w'), indent=1); return L
if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'record': record(a[1], a[2], a[3] if len(a) > 3 else None); print('recorded', a[1], a[2])
    else:
        print(json.dumps(load(), indent=1)); b = blocked(); print('blocked now:', {k: str(v) for k, v in b.items()} or 'none')
