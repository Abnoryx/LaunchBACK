# rescene OCR stage on Kaggle. Inputs: extract/ (code), reel.mp4, measure.json. Output: $OUT/ocr.json
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rapidocr', 'onnxruntime', 'opencv-python-headless'], check=True)
import json; sys.path.insert(0, '.')
from extract.text import ocr_frames
m = json.load(open('measure.json'))
o = ocr_frames('reel.mp4', m['signals']['mad'], m['cuts'])
json.dump(o, open(os.path.join(os.environ['OUT'], 'ocr.json'), 'w'), default=float)
print('ocr frames', len(o))
