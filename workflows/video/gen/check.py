"""Gate: every past APPROVED /gen plan must still pass gen/score.py's current rules (incl. learned ones).
A change to /gen (rules, ranking, templates) is kept only if this passes.  usage: python3 -m gen.check"""
import glob, json, os, sys
from .score import score
HERE = os.path.dirname(os.path.abspath(__file__)); fails = 0
for lp in sorted(glob.glob(os.path.join(HERE, 'runs', '*', 'log.json'))):
    L = json.load(open(lp)); pp = os.path.join(os.path.dirname(lp), 'plan.json')
    if L.get('status') != 'approved' or not os.path.exists(pp): continue
    b = score(json.load(open(pp)))
    if b: fails += 1; print(f"{L['run']}: now fails -> " + '; '.join(b))
print('OK: all approved plans still pass' if not fails else f'{fails} approved plan(s) now fail: fix the rule or the change')
sys.exit(1 if fails else 0)
