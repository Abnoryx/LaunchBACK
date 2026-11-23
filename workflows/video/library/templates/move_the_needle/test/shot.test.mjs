import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {makeShot, sampleEdge} from '../src/shot.mjs';

const config = JSON.parse(readFileSync(new URL('../shot.json', import.meta.url)));

test('source window maps to all 51 deterministic portrait frames', () => {
  const shot = makeShot(config);
  assert.equal(shot.frameCount, 51);
  assert.deepEqual([shot.width, shot.height, shot.fps], [720, 1280, 30]);
  assert.equal(shot.at(0).sourceFrame, 883);
  assert.equal(shot.at(50).sourceFrame, 933);
  assert.deepEqual(shot.at(17), shot.at(17));
  assert.throws(() => shot.at(51), RangeError);
});

test('the white seam opens unevenly and the dark wipe covers the last frame', () => {
  const shot = makeShot(config);
  assert.equal(shot.at(3).white.visible, false);
  const opening = shot.at(4).white;
  const open = shot.at(13).white;
  assert(opening.visible && open.visible);
  assert(sampleEdge(open.right, 0) - sampleEdge(open.left, 0) > 430);
  assert(sampleEdge(open.right, 1200) - sampleEdge(open.left, 1200) < 50);
  assert(Math.abs(sampleEdge(opening.left, 0) - sampleEdge(opening.left, 160)) > 15);
  const closed = shot.at(50).dark;
  assert(closed.visible);
  for (const y of [0, 320, 640, 960, 1279]) {
    assert(sampleEdge(closed.left, y) < 0);
    assert(sampleEdge(closed.right, y) > 720);
  }
});

test('copy and wave timing overrides alter the shared frame state', () => {
  const shot = makeShot(config, {words:{big:'Signal'}, timing:{whiteOffset:2}});
  assert.equal(shot.config.words.big, 'Signal');
  assert.equal(shot.at(4).white.visible, false);
  assert.equal(shot.at(6).white.visible, true);
  assert.equal(makeShot(config).config.words.big, 'Needle');
});
