"""Run a job on the user's Kaggle GPU (T4) and bring the results back.
usage: python3 -m kgl.run <job.py> <out_dir> [input files/dirs ...] [--name rescene-job] [--no-gpu]
- Inputs are uploaded as a private Kaggle dataset (<user>/<name>-in, new version each run), packed as inputs.tgz.
- <job.py> runs on Kaggle with cwd = the unpacked inputs and env OUT=/kaggle/working/out; files written there come back
  to <out_dir>. Prelude: NVIDIA GL/Vulkan drivers are installed so Chrome/WebGL uses the GPU (see REQUIREMENTS.md).
- Auth: the Kaggle key is injected by the environment's proxy for www.kaggle.com (never stored here).
  User name: env KAGGLE_USER or ~/.kaggle/kaggle.json."""
import argparse, io, json, os, sys, tarfile, time, urllib.request, urllib.error, base64

API = 'https://www.kaggle.com/api/v1'
AUTH = 'Basic ' + base64.b64encode(b'dummy:proxy-injected').decode()   # the proxy replaces it with the saved key


def user():
    if os.environ.get('KAGGLE_USER'): return os.environ['KAGGLE_USER']
    return json.load(open(os.path.expanduser('~/.kaggle/kaggle.json')))['username']


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method, headers={'Authorization': AUTH, 'Content-Type': 'application/json'},
                                 data=json.dumps(body).encode() if body is not None else None)
    for attempt in range(8):   # long queues mean hours of polling: Kaggle answers 429 (rate limit) -> back off, retry
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = r.read()
            break
        except urllib.error.HTTPError as e:   # say which step failed (a bare 403 traceback hid it)
            if e.code in (429, 500, 502, 503, 504) and attempt < 7:
                time.sleep(min(600, 30 * 2 ** attempt)); continue
            print(f'{method} {path} -> {e.code} {e.read()[:300]!r}', file=sys.stderr); raise
    return d if raw else json.loads(d or b'{}')


def upload_inputs(paths, owner, slug):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as t:
        for p in paths: t.add(p, arcname=os.path.basename(p.rstrip('/')))
    data = buf.getvalue()
    b = call('POST', '/blobs/upload', dict(type='DATASET', name='inputs.tgz', contentLength=len(data), lastModifiedEpochSeconds=int(time.time())))
    urllib.request.urlopen(urllib.request.Request(b['createUrl'], data=data, method='PUT',
                                                  headers={'Content-Type': 'application/octet-stream'}), timeout=600).read()
    files = [dict(token=b['token'])]
    def version():
        try: return call('GET', f'/datasets/view/{owner}/{slug}').get('currentVersionNumber') or 0
        except urllib.error.HTTPError: return 0
    v0 = version()
    try:
        r = call('POST', f'/datasets/create/version/{owner}/{slug}', dict(versionNotes='job', files=files))
    except urllib.error.HTTPError:
        r = None
    if not r or r.get('error'):
        r = call('POST', '/datasets/create/new', dict(ownerSlug=owner, slug=slug, title=slug, licenseName='CC0-1.0', isPrivate=True, files=files))
    if r.get('error'): sys.exit(f'dataset upload failed: {r["error"]}')
    for _ in range(90):   # wait until Kaggle has processed the files
        try: s = call('GET', f'/datasets/status/{owner}/{slug}', raw=True).decode().strip().strip('"').lower()
        except urllib.error.HTTPError: s = 'pending'   # a brand-new dataset answers 403 until Kaggle has registered it
        if s == 'ready' and version() > v0: return   # a stale 'ready' is the old version: wait for the new one
        time.sleep(10)
    sys.exit('dataset never became ready')


PRELUDE = r'''
import glob, os, subprocess, sys, tarfile
sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True)
if GPU:   # NVIDIA GL/Vulkan user-space drivers matching the host driver, so Chrome's WebGL runs on the T4
    v = sh('nvidia-smi --query-gpu=driver_version --format=csv,noheader').stdout.split()[0].split('.')[0]
    sh(f'apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libnvidia-gl-{v} libvulkan1')
import shutil
os.makedirs('/kaggle/working/out', exist_ok=True); os.environ['OUT'] = '/kaggle/working/out'
import time
for _ in range(30):   # a just-uploaded dataset version can mount a few moments late
    tgz = glob.glob('/kaggle/input/**/inputs.tgz', recursive=True)
    if tgz or glob.glob('/kaggle/input/**/*.json', recursive=True): break
    time.sleep(10)
if tgz: os.makedirs('/tmp/job', exist_ok=True); tarfile.open(tgz[0]).extractall('/tmp/job')
else:   # Kaggle unpacks big archives itself: copy the unpacked tree (it is read-only)
    print('inputs:', sh('find /kaggle/input -maxdepth 4 | head -20').stdout)
    root = sorted(glob.glob('/kaggle/input/**/render.json', recursive=True) + glob.glob('/kaggle/input/**/measure.json', recursive=True))[0]
    shutil.copytree(os.path.dirname(root), '/tmp/job')
os.chdir('/tmp/job')
# ---- job ----
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('job'); ap.add_argument('out'); ap.add_argument('inputs', nargs='*')
    ap.add_argument('--name', default='rescene-job'); ap.add_argument('--no-gpu', action='store_true')
    a = ap.parse_args(); owner = user(); gpu = not a.no_gpu
    t0 = time.time()
    if a.inputs: upload_inputs(a.inputs, owner, a.name + '-in'); print(f'inputs uploaded {time.time() - t0:.0f}s', flush=True)
    src = f'GPU = {gpu}\n' + PRELUDE + open(a.job).read()
    meta = dict(slug=f'{owner}/{a.name}', newTitle=a.name, text=src, language='python', kernelType='script', isPrivate=True,
                enableGpu=gpu, enableInternet=True, datasetDataSources=[f'{owner}/{a.name}-in'] if a.inputs else [],
                competitionDataSources=[], kernelDataSources=[], categoryIds=[])
    if gpu: meta['machineShape'] = 'NvidiaTeslaT4'
    r = call('POST', '/kernels/push', meta)
    if r.get('error'): sys.exit(f'push failed: {r["error"]}')
    print('running', r.get('url'), flush=True)
    t0, last = time.time(), None
    while True:
        time.sleep(20)
        s = call('GET', f'/kernels/status?userName={owner}&kernelSlug={a.name}')['status'].lower()
        if s != last: print(f'STATUS {s} after {time.time() - t0:.0f}s', flush=True); last = s   # e.g. 'STATUS running' = GPU started
        if s in ('complete', 'error', 'cancelacknowledged', 'cancelrequested'): break
    out = call('GET', f'/kernels/output?userName={owner}&kernelSlug={a.name}')
    os.makedirs(a.out, exist_ok=True)
    log = ''.join(e.get('data', '') for e in json.loads(out.get('log') or '[]'))
    open(os.path.join(a.out, 'kaggle.log'), 'w').write(log)
    for f in out.get('files', []):
        name = f['fileName']
        if not name.startswith('out/'): continue
        dst = os.path.join(a.out, name[4:]); os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        urllib.request.urlretrieve(f['url'], dst)
    print(f'{s} in {time.time() - t0:.0f}s -> {a.out}')
    sys.exit(0 if s == 'complete' else 1)


if __name__ == '__main__':
    main()
