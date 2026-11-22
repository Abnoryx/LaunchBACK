import {makeShot} from './shot.mjs';
import {createScene} from './scene.mjs';

const capture = new URLSearchParams(location.search).has('capture');
document.body.classList.toggle('capture', capture);
const response = await fetch('/shot.json', {cache:'no-store'});
if (!response.ok) throw new Error('Could not load shot.json.');
const shot = makeShot(await response.json());
const canvas = document.querySelector('canvas');
const {renderFrame} = await createScene(canvas, shot);
const slider = document.querySelector('input');
const output = document.querySelector('output');
const button = document.querySelector('button');
slider.max = shot.frameCount - 1;
let index = 0;
let playing = false;
let origin = 0;

function seek(frame) {
  const state = renderFrame(frame);
  index = frame;
  slider.value = String(frame);
  output.value = (frame + 1) + ' / ' + shot.frameCount;
  return state.sourceFrame;
}
function animate(now) {
  if (!playing) return;
  const next = Math.floor((now - origin) * shot.fps / 1000) % shot.frameCount;
  if (next !== index) seek(next);
  requestAnimationFrame(animate);
}
slider.addEventListener('input', () => {
  playing = false;
  button.textContent = 'Play';
  seek(slider.valueAsNumber);
});
button.addEventListener('click', () => {
  playing = !playing;
  button.textContent = playing ? 'Pause' : 'Play';
  if (playing) {
    origin = performance.now() - index * 1000 / shot.fps;
    requestAnimationFrame(animate);
  }
});
window.renderFrame = seek;
window.captureFrame = (frame) => {
  seek(frame);
  return canvas.toDataURL('image/png').split(',')[1];
};
seek(0);
window.shotReady = true;
if (!capture) button.click();
