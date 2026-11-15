// Keyframe + expression evaluation with After Effects semantics.
// Property node shape (from the .aep dump): {n, m, v?, k?: [{t, v, in, out, ie, oe, in_st?, out_st?}], x?}
// Interpolation codes: 6612 LINEAR, 6613 BEZIER, 6614 HOLD.

export const HOLD = 6614;

const isArr = Array.isArray;
const add = (a, b) => (isArr(a) ? a.map((x, i) => x + (isArr(b) ? b[i] : b)) : a + b);
const sub = (a, b) => (isArr(a) ? a.map((x, i) => x - (isArr(b) ? b[i] : b)) : a - b);
const mul = (a, s) => (isArr(a) ? a.map((x) => x * s) : a * s);
const len = (a) => Math.hypot(...a);

// Solve a 1D cubic bezier x(u)=x for u in [0,1] (x monotonic in time).
function solveU(x0, x1, x2, x3, x) {
  let lo = 0, hi = 1, u = (x - x0) / (x3 - x0 || 1);
  for (let i = 0; i < 40; i++) {
    const xu = cub(x0, x1, x2, x3, u);
    if (Math.abs(xu - x) < 1e-7) break;
    if (xu < x) lo = u; else hi = u;
    u = (lo + hi) / 2;
  }
  return u;
}
const cub = (a, b, c, d, u) => {
  const m = 1 - u;
  return m * m * m * a + 3 * m * m * u * b + 3 * m * u * u * c + u * u * u * d;
};

// AE temporal ease as a value curve between two keys, for one dimension.
function ease1(t, t0, t1, v0, v1, oe, ie) {
  const dt = t1 - t0;
  const io = Math.min(Math.max(oe[1], 0.1), 100) / 100, ii = Math.min(Math.max(ie[1], 0.1), 100) / 100;
  const x1 = t0 + dt * io, y1 = v0 + oe[0] * dt * io;
  const x2 = t1 - dt * ii, y2 = v1 - ie[0] * dt * ii;
  const u = solveU(t0, x1, x2, t1, t);
  return cub(v0, y1, y2, v1, u);
}

// Spatial path between two position keys, reparameterised by arc length.
function spatialPath(k0, k1) {
  const p0 = k0.v, p3 = k1.v;
  const p1 = add(p0, k0.out_st || p0.map(() => 0)), p2 = add(p3, k1.in_st || p3.map(() => 0));
  const N = 64, pts = [], acc = [0];
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    pts.push(p0.map((_, d) => cub(p0[d], p1[d], p2[d], p3[d], u)));
    if (i) acc.push(acc[i - 1] + len(sub(pts[i], pts[i - 1])));
  }
  const L = acc[N];
  return {
    L,
    at(s) {
      if (L < 1e-9) return p0.slice();
      s = Math.min(Math.max(s, 0), L);
      let i = 1;
      while (i < N && acc[i] < s) i++;
      const f = (s - acc[i - 1]) / (acc[i] - acc[i - 1] || 1);
      return add(pts[i - 1], mul(sub(pts[i], pts[i - 1]), f));
    },
  };
}

const pathCache = new WeakMap();
const SPATIAL = /ADBE Position$|ADBE Anchor Point|ADBE Vector Position|ADBE Vector Anchor|ADBE Text Position 3D|ADBE Text Anchor Point 3D|ADBE Vector Rect Position|ADBE Vector Ellipse Position/;

// Eased 0..1 fraction for keys whose dimensions share one ease; D = distance in speed units.
function magFrac(t, a, b, D) {
  if (D < 1e-9) return 0;
  const o = a.oe[0], i = b.ie[0];
  return ease1(t, a.t, b.t, 0, 1, [o[0] / D, o[1]], [i[0] / D, i[1]]);
}

// Orientation: AE interpolates rotations spherically.
const D2R = Math.PI / 180;
function eulerToQuat([x, y, z]) {
  // R = Rz * Ry * Rx  (X applied first)
  const cx = Math.cos(x * D2R / 2), sx = Math.sin(x * D2R / 2);
  const cy = Math.cos(y * D2R / 2), sy = Math.sin(y * D2R / 2);
  const cz = Math.cos(z * D2R / 2), sz = Math.sin(z * D2R / 2);
  return [
    cz * cy * cx + sz * sy * sx,
    cz * cy * sx - sz * sy * cx,
    cz * sy * cx + sz * cy * sx,
    sz * cy * cx - cz * sy * sx,
  ];
}
function quatToEuler([w, x, y, z]) {
  const sinp = 2 * (w * y - z * x);
  const ry = Math.abs(sinp) >= 1 ? Math.sign(sinp) * 90 : Math.asin(sinp) / D2R;
  const rx = Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)) / D2R;
  const rz = Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)) / D2R;
  return [rx, ry, rz].map((v) => (v + 360) % 360);
}
function angleBetween(a, b) {
  const q0 = eulerToQuat(a), q1 = eulerToQuat(b);
  const d = Math.min(1, Math.abs(q0.reduce((s, v, i) => s + v * q1[i], 0)));
  return (2 * Math.acos(d)) / D2R;
}
function slerpEuler(a, b, f) {
  const q0 = eulerToQuat(a);
  let q1 = eulerToQuat(b);
  let d = q0.reduce((s, v, i) => s + v * q1[i], 0);
  if (d < 0) { q1 = q1.map((v) => -v); d = -d; }
  let q;
  if (d > 0.9995) q = q0.map((v, i) => v + (q1[i] - v) * f);
  else {
    const th = Math.acos(d), s = Math.sin(th);
    q = q0.map((v, i) => (Math.sin((1 - f) * th) * v + Math.sin(f * th) * q1[i]) / s);
  }
  const n = Math.hypot(...q);
  return quatToEuler(q.map((v) => v / n));
}

