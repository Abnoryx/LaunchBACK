"""Edit Room page builder, shared by /gen and /rescene.  usage: python3 edit_room/build.py <room.json> <out.html>
room.json = {title, sub, reel: url, cuts: [seconds of each cut in the reel], scenes: [{id:'s01', n:'01', sec, clip: url, words:[{k,v}], chrome:[{k,v}]}]}
The page saves to the artifact db: scenes/<id>, pins/<id|reel> (pins + groups), project/main."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); room = json.load(open(sys.argv[1]))
room.setdefault('cuts', []); room.setdefault('reel', ''); room.setdefault('title', 'Edit Room'); room.setdefault('sub', '')
payload = json.dumps(room, ensure_ascii=False).replace('<', '\\u003c')
html = open(os.path.join(HERE, 'template.html')).read().replace('/*__DATA__*/{}', payload)
open(sys.argv[2], 'w').write(html); print('page', len(html), 'bytes;', len(room['scenes']), 'scenes;', sum(1 for s in room['scenes'] if s.get('clip')), 'clips')
