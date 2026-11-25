"""Builds the 'LaunchBack Edit Room' artifact page (HTML) from slots.json + scenes_gen.json + clips.json (asset urls).
usage: python3 edit_room/build_page.py <out.html>   (clips.json = {"reel": url, "01": url, ...}; missing -> no preview)"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.dirname(HERE)
slots = json.load(open(os.path.join(RUN, 'slots.json'))); scenes = json.load(open(os.path.join(RUN, 'scenes_gen.json')))
clips = json.load(open(os.path.join(HERE, 'clips.json'))) if os.path.exists(os.path.join(HERE, 'clips.json')) else {}
CHROME = {'earnera.co', 'earnera', '9:41', 'Sunday 11 September 2025', 'Read 12:30 PM', 'Song - Original audio', '4 days ago', 'View all comments', 'File', 'Edit', 'Search',
          'Help', 'General -', 'Notepad', 'My PC', 'Files', 'Recycle Bin', 'Project', 'Micheal Jordan', '1', '2', '3', '!!'}
data = []
for s in scenes:
    sid = s['scene']; n = sid.split('/s')[1]; m = slots[sid]; words, chrome = [], []
    for k, v in m.items():
        (chrome if k.strip() in CHROME else words).append({'k': k, 'v': v})
    data.append({'id': 's' + n, 'n': n, 'sec': s['seconds'], 'clip': clips.get(n, ''), 'words': words, 'chrome': chrome})
man = os.path.join(RUN, 'work', 'manifest.json')   # plain concat: a cut is the running total of scene durations
dur = [round(e['to'] - e['from'], 3) for e in json.load(open(man))['entries']] if os.path.exists(man) else [d['sec'] for d in data]
cuts = [round(sum(dur[:i + 1]), 3) for i in range(len(dur) - 1)]
payload = json.dumps({'scenes': data, 'reel': clips.get('reel', ''), 'cuts': cuts}, ensure_ascii=False).replace('<', '\\u003c')
html = open(os.path.join(HERE, 'page_template.html')).read().replace('/*__DATA__*/{}', payload)
open(sys.argv[1], 'w').write(html); print('page', len(html), 'bytes;', len(data), 'scenes;', sum(1 for d in data if d['clip']), 'clips')
