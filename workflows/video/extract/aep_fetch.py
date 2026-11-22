"""Route A step 0: get a project zip (.aep + footage) by file name from the user's MEGA folder.
usage: python3 -m extract.aep_fetch "<zip name>"      e.g. "The-Generation-Effect-Edit.zip"
       python3 -m extract.aep_fetch --list
Uses /home/user/tpl/zips/<name> when it is already there (restored from the Kaggle backup); otherwise downloads just
that file with megadl (apt-get install -y megatools). Then unzip into /home/user/tpl/src/<project>/ and run step 1."""
import os, re, subprocess, sys

MEGA = 'https://mega.nz/folder/InRm3CQT#xF_C5lxUl2l7TzSSyA_IzQ'   # user's folder of bought project zips
ZIPS = '/home/user/tpl/zips'


def listing():
    """[(number, name)] as megadl --choose-files numbers them."""
    r = subprocess.run(['megadl', '--no-ask-password', '--choose-files', '--path', '/tmp', MEGA], input='\n',
                       capture_output=True, text=True, timeout=180)
    return [(int(n), s.strip()) for n, s in re.findall(r'(\d+)\. ([^\n(]+?)(?: \([^)]*\))?\n', r.stdout + r.stderr)]


def fetch(name):
    os.makedirs(ZIPS, exist_ok=True)
    dst = os.path.join(ZIPS, name)
    if os.path.exists(dst): return dst
    items = listing()
    hit = [n for n, s in items if s == name] or [n for n, s in items if name.lower() in s.lower()]
    if len(hit) != 1: sys.exit(f'{name!r}: {len(hit)} matches in MEGA folder: {[s for _, s in items]}')
    subprocess.run(['megadl', '--no-ask-password', '--no-progress', '--choose-files', '--path', ZIPS, MEGA],
                   input=f'{hit[0]}\n', text=True, check=True, timeout=3600)
    return dst


if __name__ == '__main__':
    if sys.argv[1:] == ['--list']: [print(n, s) for n, s in listing()]
    else: print(fetch(sys.argv[1]))