// Raw keyframed value at time t (comp-local time of the layer's comp).
export function keyValue(prop, t) {
  const K = prop.k;
  if (!K || !K.length) return prop.v;
  if (t <= K[0].t) return K[0].v;
  if (t >= K[K.length - 1].t) return K[K.length - 1].v;
  let i = 0;
  while (i < K.length - 2 && t >= K[i + 1].t) i++;
  const a = K[i], b = K[i + 1];
  if (a.out === HOLD) return a.v;
  if (typeof a.v === 'number') return ease1(t, a.t, b.t, a.v, b.v, a.oe[0], b.ie[0]);
  if (!isArr(a.v)) return a.v; // text documents, shapes: step
  if (prop.m === 'ADBE Orientation') return slerpEuler(a.v, b.v, magFrac(t, a, b, angleBetween(a.v, b.v)));
  const spatial = a.oe.length === 1 && a.v.length >= 2 && SPATIAL.test(prop.m || '');
  if (!spatial && a.oe.length === 1 && a.v.length >= 2) {
    // One shared ease for all dimensions (colours, etc.): eased fraction along the straight line.
    const scale = /Color|-000[0-9]/.test(prop.m || '') && a.v.length === 4 ? 255 : 1;
    const f = magFrac(t, a, b, len(sub(b.v, a.v)) * scale);
    return add(a.v, mul(sub(b.v, a.v), f));
  }
  if (spatial) {
    let c = pathCache.get(a);
    if (!c) { c = spatialPath(a, b); pathCache.set(a, c); }
    const s = ease1(t, a.t, b.t, 0, c.L, a.oe[0], b.ie[0]);
    return c.at(s);
  }
  return a.v.map((v0, d) => ease1(t, a.t, b.t, v0, b.v[d], a.oe[d] || a.oe[0], b.ie[d] || b.ie[0]));
}

// ---------------------------------------------------------------- expressions
// The four reference projects use a small, known set of expressions. Each is
// recognised and implemented natively (AE overloads array arithmetic, so plain eval won't do).

function num(re, x, d) {
  const m = x.match(re);
  return m ? parseFloat(m[1]) : d;
}

// Deterministic smooth noise for wiggle().
function hash(n) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}
function noise1(x, seed) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  const a = hash(i + seed * 101.3) * 2 - 1, b = hash(i + 1 + seed * 101.3) * 2 - 1;
  return a + (b - a) * u;
}
export function wiggle(value, t, freq, amp, seed = 1) {
  const f = (d) => {
    let s = 0, a = 1, fr = 1, norm = 0;
    for (let o = 0; o < 3; o++) { s += a * noise1(t * freq * fr, seed * 7 + d * 13 + o * 31); norm += a; a *= 0.5; fr *= 2; }
    return (s / norm) * amp;
  };
  return isArr(value) ? value.map((v, d) => v + f(d)) : value + f(0);
}

