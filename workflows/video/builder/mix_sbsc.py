"""Sound design for 'Same recipes' following The Psychology Trick's cue grammar; mixes VO + SFX to -14 LUFS.
usage: python3 mix_sbsc.py <assets_dir> <psych_footage_dir> <out.wav>"""
import json
import subprocess
import sys

A, PS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FX = f"{PS}/(Footage)"
F = 1 / 30
words = json.load(open(f"{A}/audio/vo_edit_words.json"))


def at(w, n=0):
    k = 0
    for s, e, x in words:
        if x.lower().strip(".,?!") == w:
            if k == n:
                return s
            k += 1
    raise KeyError(w)


CUT = [1.30, 2.70, 3.55, 5.95, 9.20, 10.90, 12.60, 15.70, 17.85, 20.30, 21.85]
cues = []  # (time, file, gain_db, max_dur)
whooshes = ["VS_Short Whoosh 1.mp3", "Whoosh Fast 02.wav", "VS_Short Whoosh 2.mp3", "Whoosh Fast 01.wav", "VS_Short Whoosh 5.mp3"]
for i, t in enumerate(CUT):            # stacked whoosh landing on the cut + radio blip
    cues.append((t - 0.30, whooshes[i % len(whooshes)], -4, None))
    cues.append((t - 0.12, "Swoosh.wav", -6, None))
    cues.append((t, "Radio.mp3", -10, None))
cues += [(0.0, "VS_Short Whoosh 5.mp3", -3, None),                    # open
         (at("both") - 4 * F, "Marker.mp3", -2, None),                 # highlight boxes
         (at("free", 1) - 4 * F, "Marker.mp3", -2, None),
         (at("use") - 4 * F, "Marker.mp3", -2, None),
         (3.82, "Typewriter Sound Effect.mp3", -8, 0.9),                # first line of S4
         (6.13, "Typewriter Sound Effect.mp3", -10, 0.8),               # "He says..."
         (at("are"), "micro-air-swoosh_G18j6H4u.mp3", -4, None),        # phone pop on the flip
         (at("all") - 0.25, "paper flapping.mp4", -6, 1.4),             # pages fly into the book
         (12.50, "Riser.wav", -9, 3.2),                                 # riser into the 15.7 slam
         (at("same"), "Hit 3.mp3", -4, 4.0),                            # SAME reveal
         (at("why") - 0.02, "Radio.mp3", -6, None)]

inputs, filters = ["-i", f"{A}/audio/vo_edit.wav"], ["[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,volume=0dB[vo]"]
for k, (t, f, g, d) in enumerate(cues, 1):
    inputs += ["-i", f"{FX}/{f}"]
    trim = f"atrim=0:{d}," if d else ""
    fade = f"afade=t=out:st={max(0, (d or 9) - 0.15)}:d=0.15," if d else ""
    filters.append(f"[{k}:a]{trim}{fade}aresample=48000,aformat=channel_layouts=stereo,volume={g}dB,adelay={int(max(0, t) * 1000)}|{int(max(0, t) * 1000)}[s{k}]")
mixin = "[vo]" + "".join(f"[s{k}]" for k in range(1, len(cues) + 1))
filters.append(f"{mixin}amix=inputs={len(cues) + 1}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-t", "24.4", "-ar", "48000", OUT]
subprocess.run(cmd, check=True)
print("mixed", len(cues), "cues ->", OUT)
