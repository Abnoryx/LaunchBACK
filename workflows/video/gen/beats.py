"""Script -> beats (1-5 on-screen words each, text = VO) with estimated or voice-timed seconds.
usage: python3 -m gen.beats <script.txt> [--words words.json]   (words.json: [{word, start, end}] from gen.voice)"""
import json, os, re, sys
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))


def beats(script, words=None, max_words=None):
    max_words = max_words or CFG['rules']['max_words_per_beat']
    sents = [s.strip() for s in re.split(r'(?<=[.!?:])\s+', script.strip()) if s.strip()]
    out = []
    for si, s in enumerate(sents):
        toks = s.split()
        # break long sentences at commas first, then every max_words
        chunks, cur = [], []
        for t in toks:
            cur.append(t)
            if len(cur) >= max_words or t.endswith(','):
                chunks.append(cur); cur = []
        if cur:
            if chunks and len(cur) < 3 and len(chunks[-1]) + len(cur) <= max_words + 2: chunks[-1] += cur   # no dangling tails
            else: chunks.append(cur)
        for ci, c in enumerate(chunks):
            out.append(dict(text=' '.join(c), sentence=si, first_in_sentence=ci == 0))
    # timing: voice word onsets if given, else words/second
    if words:
        i = 0
        for b in out:
            n = len(b['text'].split()); b['start'] = words[i]['start']; b['end'] = words[min(i + n, len(words)) - 1]['end']; i += n
    else:
        t = 0.0; wps = CFG['words_per_second']
        for b in out:
            d = max(len(b['text'].split()) / wps, 0.6); b['start'], b['end'] = round(t, 2), round(t + d, 2); t += d
    if out:
        out[0]['role'] = 'hook'; out[-1]['role'] = 'payoff'
    return out


if __name__ == '__main__':
    w = json.load(open(sys.argv[sys.argv.index('--words') + 1])) if '--words' in sys.argv else None
    print(json.dumps(beats(open(sys.argv[1]).read(), w), indent=1))
