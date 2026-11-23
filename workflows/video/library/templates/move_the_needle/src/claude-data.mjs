import {readFileSync} from 'node:fs';
import {makeShot, wavePolygon} from './shot.mjs';

const config = JSON.parse(readFileSync(new URL('../shot.json', import.meta.url), 'utf8'));
const input = readFileSync(0, 'utf8');
const shot = makeShot(config, input ? JSON.parse(input) : {});
const frames = Array.from({length:shot.frameCount}, (_, frame) =>
  shot.at(frame).layers.map((layer) => {
    if (layer.kind === 'wave') {
      const {left, right, visible, ...style} = layer;
      return {...style, points: wavePolygon({left,right}, shot.height)};
    }
    return layer;
  }),
);
process.stdout.write(JSON.stringify({
  width: shot.width, height: shot.height, fps: shot.fps, frameCount: shot.frameCount, frames,
}));
