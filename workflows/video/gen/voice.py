"""Voice-over in the user's cloned ElevenLabs voice, with word timestamps (so shots are timed to the VO before build).
usage: python3 -m gen.voice <script.txt> <out_dir>   -> vo.mp3 + words.json [{word, start, end}]
Setup (once): user connects ElevenLabs; the API key is saved via the secure credential form for api.elevenlabs.io
(header xi-api-key, injected by the proxy — never in chat or git); put the cloned voice_id in gen/config.json."""
import base64, json, os, sys, urllib.request
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))['voice']


def words_from_alignment(al):
    out, cur, t0 = [], '', None
    for ch, s, e in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if ch.isspace():
            if cur: out.append(dict(word=cur, start=t0, end=prev_e)); cur = ''
            continue
        if not cur: t0 = s
        cur += ch; prev_e = e
    if cur: out.append(dict(word=cur, start=t0, end=prev_e))
    return out


def speak(text, out_dir):
    if not CFG.get('voice_id'): sys.exit('set voice.voice_id in gen/config.json (the cloned voice) first')
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{CFG['voice_id']}/with-timestamps", method='POST',
                                 headers={'xi-api-key': 'proxy-injected', 'Content-Type': 'application/json'},
                                 data=json.dumps(dict(text=text, model_id=CFG['model'])).encode())
    d = json.load(urllib.request.urlopen(req, timeout=300)); os.makedirs(out_dir, exist_ok=True)
    open(f'{out_dir}/vo.mp3', 'wb').write(base64.b64decode(d['audio_base64']))
    w = words_from_alignment(d['alignment']); json.dump(w, open(f'{out_dir}/words.json', 'w'), indent=1)
    return w


if __name__ == '__main__':
    print(len(speak(open(sys.argv[1]).read(), sys.argv[2])), 'words')
