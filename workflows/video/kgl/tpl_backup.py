"""Back up / restore /home/user/tpl (the bought templates: fonts, reels, zips, analysis notes) as a PRIVATE Kaggle
dataset (<user>/launchback-tpl). Not in git on purpose (licence: use, not redistribution).
usage: python3 -m kgl.tpl_backup backup     (fonts, reels, zips, an/**/*.md|json|tsv|py; skips regenerable x/ and frames)
       python3 -m kgl.tpl_backup restore    (downloads and unpacks into /home/user/tpl)"""
import os, sys, tarfile, time, urllib.request, zipfile, io
from .run import call, user

TPL, SLUG = '/home/user/tpl', 'launchback-tpl'
KEEP_EXT = ('.md', '.json', '.tsv', '.py', '.txt')


def backup():
    owner = user(); tgz = '/tmp/launchback_tpl.tgz'
    with tarfile.open(tgz, 'w:gz') as t:
        for d in ('fonts', 'reels', 'zips'):
            if os.path.isdir(f'{TPL}/{d}'): t.add(f'{TPL}/{d}', arcname=d)
        for root, _, files in os.walk(f'{TPL}/an'):
            for f in files:
                if f.endswith(KEEP_EXT): p = os.path.join(root, f); t.add(p, arcname=os.path.relpath(p, TPL))
    n = os.path.getsize(tgz); print('archive', n // 2**20, 'MB', flush=True)
    b = call('POST', '/blobs/upload', dict(type='DATASET', name='tpl.tgz', contentLength=n, lastModifiedEpochSeconds=int(time.time())))
    with open(tgz, 'rb') as fh:
        req = urllib.request.Request(b['createUrl'], data=fh, method='PUT',
                                     headers={'Content-Type': 'application/octet-stream', 'Content-Length': str(n)})
        urllib.request.urlopen(req, timeout=3600).read()
    files = [dict(token=b['token'])]
    try: r = call('POST', f'/datasets/create/version/{owner}/{SLUG}', dict(versionNotes='backup', files=files))
    except urllib.error.HTTPError: r = None
    if not r or r.get('error'):
        r = call('POST', '/datasets/create/new', dict(ownerSlug=owner, slug=SLUG, title=SLUG, licenseName='unknown', isPrivate=True, files=files))
    print(r.get('error') or f'backed up -> {owner}/{SLUG} (private)'); os.remove(tgz)


def restore():
    owner = user()
    raw = call('GET', f'/datasets/download/{owner}/{SLUG}', raw=True)   # a zip holding tpl.tgz
    z = zipfile.ZipFile(io.BytesIO(raw)); os.makedirs(TPL, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(z.read('tpl.tgz'))) as t: t.extractall(TPL)
    print('restored ->', TPL, os.listdir(TPL))


if __name__ == '__main__':
    {'backup': backup, 'restore': restore}[sys.argv[1]]()
