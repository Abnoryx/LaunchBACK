"""Save every DISTINCT transition measured in a rescene run as its own asset with an .mp4 preview (library/transitions/<reel>/<tag>.*).
usage: python3 -m extract.transitions_export <run name> [--out DIR]
Reads extract/runs/<name>/measure.json (cuts + transition tags). Params are defaults per tag unless the run measured them
(`params_source` says which); each spec lists how often the tag occurs and at which cut frames, so the user can check it in the reel."""
import json, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE); sys.path.insert(0, VID)
from library import transitions as T


def main(name, out=None):
    m = json.load(open(os.path.join(HERE, 'runs', name, 'measure.json'))); at = defaultdict(list)
    for fr, tags in m['transitions'].items():
        for t in tags: at[t].append(int(fr))
    made = []
    for tag, frames in sorted(at.items()):
        if tag not in T.DEFAULTS: print('skip (no recipe yet):', tag, frames); continue
        spec = T.export(f'{name}/{tag}', tag, None, {'reel': name, 'uses': len(frames), 'at_frames': sorted(frames), 'params_source': 'defaults per tag (not yet measured per use)'}, out_dir=out or T.OUT)
        made.append(spec['id']); print('saved', spec['id'], spec['preview'])
    return made


if __name__ == '__main__':
    a = sys.argv[1:]; main(a[0], a[a.index('--out') + 1] if '--out' in a else None)
