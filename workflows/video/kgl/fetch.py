"""Wait for an already-pushed Kaggle kernel and download its out/ files (no re-push; use when the local watcher died).
usage: python3 -m kgl.fetch <kernel slug> <out_dir>"""
import json, os, sys, time, urllib.request
from kgl.run import call, user

slug, out_dir = sys.argv[1], sys.argv[2]; owner = user(); t0 = time.time()
while True:
    s = call('GET', f'/kernels/status?userName={owner}&kernelSlug={slug}')['status'].lower()
    if s in ('complete', 'error', 'cancelacknowledged', 'cancelrequested'): break
    time.sleep(30)
out = call('GET', f'/kernels/output?userName={owner}&kernelSlug={slug}')
os.makedirs(out_dir, exist_ok=True)
open(os.path.join(out_dir, 'kaggle.log'), 'w').write(''.join(e.get('data', '') for e in json.loads(out.get('log') or '[]')))
for f in out.get('files', []):
    if f['fileName'].startswith('out/'): urllib.request.urlretrieve(f['url'], os.path.join(out_dir, f['fileName'][4:]))
print(f'{s} after {time.time() - t0:.0f}s -> {out_dir}')
sys.exit(0 if s == 'complete' else 1)
