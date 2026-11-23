const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const mix = (start, end, progress) => start + (end - start) * progress;
const smooth = (progress) => progress * progress * (3 - 2 * progress);
const rise = (frame, start, end) => smooth(clamp((frame - start) / Math.max(end - start, 0.01)));

function merge(base, overrides) {
  const result = {...base};
  for (const [key, value] of Object.entries(overrides)) {
    result[key] = value && typeof value === 'object' && !Array.isArray(value)
      ? merge(base[key], value) : value;
  }
  return result;
}

function locate(keys, frame) {
  const last = keys.length - 1;
  if (frame <= keys[0][0]) return [keys[0], keys[0], 0];
  if (frame >= keys[last][0]) return [keys[last], keys[last], 0];
  const index = keys.findIndex(([at]) => at > frame);
  const start = keys[index - 1];
  const end = keys[index];
  return [start, end, (frame - start[0]) / (end[0] - start[0])];
}

function valuesAt(keys, frame) {
  const [start, end, weight] = locate(keys, frame);
  return start.slice(1).map((value, i) => mix(value, end[i + 1], weight));
}

function waveAt(keys, heights, frame, feather, opacity) {
  const [start, end, weight] = locate(keys, frame);
  const side = (index) => heights.map((height, i) => [
    height, mix(start[index][i], end[index][i], weight),
  ]);
  return {
    left: side(1), right: side(2), feather,
    opacity: frame >= keys[0][0] ? valuesAt(opacity, frame)[0] : 0,
    visible: frame >= keys[0][0],
  };
}

// Monotone Hermite between measured scanlines. A change of slope at a turning
// point has a flat tangent, keeping the two boundaries from oscillating.
export function sampleEdge(points, y) {
  if (y <= points[0][0]) return points[0][1];
  if (y >= points.at(-1)[0]) return points.at(-1)[1];
  const index = points.findIndex(([height]) => height > y);
  const a = points[index - 1];
  const b = points[index];
  const prev = points[index - 2] ?? a;
  const next = points[index + 1] ?? b;
  const span = b[0] - a[0];
  const slope = (b[1] - a[1]) / span;
  const previousSlope = prev === a ? slope : (a[1] - prev[1]) / (a[0] - prev[0]);
  const nextSlope = next === b ? slope : (next[1] - b[1]) / (next[0] - b[0]);
  const tangent = (side) => slope * side <= 0 ? 0 : 2 * slope * side / (slope + side);
  const u = (y - a[0]) / span;
  const h = u * (1 - u);
  return mix(a[1], b[1], smooth(u)) + span * h * ((1 - u) * tangent(previousSlope) - u * tangent(nextSlope));
}

export function wavePolygon(wave, height) {
  const ys = Array.from({length: Math.ceil(height / 8) + 5}, (_, index) => (index - 2) * 8);
  return [
    ...ys.map((y) => [sampleEdge(wave.left, y), y]),
    ...ys.reverse().map((y) => [sampleEdge(wave.right, y), y]),
  ];
}

function wrappedLines(text, limit) {
  const lines = [''];
  for (const word of text.split(/\s+/)) {
    const index = lines.length - 1;
    if (lines[index] && lines[index].length + word.length + 1 > limit) lines.push(word);
    else lines[index] = lines[index] ? lines[index] + ' ' + word : word;
  }
  return lines;
}

const image = (id, asset, x, y, width, height, rest = {}) =>
  ({kind: 'image', id, asset, x, y, width, height, opacity: 1, ...rest});
const copy = (id, text, style, rest = {}) =>
  ({kind: 'text', id, text, opacity: 1, angle: 0, align: 'left', ...style, ...rest});
const polygon = (id, points, color, rest = {}) =>
  ({kind: 'polygon', id, points, color, opacity: 1, ...rest});

