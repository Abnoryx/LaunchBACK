"""Describe every library shot once with CLIP ViT-B/32 (OpenAI weights == open_clip 'ViT-B-32/openai'), on this CPU.
Per shot: image embeddings of its 3 preview key frames + text embeddings of its on-screen words and of its notes
(two short captions, zero rows when empty), plus how
bright it is (paper vs dark world). Cached; only new or changed shots are recomputed.
  ours -> library/previews/embed.npz      bought scenes -> /home/user/tpl/previews/embed.npz (private)
The model runs from ONNX (no torch here; Hugging Face is blocked from this container): exported once on Kaggle by
kgl/jobs/clip_export.py (kernel 'clip-export') and cached in ~/.cache/launchback/clip.
usage: python3 -m gen.embed          (update the caches)"""
import hashlib, json, os, sys, urllib.request
import numpy as np
from PIL import Image
from . import library as LIB
MODEL = os.path.expanduser('~/.cache/launchback/clip')
FILES = ('clip_text.onnx', 'clip_image.onnx', 'clip_tokenizer.json')
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073], 'f4'), np.array([0.26862954, 0.26130258, 0.27577711], 'f4')
_s = {}


def ensure():
    """Download the exported model from the Kaggle kernel's output the first time (per container)."""
    if all(os.path.exists(os.path.join(MODEL, f)) for f in FILES): return
    sys.path.insert(0, LIB.VID); from kgl.run import call, user
    out = call('GET', f'/kernels/output?userName={user()}&kernelSlug=clip-export'); os.makedirs(MODEL, exist_ok=True)
    got = {f['fileName'][4:]: f['url'] for f in out.get('files', []) if f['fileName'].startswith('out/')}
    if not all(f in got for f in FILES):
        sys.exit('CLIP model not exported yet: python3 -m kgl.run kgl/jobs/clip_export.py <out> <any.png> --name clip-export --no-gpu')
    for f in FILES: urllib.request.urlretrieve(got[f], os.path.join(MODEL, f))


def _sess(name):
    if name not in _s:
        ensure(); import onnxruntime as ort
        _s[name] = ort.InferenceSession(os.path.join(MODEL, f'clip_{name}.onnx'), providers=['CPUExecutionProvider'])
    return _s[name]


def _norm(x): return (x / np.linalg.norm(x, axis=-1, keepdims=True)).astype('f4')


def text(texts):
    """(n, 512) unit vectors."""
    from tokenizers import Tokenizer
    if 'tok' not in _s: ensure(); _s['tok'] = Tokenizer.from_file(os.path.join(MODEL, 'clip_tokenizer.json'))
    ids = np.full((len(texts), 77), 49407, 'i8'); mask = np.zeros((len(texts), 77), 'i8')
    for i, t in enumerate(texts):
        e = _s['tok'].encode(t).ids
        if len(e) > 77: e = e[:76] + [49407]   # keep the end token (CLIP pools there)
        ids[i, :len(e)] = e; mask[i, :len(e)] = 1
    return _norm(np.concatenate([_sess('text').run(None, {'input_ids': ids[i:i + 32], 'attention_mask': mask[i:i + 32]})[0]
                                 for i in range(0, len(texts), 32)]))


def _px(im):   # CLIP preprocessing: shortest side 224 (bicubic), centre crop, normalise
    im = im.convert('RGB'); w, h = im.size; s = 224 / min(w, h)
    im = im.resize((max(224, round(w * s)), max(224, round(h * s))), Image.BICUBIC); w, h = im.size
    l, t = (w - 224) // 2, (h - 224) // 2; a = np.asarray(im.crop((l, t, l + 224, t + 224)), 'f4') / 255
    return ((a - MEAN) / STD).transpose(2, 0, 1)


def image(ims):
    return _norm(_sess('image').run(None, {'pixel_values': np.stack([_px(i) for i in ims])})[0])


def frames(jpg):
    """The 3 key frames of a preview strip."""
    im = Image.open(jpg); w = im.width // 3
    return [im.crop((i * w, 0, (i + 1) * w, im.height)) for i in range(3)]


def _sig(e):
    j = e['preview'] + '.jpg'
    return hashlib.sha1(('|'.join(LIB.describe(e)) + (f'|{os.path.getsize(j)}|{os.path.getmtime(j)}' if os.path.exists(j) else '|none')).encode()).hexdigest()[:16]


def _cache(private): return os.path.join(LIB.PREV_PRIVATE if private else LIB.PREV, 'embed.npz')


def _read(p):
    if not os.path.exists(p): return {}
    z = np.load(p)
    return {i: dict(sig=s, txt=z['txt'][k], img=z['img'][k], has_img=bool(z['has_img'][k]), light=float(z['light'][k]))
            for k, (i, s) in enumerate(zip(z['ids'], z['sigs']))}


def update(S=None, quiet=False):
    """Embed new/changed shots; returns id -> {txt (2,512: words, notes), img (3,512), has_img, light}."""
    S = S or LIB.shots(); out = {}
    for private in (False, True):
        es = [e for e in S.values() if e['private'] == private]
        if not es: continue
        old = _read(_cache(private)); new = {}
        todo = [e for e in es if old.get(e['id'], {}).get('sig') != _sig(e)]
        caps = [c for e in todo for c in LIB.describe(e)]; idx = [i for i, c in enumerate(caps) if c]
        T = np.zeros((len(caps), 512), 'f4')
        if idx: T[idx] = text([caps[i] for i in idx])
        for n, e in enumerate(todo):
            r = dict(sig=_sig(e), txt=T[2 * n:2 * n + 2], img=np.zeros((3, 512), 'f4'), has_img=False, light=-1.0)
            if LIB.has_preview(e):
                fr = frames(e['preview'] + '.jpg'); r.update(img=image(fr), has_img=True,
                                                             light=float(np.mean([np.asarray(f.convert('L'), 'f4').mean() / 255 for f in fr])))
            new[e['id']] = r
        keep = {e['id']: new.get(e['id']) or old[e['id']] for e in es}
        if todo:
            os.makedirs(os.path.dirname(_cache(private)), exist_ok=True); ids = sorted(keep)
            np.savez(_cache(private), ids=np.array(ids), sigs=np.array([keep[i]['sig'] for i in ids]), txt=np.stack([keep[i]['txt'] for i in ids]),
                     img=np.stack([keep[i]['img'] for i in ids]), has_img=np.array([keep[i]['has_img'] for i in ids]),
                     light=np.array([keep[i]['light'] for i in ids], 'f4'))
            if not quiet: print(f"embedded {len(todo)} {'bought' if private else 'our'} shot(s)")
        out.update(keep)
    return out


if __name__ == '__main__':
    E = update(); print(f'{len(E)} shots described, {sum(e["has_img"] for e in E.values())} from preview frames')
