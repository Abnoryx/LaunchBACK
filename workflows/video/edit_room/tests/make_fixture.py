"""Builds a local test page for the Edit Room: a synthetic 42 s 9:16 webm + the page built from a room.json (clips point at the local file).
usage: python3 make_fixture.py <room.json> <out dir>   -> <out dir>/page.html"""
import json, os, subprocess, sys
room = json.load(open(sys.argv[1])); out = os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
webm = os.path.join(out, 't.webm')
if not os.path.exists(webm):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=270x480:rate=30:duration=42', '-c:v', 'libvpx-vp9', '-b:v', '200k', '-an', webm], check=True)
room['reel'] = 'file://' + webm
for s in room['scenes']: s['clip'] = 'file://' + webm
json.dump(room, open(os.path.join(out, 'room.json'), 'w'))
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build.py'), os.path.join(out, 'room.json'), os.path.join(out, 'page.html')], check=True)
