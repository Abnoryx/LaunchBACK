"""Stage 0: probe the reel, decode a small BT.709-correct analysis stack (uint8 .npy) + mono 16 kHz audio.
Frames are decoded once; every later stage reads frames.npy (N, H, W, 3)."""
import json, os, subprocess
import numpy as np


def probe(src):
    j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', src]))
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    num, den = map(int, v['r_frame_rate'].split('/'))
    pts = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time',
                                   '-of', 'csv=p=0', src]).decode().split()
    pts = [float(p.strip(',')) for p in pts if p.strip(', ') not in ('', 'N/A')]   # some muxers print 'x,' (side data column)
    d = np.diff(pts) if len(pts) > 1 else np.array([den / num])
    return dict(w=int(v['width']), h=int(v['height']), fps=num / den, frames=len(pts), dur=float(j['format']['duration']),
                vfr=bool(len(d) and (d.max() - d.min()) > 0.25 * np.median(d)), color_space=v.get('color_space', '?'),
                audio=any(s['codec_type'] == 'audio' for s in j['streams']), pts=pts)


def ingest(src, out, width=216):
    os.makedirs(out, exist_ok=True)
    info = probe(src)
    h = int(round(info['h'] * width / info['w'] / 2) * 2)
    cm = 'bt709' if info['color_space'] in ('bt709', '?', 'unknown') else 'bt601'
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', src, '-vsync', 'passthrough', '-vf',
                                   f'scale={width}:{h}:in_color_matrix={cm}:flags=area,format=rgb24', '-f', 'rawvideo', '-'])
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, width, 3)
    np.save(os.path.join(out, 'frames.npy'), fr)
    if info['audio']:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', os.path.join(out, 'audio.wav')], check=True)
    info.update(analysis_w=width, analysis_h=h, decoded=len(fr), scale_to_1080=1080 / width)
    json.dump({k: v for k, v in info.items() if k != 'pts'}, open(os.path.join(out, 'info.json'), 'w'), indent=1)
    np.save(os.path.join(out, 'pts.npy'), np.array(info['pts']))
    return info, fr