function renderState(sourceFrame, config, white, dark) {
  const {layout, timing, words, assets, width, height} = config;
  const f = sourceFrame;
  const ctaAlpha = 1 - rise(f, ...timing.ctaOut);
  const [gripX, gripY, handAngle, needleAngle, upper, lower] = valuesAt(layout.arm, f - timing.armOffset);
  const [titleX, titleY, bigNudgeX] = valuesAt(layout.title, f);
  const {hand, logo} = layout;
  const armAlpha = f - timing.armOffset < layout.arm[0][0] ? 0 : 1;
  const finish = 1 - rise(f, ...timing.finishOut);
  const layers = [
    polygon('background', [[0,0],[width,0],[width,height],[0,height]], layout.bg),
    image('plate', assets.plate, width / 2, height / 2, width, height, {opacity: finish}),
  ];
  layers.push(image('logo', assets.logo, logo.x, logo.y, logo.width, logo.height, {angle: -9, opacity: .73 * ctaAlpha}));
  layout.pens.forEach(([x,y,w,h,angle], i) => {
    layers.push(image('pen ' + (i + 1), assets.pen, x, y, w, h, {angle, opacity: .8 * ctaAlpha}));
  });
  layers.push(
    copy('follow', words.cta, layout.cta, {color: layout.ink, align: 'center', opacity: ctaAlpha}),
    copy('insight', words.accent, layout.accentText, {color: layout.accent, align: 'center', opacity: ctaAlpha}),
    {kind: 'wave', id: 'white wave', ...white, color: layout.waveWhite, halo: config.wave.whiteHalo * white.spread},
  );

  const radians = needleAngle * Math.PI / 180;
  const downX = -Math.sin(radians);
  const downY = Math.cos(radians);
  const revealNeedle = .55 + .33 * rise(f, 888, 895);
  const half = 6.3;
  const vector = [
    [gripX - upper * downX - half * downY, gripY - upper * downY + half * downX],
    [gripX - upper * downX + half * downY, gripY - upper * downY - half * downX],
    [gripX + (lower - 40) * downX + half * downY, gripY + (lower - 40) * downY - half * downX],
    [gripX + lower * downX, gripY + lower * downY],
    [gripX + (lower - 40) * downX - half * downY, gripY + (lower - 40) * downY + half * downX],
  ];
  const transition = Math.abs(handAngle) > 3 ? .78 : 1;
  layers.push(polygon('needle', vector, layout.needle, {opacity: revealNeedle * armAlpha}));
  layers.push(image('arm', assets.hand, gripX, gripY, hand.width, hand.height, {
    angle: handAngle, anchor: [hand.gripU, hand.gripV], opacity: transition * armAlpha,
  }));

  const [lead, ...tail] = words.small.split('\n');
  const [firstWord = '', ...lastWords] = (tail.join(' ').trim()).split(/\s+/);
  const [thatIn, moveIn, restIn] = timing.small;
  const small = {color: layout.ink, blend: 'exclusion'};
  layers.push(
    copy('intro', lead, layout.small, {...small, x: titleX, y: titleY, size: layout.small.thatSize, opacity: rise(f, thatIn - .7, thatIn + 1.5)}),
    copy('move', firstWord, layout.small, {...small, x: titleX, y: titleY + layout.small.lineGap, opacity: rise(f, moveIn - .8, moveIn + 1.4)}),
    copy('move tail', lastWords.join(' '), layout.small, {...small, x: titleX, y: titleY + layout.small.lineGap, after: firstWord + ' ', opacity: rise(f, restIn - 1, restIn + 4)}),
    copy('headline', words.big, layout.big, {...small, x: layout.big.x + bigNudgeX, opacity: rise(f, ...timing.big)}),
  );

  layers.push(copy('watermark', words.watermark, layout.mark, {
    color: '#56724b', align: 'center', opacity: .86,
  }));
  wrappedLines(words.fineprint, 49).forEach((line, index) => {
    layers.push(copy('fine print ' + index, line, layout.fine, {
      y: layout.fine.y + index * 9, color: '#818886', align: 'center', opacity: .29,
    }));
  });
  for (const [index, y] of [359, 1109].entries()) {
    layers.push(copy('film stock ' + index, 'KODAK PORTRA 400', {
      x: 81, y, angle: -90, size: 20, font: 'Arimo Bold', tracking: 177, color: '#ba8554', opacity: .88,
    }));
  }
  for (const [index, y] of [529, 892, 1277].entries()) {
    layers.push(copy('film count ' + index, ['43', '9', '12'][index], {
      x: 80, y, angle: -90, size: 15, font: 'Arimo Bold', tracking: 140, color: '#ad895b', opacity: .77,
    }));
  }
  for (const [i, y] of [64, 485, 916].entries()) {
    layers.push(polygon('film mark ' + i, [[678,y+8],[687,y+8],[682,y-10]], '#ffbb49', {opacity: .86}));
  }
  layers.push({kind: 'wave', id: 'dark wipe', ...dark, color: layout.waveDark});
  return {sourceFrame, white, dark, layers};
}

export function makeShot(defaults, overrides = {}) {
  const config = merge(defaults, overrides);
  const {width, height, fps, sourceStart, frameCount, wave, timing} = config;
  function at(frameIndex) {
    if (!Number.isInteger(frameIndex) || frameIndex < 0 || frameIndex >= frameCount) {
      throw new RangeError('Frame index is outside the shot.');
    }
    const f = sourceStart + frameIndex;
    const whiteFrame = f - timing.whiteOffset;
    const spread = valuesAt(wave.whiteSpread, whiteFrame)[0];
    const white = {...waveAt(wave.white, wave.heights, whiteFrame, wave.whiteFeather * spread, wave.whiteOpacity), spread};
    const darkFrame = f - timing.darkOffset;
    const darkSpread = valuesAt(wave.darkSpread, darkFrame)[0];
    const dark = waveAt(wave.dark, wave.heights, darkFrame, wave.darkFeather * darkSpread, timing.darkOpacity);
    return renderState(f, config, white, dark);
  }
  return {config, width, height, fps, frameCount, at};
}