export function classifyExpression(x) {
  if (!x) return null;
  const s = x.replace(/\s+/g, ' ');
  if (/nearestKey\(time\)/.test(s) && /velocityAtTime/.test(s) && /Math\.sin/.test(s)) {
    return {
      kind: 'inertia',
      amp: num(/amp\s*=\s*([-\d.]+)/, s, 0.05),
      freq: num(/freq\s*=\s*([-\d.]+)/, s, 2.5),
      decay: num(/decay\s*=\s*([-\d.]+)/, s, 5),
      tmax: num(/time_max\s*=\s*([-\d.]+)/, s, 1),
      easeTail: /easeOut\(t,\s*0,\s*time_max/.test(s),
    };
  }
  if (/textIndex/.test(s) && /Math\.cos\(freq\*t\*2\*Math\.PI\)/.test(s.replace(/\s/g, ''))) {
    return {
      kind: 'textBounce',
      middleFirst: /distFromMid/.test(s),
      delay: /delay\s*=\s*effect\(/.test(s) ? { effect: s.match(/delay\s*=\s*effect\("([^"]+)"\)/)[1] } : num(/delay\s*=\s*([-\d.]+)/, s, 0.05),
      freq: num(/freq\s*=\s*([-\d.]+)/, s, 2.5),
      amp: num(/amplitude\s*=\s*([-\d.]+)/, s, 100),
      decay: num(/decay\s*=\s*([-\d.]+)/, s, 7),
    };
  }
  let m = s.match(/^wiggle\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)/);
  if (m) return { kind: 'wiggle', freq: +m[1], amp: +m[2] };
  m = s.match(/^wiggle\(\s*([-\d.]+)\s*,\s*effect\("([^"]+)"\)\("([^"]+)"\)\s*\)/);
  if (m) return { kind: 'wiggle', freq: +m[1], ampEffect: m[2] };
  if (/^loopOut\(\s*"cycle"\s*\)/.test(s)) return { kind: 'loopCycle' };
  m = s.match(/^time\s*\*\s*([-\d.]+)\s*;?$/);
  if (m) return { kind: 'timeMul', k: +m[1] };
  m = s.match(/position\[0\]\s*\+\s*\(index\s*\*\s*comp\("([^"]+)"\)\.layer\("([^"]+)"\)\.effect\("([^"]+)"\)\(1\)\/10\)/);
  if (m) return { kind: 'depthOffset', comp: m[1], layer: m[2], effect: m[3] };
  m = s.match(/^comp\("([^"]+)"\)\.layer\("([^"]+)"\)\.effect\("([^"]+)"\)\(1\)\/(\d+)\s*;?$/);
  if (m) return { kind: 'ctrlDiv', comp: m[1], layer: m[2], effect: m[3], div: +m[4] };
  if (/textIndex === textTotal/.test(s)) return { kind: 'lastChar' };
  return { kind: 'unknown', src: s.slice(0, 80) };
}

const exprCache = new WeakMap();
export function exprOf(prop) {
  if (!prop.x || prop.x_off) return null;
  let e = exprCache.get(prop);
  if (e === undefined) { e = classifyExpression(prop.x); exprCache.set(prop, e); }
  return e;
}

// Evaluate a property at time t including its expression. ctx gives layer/comp lookups.
export function evalProp(prop, t, ctx = {}) {
  if (!prop) return undefined;
  const base = keyValue(prop, t);
  const e = exprOf(prop);
  if (!e) return base;
  switch (e.kind) {
    case 'inertia': {
      const K = prop.k || [];
      let n = -1;
      for (let i = 0; i < K.length; i++) if (K[i].t <= t) n = i;
      if (n < 0) return base;
      const dt = t - K[n].t;
      if (dt >= e.tmax || (!e.easeTail && dt >= 1)) return base;
      const fd = (ctx.frameDuration || 1 / 30) / 10;
      const h = 1e-3, tv = K[n].t - fd;
      const v = mul(sub(keyValue(prop, tv + h / 2), keyValue(prop, tv - h / 2)), 1 / h);
      let k = (e.amp * Math.sin(e.freq * dt * 2 * Math.PI)) / Math.exp(e.decay * dt);
      if (e.easeTail) k *= easeOutF(dt, 0, e.tmax, 1, 0);
      return add(base, mul(v, k));
    }
    case 'wiggle': {
      const amp = e.ampEffect ? (ctx.effectValue?.(e.ampEffect) ?? 0) : e.amp;
      return amp ? wiggle(base, t, e.freq, amp, ctx.seed || 1) : base;
    }
    case 'loopCycle': {
      const K = prop.k;
      if (!K || K.length < 2 || t <= K[K.length - 1].t) return base;
      const a = K[0].t, b = K[K.length - 1].t;
      return keyValue(prop, a + ((t - a) % (b - a)));
    }
    case 'timeMul': return e.k * t;
    case 'depthOffset': {
      const off = ctx.ctrl?.(e.comp, e.layer, e.effect) ?? 0;
      const idx = ctx.index || 0;
      const s = (ctx.ctrl?.(e.comp, e.layer, e.effect.replace('x', 'y')) ?? 0);
      const zo = ctx.ctrl?.(e.comp, e.layer, e.effect.replace('x', 'z')) ?? 0;
      return [base[0] + (idx * off) / 10, base[1] + (idx * s) / 10, idx + (idx * zo) / 10];
    }
    case 'ctrlDiv': return (ctx.ctrl?.(e.comp, e.layer, e.effect) ?? 0) / e.div;
    default: return base;
  }
}

function easeOutF(t, t0, t1, v0, v1) {
  if (t <= t0) return v0;
  if (t >= t1) return v1;
  const u = (t - t0) / (t1 - t0);
  return v0 + (v1 - v0) * (1 - (1 - u) * (1 - u));
}

// Text "Expressible" selector amount for character i (0-based) of n at layer-local time.
export function textBounceAmount(e, i, n, tLocal, ctx) {
  const delay = typeof e.delay === 'number' ? e.delay : (ctx.effectValue?.(e.delay.effect) ?? 0.05);
  const idx = e.middleFirst ? Math.abs(i - (n - 1) / 2) : i + 1;
  const t = tLocal - delay * idx;
  if (t < 0) return 100; // before start: full effect (property value applied)
  return (e.amp * Math.cos(e.freq * t * 2 * Math.PI)) / Math.exp(e.decay * t);
}
