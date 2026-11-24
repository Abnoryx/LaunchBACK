"""Concatenate the rendered scenes (NN.mp4) in original order, no effects, no trimming: the original handoffs stay.
usage: stitch.py <dir> <out.mp4>"""
import glob, os, subprocess, sys
d, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); fs = sorted(glob.glob(f'{d}/[0-9][0-9].mp4'))
open(f'{d}/list.txt', 'w').write('\n'.join(f"file '{f}'" for f in fs))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{d}/list.txt', '-vf', 'scale=540:960,fps=30', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out], check=True)
print(len(fs), 'scenes ->', out)
