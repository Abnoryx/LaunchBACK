"""Audio for the 10 s test: our VO + the OG's music bed (12 LU under VO, no ducking) + the OG's SFX at their
reel onsets mapped through the same shot time map as the picture.  usage: python3 mix_10s.py <assets> <psych_footage> <out.wav>"""
import subprocess
import sys

A, PS, OUT = sys.argv[1:4]
FX = f"{PS}/(Footage)"
SEG = [(0.000, 3.233, 0.00, 2.70), (3.233, 4.733, 2.70, 3.68), (8.300, 11.500, 3.68, 5.95), (11.500, 15.567, 5.95, 9.25)]
DUR = 9.25


def omap(t):
    for a, b, x, y in SEG:
        if a - 0.3 <= t <= b + 0.05:
            return x + (t - a) * (y - x) / (b - a)
    return None


# OG SFX onsets measured in the reel (research/shots_d), file, gain dB, max seconds
OG = [(0.43, "VS_Short Whoosh 5.mp3", -2, None), (1.38, "Radio.mp3", -4, None),
      (1.61, "micro-air-swoosh_G18j6H4u.mp3", -3, None), (3.69, "vibrant hit.mp4", -7, 1.6),
      (8.44, "Radio.mp3", -4, None), (9.39, "Swoosh.wav", 0, None), (12.14, "Radio.mp3", -4, None),
      (12.71, "micro-air-swoosh_G18j6H4u.mp3", -3, None), (13.48, "Whoosh Fast 02.wav", 0, None),
      (13.75, "Riser.wav", -8, 3.0), (14.15, "Whoosh Fast 01.wav", -2, None)]
cues = [(omap(t), f, g, d) for t, f, g, d in OG if omap(t) is not None]
cues += [(2.62, "Whoosh Fast 02.wav", -2, None), (5.90, "VS_Short Whoosh 1.mp3", -3, None), (9.12, "Hit 3.mp3", -4, 2.0)]

inp = ["-i", f"{A}/audio/vo_edit.wav", "-ss", "6.97", "-i", f"{FX}/2025-09-26 21-45-26.mp4"]
flt = ["[0:a]atrim=0:9.25,aresample=48000,pan=stereo|c0=c0|c1=c0,loudnorm=I=-14.7:TP=-2:LRA=7[vo]",
       "[1:a]atrim=0:9.25,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26.3:LRA=7,afade=t=in:d=0.05[mu]"]
for k, (t, f, g, d) in enumerate(cues, 2):
    inp += ["-i", f"{FX}/{f}"]
    tr = f"atrim=0:{d},afade=t=out:st={d - 0.15}:d=0.15," if d else ""
    ms = int(max(0, t) * 1000)
    flt.append(f"[{k}:a]{tr}aresample=48000,aformat=channel_layouts=stereo,volume={g - 6}dB,adelay={ms}|{ms}[s{k}]")
ins = "[vo][mu]" + "".join(f"[s{k}]" for k in range(2, len(cues) + 2))
flt.append(f"{ins}amix=inputs={len(cues) + 2}:normalize=0:duration=first,alimiter=limit=0.89,loudnorm=I=-14:TP=-1:LRA=7[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(flt), "-map", "[out]", "-t", str(DUR), "-ar", "48000", OUT], check=True)
print(len(cues), "sfx cues ->", OUT)
