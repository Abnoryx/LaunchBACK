"""Which Edit Lab (artifact URL) belongs to which run. One artifact per run, never shared between runs: the page data lives in that artifact's db.
usage: python3 edit_room/lab.py list | get <run> | set <run> <url> [title] [gen|rescene]
Before publishing a run's first version: `get <run>`; if missing, publish a NEW artifact and `set` it. Later versions republish to that URL."""
import json, os, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs.json'); d = json.load(open(P)) if os.path.exists(P) else {}; a = sys.argv[1:]
if not a or a[0] == 'list': print(json.dumps(d, indent=1))
elif a[0] == 'get': print(d[a[1]]['url'] if a[1] in d else sys.exit('no lab registered for ' + a[1] + ': publish a NEW artifact, then lab.py set'))
elif a[0] == 'set':
    d[a[1]] = {'url': a[2], 'title': a[3] if len(a) > 3 else a[1], 'kind': a[4] if len(a) > 4 else 'gen'}; json.dump(d, open(P, 'w'), indent=1); print('registered', a[1], a[2])
