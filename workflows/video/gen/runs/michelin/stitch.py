"""Stitch work/<round>/NN.mp4 in plan order into <out>.mp4 (hard concat; the templates carry their own whip-ins). usage: stitch.py <dir> <out.mp4>"""
import glob, os, subprocess, sys
d, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
fs = sorted(glob.glob(f'{d}/[0-9][0-9].mp4')); lst = f'{d}/list.txt'
open(lst, 'w').write('\n'.join(f"file '{f}'" for f in fs))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-vf', 'scale=540:960,fps=30', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out], check=True)
print(len(fs), 'shots ->', out)
