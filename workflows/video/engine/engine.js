// AE-semantics renderer: evaluates a comp tree (from the .aep dump format) at time t and composites it with WebGL.
import { evalProp, keyValue } from './anim.js';
import { textAnimation, drawText, mapFont, ensureFont } from './text.js';
import { GL, BLEND } from './gl.js';

// ------------------------------------------------------------------ math (column-major 4x4)
const I4 = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
function mm(a, b) {
  const o = new Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
    o[c * 4 + r] = s;
  }
  return o;
}
const T = (x, y, z) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1];
const S = (x, y, z) => [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1];
const D2R = Math.PI / 180;
const RX = (a) => { const c = Math.cos(a * D2R), s = Math.sin(a * D2R); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; };
const RY = (a) => { const c = Math.cos(a * D2R), s = Math.sin(a * D2R); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; };
const RZ = (a) => { const c = Math.cos(a * D2R), s = Math.sin(a * D2R); return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; };
const xf = (m, p) => [0, 1, 2, 3].map((r) => m[r] * p[0] + m[4 + r] * p[1] + m[8 + r] * p[2] + m[12 + r] * (p[3] ?? 1));
function inv(m) {
  const [a00, a01, a02, a03, a10, a11, a12, a13, a20, a21, a22, a23, a30, a31, a32, a33] = m;
  const b00 = a00 * a11 - a01 * a10, b01 = a00 * a12 - a02 * a10, b02 = a00 * a13 - a03 * a10, b03 = a01 * a12 - a02 * a11;
  const b04 = a01 * a13 - a03 * a11, b05 = a02 * a13 - a03 * a12, b06 = a20 * a31 - a21 * a30, b07 = a20 * a32 - a22 * a30;
  const b08 = a20 * a33 - a23 * a30, b09 = a21 * a32 - a22 * a31, b10 = a21 * a33 - a23 * a31, b11 = a22 * a33 - a23 * a32;
  const d = 1 / (b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06);
  return [
    (a11 * b11 - a12 * b10 + a13 * b09) * d, (a02 * b10 - a01 * b11 - a03 * b09) * d, (a31 * b05 - a32 * b04 + a33 * b03) * d, (a22 * b04 - a21 * b05 - a23 * b03) * d,
    (a12 * b08 - a10 * b11 - a13 * b07) * d, (a00 * b11 - a02 * b08 + a03 * b07) * d, (a32 * b02 - a30 * b05 - a33 * b01) * d, (a20 * b05 - a22 * b02 + a23 * b01) * d,
    (a10 * b10 - a11 * b08 + a13 * b06) * d, (a01 * b08 - a00 * b10 - a03 * b06) * d, (a30 * b04 - a31 * b02 + a33 * b00) * d, (a21 * b02 - a20 * b04 - a23 * b00) * d,
    (a11 * b07 - a10 * b09 - a12 * b06) * d, (a00 * b09 - a01 * b07 + a02 * b06) * d, (a31 * b01 - a30 * b03 - a32 * b00) * d, (a20 * b03 - a21 * b01 + a22 * b00) * d,
  ];
}

// AE Gaussian 'Blurriness' -> sigma (px). Calibrated against renders; see golden-shot notes.
export let BLUR_K = 0.5;
export const setBlurK = (k) => { BLUR_K = k; };
const findM = (node, m) => (node?.c || node?.props || []).find((c) => c.m === m);
const isEnabled = (L) => L.enabled === true;

export class Engine {
  constructor(project, opts = {}) {
    this.p = project;
    this.comps = new Map(project.comps.map((c) => [c.id, c]));
    this.compsByName = new Map(project.comps.map((c) => [c.name, c]));
    this.footage = new Map(project.footage.map((f) => [f.id, f]));
    this.assetUrl = opts.assetUrl; // (footage) => url | null
    this.videoFrameUrl = opts.videoFrameUrl; // (footage, sourceTime) => url
    this.images = new Map();
    this.warned = new Set();
    this.mbSamples = opts.mbSamples ?? 8;
    this.ss = opts.supersample ?? 2;
  }
  warn(k) { if (!this.warned.has(k)) { this.warned.add(k); console.warn('[engine]', k); } }

  async init(canvas) {
    this.canvas = canvas;
    this.g = new GL(canvas);
    this.g.keep = [...new Set(this.p.comps.map((c) => c.w + 'x' + c.h))].map((k) => k.split('x').map(Number));
    for (const f of ['Inter Variable', 'Inter Tight Variable', 'Anton', 'Tinos', 'Patrick Hand', 'League Gothic', 'Archivo Narrow'])
      for (const w of [100, 300, 400, 500, 600, 700, 800, 900]) await document.fonts.load(`${w} 40px "${f}"`).catch(() => {});
  }

  // ------------------------------------------------------------ time & visibility
  localTime(L, t) { // layer source time
    const st = L.start_time || 0, str = (L.stretch || 100) / 100;
    const tr = (L.props || []).find((p) => p.m === 'ADBE Time Remapping');
    if (L.time_remap_enabled && tr) return evalProp(tr, t);
    return (t - st) / str;
  }
  // in/out points are frame-aligned but stored rounded to 1e-4 s: compare with a 1 ms tolerance
  active(L, t) { return isEnabled(L) && t >= L.in_point - 1e-3 && t < L.out_point - 1e-3; }

  // ------------------------------------------------------------ expressions context
  ctxFor(comp, L) {
    const self = this;
    return {
      frameDuration: 1 / comp.fps,
      index: (L.i ?? 0) + 1,
      seed: (L.i ?? 0) + 1,
      effectValue(name) {
        const fx = findM(L, 'ADBE Effect Parade');
        const e = fx?.c?.find((x) => x.n === name);
        const p = e?.c?.find((x) => !x.c);
        return p ? evalProp(p, self._t) : 0;
      },
      ctrl(compName, layerName, effName) {
        const c = self.compsByName.get(compName);
        const l = c?.layers.find((x) => x.name === layerName);
        const fx = l && findM(l, 'ADBE Effect Parade');
        const e = fx?.c?.find((x) => x.n === effName);
        const p = e?.c?.find((x) => !x.c);
        return p ? evalProp(p, self._t) : 0;
      },
    };
  }

  // ------------------------------------------------------------ transforms
  sourceSize(L) {
    if (L.src_id != null) {
      const c = this.comps.get(L.src_id);
      if (c) return [c.w, c.h];
      const f = this.footage.get(L.src_id);
      if (f) return [f.width || 100, f.height || 100];
    }
    return [0, 0];
  }
  transformOf(comp, L, t) {
    const tg = findM(L, 'ADBE Transform Group') || { c: [] };
    const ctx = this.ctxFor(comp, L);
    const g = (m, d) => { const p = findM(tg, m); return p ? evalProp(p, t, ctx) : d; };
    const [sw, sh] = this.sourceSize(L);
    const isAV = L.type === 'AVLayer' && L.src_id != null;
    const isCam = L.type === 'CameraLayer';
    const anchor = isCam ? [0, 0, 0] : g('ADBE Anchor Point', isAV ? [sw / 2, sh / 2, 0] : [0, 0, 0]);
    let pos;
    const sep = ['ADBE Position_0', 'ADBE Position_1', 'ADBE Position_2'].map((m) => findM(tg, m));
    const P = g('ADBE Position', [comp.w / 2, comp.h / 2, 0]);
    if (sep.some((p) => p && p.k)) pos = sep.map((p, i) => (p ? evalProp(p, t, ctx) : (P[i] || 0)));
    else pos = P;
    const sc = g('ADBE Scale', [100, 100, 100]);
    const ori = g('ADBE Orientation', [0, 0, 0]);
    const rx = g('ADBE Rotate X', 0), ry = g('ADBE Rotate Y', 0), rz = g('ADBE Rotate Z', 0);
    const op = g('ADBE Opacity', 100);
    const is3D = !!L.three_d_layer || isCam;
    let m = T(pos[0], pos[1], is3D ? pos[2] || 0 : 0);
    if (is3D) m = mm(m, mm(RZ(ori[2]), mm(RY(ori[1]), RX(ori[0]))));
    if (is3D) m = mm(m, mm(RX(rx), mm(RY(ry), RZ(rz))));
    else m = mm(m, RZ(rz));
    if (!isCam) m = mm(m, mm(S(sc[0] / 100, sc[1] / 100, is3D ? (sc[2] ?? 100) / 100 : 1), T(-anchor[0], -anchor[1], is3D ? -(anchor[2] || 0) : 0)));
    return { m, op: op / 100, is3D };
  }
  worldOf(comp, L, t, cache) {
    if (cache.has(L)) return cache.get(L);
    let { m, op, is3D } = this.transformOf(comp, L, t);
    if (L.parent != null) {
      const P = comp.layers.find((x) => x.i === L.parent);
      if (P) {
        const pw = this.worldOf(comp, P, t, cache);
        // parenting ignores parent's anchor-less scale on camera; uses full parent matrix
        m = mm(pw.m, m);
      }
    }
    const r = { m, op, is3D };
    cache.set(L, r);
    return r;
  }
  cameraOf(comp, t, cache) {
    const cams = comp.layers.filter((L) => L.type === 'CameraLayer' && this.active(L, t)).sort((a, b) => a.i - b.i);
    const W = comp.w, H = comp.h;
    if (!cams.length) {
      const zoom = W * 1.38889;
      return { view: inv(T(W / 2, H / 2, -zoom)), zoom, W, H };
    }
    const C = cams[0];
    const w = this.worldOf(comp, C, t, cache);
    const co = findM(C, 'ADBE Camera Options Group');
    const zoomP = co && findM(co, 'ADBE Camera Zoom');
    const zoom = zoomP ? evalProp(zoomP, t) : W * 1.38889;
    // one-node camera: camera space x right, y down, z forward. Its world origin is at comp centre offset.
    return { view: inv(w.m), zoom, W, H, layer: C, dof: co };
  }
  // project a world point to clip space of target (W,H)
  clip3(cam, p) {
    const c = xf(cam.view, p);
    const Z = c[2];
    return [(2 * cam.zoom * c[0]) / cam.W, (2 * cam.zoom * c[1]) / cam.H, 0, Z];
  }
  clip2(W, H, p) { return [(p[0] / W) * 2 - 1, (p[1] / H) * 2 - 1, 0, 1]; }

  // ------------------------------------------------------------ assets
  async loadImage(url) {
    if (this.images.has(url)) return this.images.get(url);
    const pr = new Promise((res) => {
      const im = new Image();
      im.onload = () => res(im);
      im.onerror = () => { this.warn('missing ' + url); res(null); };
      im.src = url;
    });
    this.images.set(url, pr);
    const im = await pr;
    this.images.set(url, im);
    return im;
  }
  // Walk visible layers and preload what will be drawn at time t.
  async prepare(comp, t, depth = 0) {
    if (depth > 12) return;
    for (const L of comp.layers) {
      if (!this.active(L, t) && !(L.is_track_matte && t >= L.in_point && t < L.out_point)) continue;
      if (L.src_id == null) continue;
      const lt = this.localTime(L, t);
      const sub = this.comps.get(L.src_id);
      if (sub) { await this.prepare(sub, lt, depth + 1); continue; }
      const f = this.footage.get(L.src_id);
      if (!f || f.source_type === 'SolidSource' || /\.(mp3|wav|aac|m4a|aif+)$/i.test(f.file || f.name)) continue;
      if (f.is_still || !f.duration) { const u = this.assetUrl(f); if (u) await this.loadImage(u); }
      else { const u = this.videoFrameUrl(f, lt); if (u) await this.loadImage(u); }
    }
    if (this.textNeeded) await this.textNeeded;
  }

  // ------------------------------------------------------------ layer content → target (+ rect in layer space)
  content(comp, L, t, opts) {
    const g = this.g;
    const lt = this.localTime(L, t);
    if (L.type === 'TextLayer') {
      const anim = textAnimation(L, t, this.ctxFor(comp, L));
      const ss = Math.max(1, Math.min(4, (opts.scaleHint || 1) * this.ss));
      const r = drawText(anim, ss);
      const tex = g.texFromImage(r.canvas);
      const tg = g.target(r.canvas.width, r.canvas.height);
      g.copy(tex, tg); g.deleteTex(tex);
      return { tg, rect: [-r.ox, -r.oy, -r.ox + r.canvas.width / ss, -r.oy + r.canvas.height / ss] };
    }
    if (L.type === 'ShapeLayer') return this.shapeContent(comp, L, t, opts);
    if (L.src_id == null) return null;
    const sub = this.comps.get(L.src_id);
    if (sub) {
      const tg = this.renderComp(sub, lt, { ...opts, tc: this.localTime(L, opts.tcL ?? t) });
      return { tg, rect: [0, 0, sub.w, sub.h] };
    }
    const f = this.footage.get(L.src_id);
    if (!f) return null;
    if (L.null_layer) return null;
    if (f.source_type === 'SolidSource') {
      const tg = g.target(Math.min(f.width, 4096), Math.min(f.height, 4096));
      const c = f.color || [0, 0, 0];
      g.clear(tg, [c[0], c[1], c[2], 1]);
      return { tg, rect: [0, 0, f.width, f.height] };
    }
    const url = f.is_still || !f.duration ? this.assetUrl(f) : this.videoFrameUrl(f, lt);
    const im = url && this.images.get(url);
    if (!im || im instanceof Promise) return null;
    const tex = g.texFromImage(im);
    const tg = g.target(im.width, im.height);
    g.copy(tex, tg); g.deleteTex(tex);
    return { tg, rect: [0, 0, f.width || im.width, f.height || im.height] };
  }

  shapeContent(comp, L, t, opts) {
    const root = findM(L, 'ADBE Root Vectors Group');
    if (!root) return null;
    const ctxE = this.ctxFor(comp, L);
    const ev = (p, d) => (p ? evalProp(p, t, ctxE) : d);
    const draws = []; // {path:Path2D in layer coords, fill, stroke, width, m:DOMMatrix}
    const pts = [];
    const walk = (grp, mat, opacity) => {
      const items = findM(grp, 'ADBE Vectors Group')?.c || grp.c || [];
      const paths = [];
      let localM = mat;
      const vt = findM(grp, 'ADBE Vector Transform Group');
      if (vt) {
        const a = ev(findM(vt, 'ADBE Vector Anchor'), [0, 0]), p = ev(findM(vt, 'ADBE Vector Position'), [0, 0]);
        const s = ev(findM(vt, 'ADBE Vector Scale'), [100, 100]), r = ev(findM(vt, 'ADBE Vector Rotation'), 0);
        opacity *= ev(findM(vt, 'ADBE Vector Group Opacity'), 100) / 100;
        localM = mat.multiply(new DOMMatrix().translate(p[0], p[1]).rotate(r).scale(s[0] / 100, s[1] / 100).translate(-a[0], -a[1]));
      }
      let trim = null;
      for (const it of items) if (it.m === 'ADBE Vector Filter - Trim') trim = { s: ev(findM(it, 'ADBE Vector Trim Start'), 0), e: ev(findM(it, 'ADBE Vector Trim End'), 100), o: ev(findM(it, 'ADBE Vector Trim Offset'), 0) };
      for (const it of items) {
        if (it.m === 'ADBE Vector Group') { walk(it, localM, opacity); continue; }
        if (it.m === 'ADBE Vector Shape - Rect') {
          const sz = ev(findM(it, 'ADBE Vector Rect Size'), [100, 100]), ps = ev(findM(it, 'ADBE Vector Rect Position'), [0, 0]);
          const rd = Math.min(ev(findM(it, 'ADBE Vector Rect Roundness'), 0), sz[0] / 2, sz[1] / 2);
          const p = new Path2D(); p.roundRect(ps[0] - sz[0] / 2, ps[1] - sz[1] / 2, sz[0], sz[1], rd);
          paths.push(p); pts.push([localM, ps[0] - sz[0] / 2, ps[1] - sz[1] / 2], [localM, ps[0] + sz[0] / 2, ps[1] + sz[1] / 2]);
        } else if (it.m === 'ADBE Vector Shape - Ellipse') {
          const sz = ev(findM(it, 'ADBE Vector Ellipse Size'), [100, 100]), ps = ev(findM(it, 'ADBE Vector Ellipse Position'), [0, 0]);
          const p = new Path2D(); p.ellipse(ps[0], ps[1], Math.abs(sz[0] / 2), Math.abs(sz[1] / 2), 0, 0, Math.PI * 2);
          paths.push(p); pts.push([localM, ps[0] - sz[0] / 2, ps[1] - sz[1] / 2], [localM, ps[0] + sz[0] / 2, ps[1] + sz[1] / 2]);
        } else if (it.m === 'ADBE Vector Shape - Group') {
          const sh = ev(findM(it, 'ADBE Vector Shape'), null);
          if (sh && sh._shape) { paths.push(bezPath(sh)); for (const v of sh.vtx) pts.push([localM, v[0], v[1]]); }
        } else if (it.m === 'ADBE Vector Graphic - Fill' || it.m === 'ADBE Vector Graphic - Stroke') {
          const col = ev(findM(it, it.m.endsWith('Fill') ? 'ADBE Vector Fill Color' : 'ADBE Vector Stroke Color'), [1, 1, 1, 1]);
          const o = ev(findM(it, it.m.endsWith('Fill') ? 'ADBE Vector Fill Opacity' : 'ADBE Vector Stroke Opacity'), 100) / 100;
          const w = it.m.endsWith('Stroke') ? ev(findM(it, 'ADBE Vector Stroke Width'), 2) : 0;
          for (const p of paths) draws.push({ p, m: localM, col, o: o * opacity, stroke: it.m.endsWith('Stroke'), w, trim });
        }
      }
    };
    walk(root, new DOMMatrix(), 1);
    if (!draws.length || !pts.length) return null;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [m, x, y] of pts) { const q = m.transformPoint({ x, y }); x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.x); y1 = Math.max(y1, q.y); }
    const pad = 4 + Math.max(...draws.map((d) => d.w));
    x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
    const ss = Math.max(1, Math.min(3, (opts.scaleHint || 1) * this.ss));
    const W = Math.min(8192, Math.ceil((x1 - x0) * ss)), H = Math.min(8192, Math.ceil((y1 - y0) * ss));
    if (W < 1 || H < 1) return null;
    const cv = new OffscreenCanvas(W, H), c = cv.getContext('2d');
    for (const d of draws.reverse()) {
      c.save();
      c.setTransform(new DOMMatrix().scale(ss, ss).translate(-x0, -y0).multiply(d.m));
      c.globalAlpha = Math.max(0, Math.min(1, d.o * (d.col[3] ?? 1)));
      const css = `rgb(${d.col.slice(0, 3).map((v) => Math.round(v * 255)).join(',')})`;
      if (d.stroke) {
        c.strokeStyle = css; c.lineWidth = d.w; c.lineCap = 'round'; c.lineJoin = 'round';
        if (d.trim && (d.trim.s !== 0 || d.trim.e !== 100)) { // approximate trim with dash
          const L = 4000, s = (Math.min(d.trim.s, d.trim.e) / 100) * L, e = (Math.max(d.trim.s, d.trim.e) / 100) * L;
          c.setLineDash([Math.max(0.001, e - s), L * 2]); c.lineDashOffset = -s;
        }
        c.stroke(d.p);
      } else { c.fillStyle = css; c.fill(d.p); }
      c.restore();
    }
    const tex = this.g.texFromImage(cv.transferToImageBitmap());
    const tg = this.g.target(W, H);
    this.g.copy(tex, tg); this.g.deleteTex(tex);
    return { tg, rect: [x0, y0, x0 + W / ss, y0 + H / ss] };
  }

  // ------------------------------------------------------------ masks & effects
  maskTarget(L, t, ct) {
    const mp = findM(L, 'ADBE Mask Parade');
    const masks = (mp?.c || []).filter((m) => m.m === 'ADBE Mask Atom' && m.mode !== 6812);
    if (!masks.length) return null;
    const [rx0, ry0, rx1, ry1] = ct.rect;
    const W = ct.tg.w, H = ct.tg.h, sx = W / (rx1 - rx0), sy = H / (ry1 - ry0);
    const cv = new OffscreenCanvas(W, H), c = cv.getContext('2d');
    let first = true;
    let maxFeather = 0;
    for (const m of masks) {
      const sh = evalProp(findM(m, 'ADBE Mask Shape'), t);
      if (!sh || !sh._shape) continue;
      const op = (evalProp(findM(m, 'ADBE Mask Opacity'), t) ?? 100) / 100;
      const fe = evalProp(findM(m, 'ADBE Mask Feather'), t) ?? [0, 0];
      maxFeather = Math.max(maxFeather, fe[0] || 0);
      const tmp = new OffscreenCanvas(W, H), tc = tmp.getContext('2d');
      tc.setTransform(sx, 0, 0, sy, -rx0 * sx, -ry0 * sy);
      if (fe[0] > 0.5) tc.filter = `blur(${(fe[0] * sx) / 2.5}px)`;
      tc.fillStyle = `rgba(255,255,255,${op})`;
      tc.fill(bezPath(sh));
      if (m.inv) { tc.globalCompositeOperation = 'xor'; tc.setTransform(1, 0, 0, 1, 0, 0); tc.filter = 'none'; tc.fillRect(0, 0, W, H); }
      const mode = m.mode || 6813;
      if (first && mode === 6814) { c.fillStyle = '#fff'; c.fillRect(0, 0, W, H); }
      c.globalCompositeOperation = mode === 6814 ? 'destination-out' : mode === 6815 ? 'destination-in' : (first ? 'source-over' : 'source-over');
      c.drawImage(tmp, 0, 0);
      first = false;
    }
    const tex = this.g.texFromImage(cv.transferToImageBitmap());
    return tex;
  }

  // extra pixels needed around layer content so blurs / glows / shadows aren't clipped
  effectPad(comp, L, t, sx) {
    const fx = findM(L, 'ADBE Effect Parade');
    if (!fx?.c?.length) return 0;
    let pad = 0;
    for (const e of fx.c) {
      const PM = (suffix, d) => { const p = (e.c || []).find((x) => x.m === `${e.m}-${suffix}`); return p ? evalProp(p, t) : d; };
      if (/Gaussian Blur|Camera Lens Blur/.test(e.m)) pad = Math.max(pad, PM('0001', 0) * 1.5);
      else if (e.m === 'ADBE Box Blur2') pad = Math.max(pad, PM('0001', 0) * 2);
      else if (e.m === 'ADBE Drop Shadow') pad = Math.max(pad, PM('0004', 5) + PM('0005', 0) * 1.2);
      else if (e.m === 'PEDG') pad = Math.max(pad, 160);
    }
    return Math.min(600, Math.ceil(pad * sx));
  }

  applyEffects(comp, L, t, tg, rect, isAdjustment = false) {
    const fx = findM(L, 'ADBE Effect Parade');
    if (!fx?.c?.length) return tg;
    const g = this.g;
    const sx = tg.w / (rect[2] - rect[0]);
    let cur = tg;
    const swap = (n) => { if (n !== cur) { g.release(cur); cur = n; } };
    for (const e of fx.c) {
      if (e.off) continue;
      const P = (name, d) => { const p = (e.c || []).find((x) => x.n === name && !x.c); return p ? evalProp(p, t, this.ctxFor(comp, L)) : d; };
      const PM = (suffix, d) => { const p = (e.c || []).find((x) => x.m === `${e.m}-${suffix}`); return p ? evalProp(p, t, this.ctxFor(comp, L)) : d; };
      switch (e.m) {
        case 'ADBE Fill': swap(g.color(cur, 1, { uA: P('Color', [1, 0, 0, 1]), uK: (P('Opacity', 1) > 1 ? P('Opacity', 100) / 100 : P('Opacity', 1)) })); break;
        case 'ADBE Tint': swap(g.color(cur, 2, { uA: PM('0001', [0, 0, 0, 1]), uB: PM('0002', [1, 1, 1, 1]), uK: PM('0003', 100) / 100 })); break;
        case 'ADBE Exposure2': swap(g.color(cur, 3, { uA: [PM('0003', 0), PM('0004', 0), PM('0005', 1), 0] })); break;
        case 'ADBE Invert': swap(g.color(cur, 6)); break;
        case 'CC Threshold': swap(g.color(cur, 5, { uK: PM('0001', 0.5) > 1 ? PM('0001', 127) / 255 : PM('0001', 0.5) })); break;
        case 'ADBE Gaussian Blur 2': case 'ADBE Gaussian Blur': {
          const b = PM('0001', 0) * sx * BLUR_K, dim = PM('0002', 1);
          if (b > 0.3) swap(g.blur(cur, dim === 3 ? 0 : b, dim === 2 ? 0 : b));
          break;
        }
        case 'ADBE Box Blur2': {
          const r = PM('0001', 0) * sx * 0.6, dim = PM('0003', 1);
          if (r > 0.3) swap(g.blur(cur, dim === 3 ? 0 : r, dim === 2 ? 0 : r));
          break;
        }
        case 'ADBE Camera Lens Blur': { const r = PM('0001', 0) * sx * 0.5; if (r > 0.3) swap(g.blur(cur, r, r)); break; }
        case 'ADBE Drop Shadow': {
          const col = PM('0001', [0, 0, 0, 1]), op = PM('0002', 127.5) / 255, dir = PM('0003', 135), dist = PM('0004', 5) * sx, soft = PM('0005', 0) * sx, only = PM('0006', 0);
          const bl = g.blur(cur, soft / 2.5 + 0.01, soft / 2.5 + 0.01);
          const out = g.target(cur.w, cur.h);
          g.run('shadow', out, { uOff: [dist * Math.sin(dir * D2R), -dist * Math.cos(dir * D2R)], uA: col, uK: op, uOnly: only ? 1 : 0 }, { uTex: bl, uDst: cur });
          g.release(bl); swap(out);
          break;
        }
        case 'PEDG': { // Deep Glow approximation: multi-radius bloom added on top
          const exp = P('Exposure', 0.5), rad = (P('Radius', 100)) * sx;
          let acc = g.target(cur.w, cur.h); g.copy(cur, acc);
          for (let k = 0; k < 5; k++) {
            const b = g.blur(cur, Math.max(1, rad / Math.pow(2.2, k) / 3));
            const o = g.target(cur.w, cur.h);
            g.run('add', o, { uK: exp * 0.35 }, { uTex: b, uDst: acc });
            g.release(b); g.release(acc); acc = o;
          }
          swap(acc);
          break;
        }
        case 'ADBE Minimax': {
          const op = PM('0001', 2), rad = PM('0002', 0) * sx, dir = PM('0004', 1);
          const dirs = dir === 2 ? [[1, 0]] : dir === 3 ? [[0, 1]] : [[1, 0], [0, 1]];
          if (rad >= 1) {
            if (op === 1 || op === 2) swap(g.minimax(cur, rad, dirs, op === 2));
            else { const a = g.minimax(cur, rad, dirs, op === 4); swap(a); swap(g.minimax(cur, rad, dirs, op !== 4)); }
          }
          break;
        }
        case 'S_Gradient': {
          const a = P('Start XY', [0, 0]), b = P('End XY', [0, rect[3]]);
          const toPx = (p) => [(p[0] - rect[0]) * sx, (p[1] - rect[1]) * sx];
          swap(g.color(cur, 7, { uA: [...toPx(a), 0, 0], uB: [...toPx(b), 0, 0], uK: 0.6 }));
          break;
        }
        case 'CS Vignette': swap(g.color(cur, 8, { uK: Math.min(1, PM('0001', 100) / 250) })); break;
        case 'ADBE CurvesCustom': {
          const cv = (e.c || []).find((x) => x.v && x.v._curves);
          if (cv) { const lut = g.lutTex(curvesLut(cv.v.channels)); swap(g.color(cur, 4, {}, lut)); g.deleteTex(lut); }
          break;
        }
        case 'ADBE Geometry2': {
          const [w, h] = [rect[2] - rect[0], rect[3] - rect[1]];
          const an = P('Anchor Point', [w / 2, h / 2]), ps = P('Position', [w / 2, h / 2]);
          const sh = P('Scale Height', 100), sw = P('Scale Width', sh), uni = P('Uniform Scale', 1);
          const rot = P('Rotation', 0), op = P('Opacity', 100) / 100;
          const scx = (uni ? sh : sw) / 100, scy = sh / 100;
          // inverse map: dst px → src px
          const m = new DOMMatrix().translate((ps[0] - rect[0]) * sx, (ps[1] - rect[1]) * sx).rotate(rot).scale(scx, scy).translate(-(an[0] - rect[0]) * sx, -(an[1] - rect[1]) * sx).inverse();
          const o = g.target(cur.w, cur.h);
          g.run('transform', o, { uM: [m.a, m.b, 0, m.c, m.d, 0, m.e, m.f, 1], uK: op }, { uTex: cur });
          swap(o);
          break;
        }
        case 'BCC Halftone': case 'X Halftone': {
          const cell = P('Cell', 5 * 2.2) * sx; // BCC 'scale 5' ~ 11 px cells at 1080p (visual match)
          swap(g.color(cur, 9, { uK: Math.max(2, cell), uA: P('Ink', [0.11, 0.11, 0.11, 1]), uB: P('Paper', [0.86, 0.86, 0.86, 1]) }));
          break;
        }
        case 'CC Light Sweep': {
          const c = P('Center', [(rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2]), dir = P('Direction', 30), w = P('Width', 80);
          const col = P('Light Color', [1, 1, 1, 1]), inten = P('Sweep Intensity', 50) / 100;
          swap(g.color(cur, 10, { uA: [(c[0] - rect[0]) * sx, (c[1] - rect[1]) * sx, dir, 0], uB: [col[0], col[1], col[2], Math.max(0.2, inten)], uK: w * sx }));
          break;
        }
        case 'S_TimeWarpRGB': case 'X RGB Split': {
          const o = g.target(cur.w, cur.h);
          g.run('rgbsplit', o, { uOff: [P('Amount', 8) * sx, 0] }, { uTex: cur });
          swap(o);
          break;
        }
        case 'ADBE Slider Control': case 'ADBE Checkbox Control': case 'ADBE Layer Control': case 'ADBE Color Control': case 'ADBE Point Control': case 'ADBE Angle Control': break;
        default: this.warn('effect not implemented: ' + e.m + ' (' + e.n + ')');
      }
    }
    return cur;
  }

  // ------------------------------------------------------------ comp rendering
  // Returns a pooled target with the comp rendered at time t (no motion blur here).
  // ts = sub-frame time (motion-blur sample), opts.tc = the frame's own time in this comp.
  // AE semantics: visibility follows the frame time; only layers with their motion-blur switch on
  // (in a comp with motion blur enabled) move with the sub-frame time, others stay at the frame time.
  renderComp(comp, ts, opts = {}) {
    const g = this.g;
    const tc = opts.tc ?? ts;
    this._t = tc;
    const out = g.target(comp.w, comp.h);
    g.clear(out);
    const cacheS = new Map(), cacheC = ts === tc ? cacheS : new Map();
    const camS = this.cameraOf(comp, ts, cacheS), camC = ts === tc ? camS : this.cameraOf(comp, tc, cacheC);
    const layers = [...comp.layers].sort((a, b) => b.i - a.i);
    const items = [];
    for (const L of layers) {
      if (!this.active(L, tc)) continue;
      if (L.type === 'CameraLayer' || L.type === 'LightLayer' || L.guide_layer || L.is_track_matte) continue;
      if (L.null_layer) continue;
      const f = L.src_id != null ? this.footage.get(L.src_id) : null;
      if (f && (f.has_video === false || /\.(mp3|wav|aac|m4a|aif+)$/i.test(f.file || f.name))) continue;
      const mb = !!(comp.motion_blur && L.motion_blur);
      items.push({ L, t: mb ? ts : tc, cache: mb ? cacheS : cacheC, cam: mb ? camS : camC });
    }
    // depth sort runs of 3D layers (AE sorts 3D layers among themselves between 2D layers)
    let i = 0;
    const ordered = [];
    while (i < items.length) {
      if (!items[i].L.three_d_layer) { ordered.push(items[i++]); continue; }
      const run = [];
      while (i < items.length && items[i].L.three_d_layer) run.push(items[i++]);
      run.forEach((it) => {
        const w = this.worldOf(comp, it.L, it.t, it.cache);
        const [sw, sh] = it.L.type === 'TextLayer' || it.L.type === 'ShapeLayer' ? [0, 0] : this.sourceSize(it.L);
        it.z = xf(it.cam.view, xf(w.m, [sw / 2, sh / 2, 0, 1]))[2];
      });
      run.sort((a, b) => b.z - a.z || b.L.i - a.L.i);
      ordered.push(...run);
    }
    for (const it of ordered) this.drawLayer(comp, it.L, it.t, out, it.cam, it.cache, { ...opts, tcL: tc });
    return out;
  }

  drawLayer(comp, L, t, out, cam, cache, opts, parentM = null, parentOp = 1) {
    const g = this.g;
    const w = this.worldOf(comp, L, t, cache);
    const op = w.op * parentOp;
    if (op <= 0.001) return;
    const sub = L.src_id != null ? this.comps.get(L.src_id) : null;
    // collapsed 3D precomp: draw its layers into this comp with combined transforms and our camera
    if (sub && L.collapse_transformation && !findM(L, 'ADBE Effect Parade')?.c?.length && !findM(L, 'ADBE Mask Parade')?.c?.length) {
      const lt = this.localTime(L, t), ltc = this.localTime(L, opts.tcL ?? t);
      const subCache = new Map();
      const base = parentM ? mm(parentM, w.m) : w.m;
      const kids = [...sub.layers].sort((a, b) => b.i - a.i).filter((K) => this.active(K, ltc) && K.type !== 'CameraLayer' && !K.null_layer && !K.is_track_matte && !K.guide_layer);
      // depth-sort children by projected depth
      const third = (K) => { const kw = this.worldOf(sub, K, lt, subCache); return xf(cam.view, xf(mm(base, kw.m), [0, 0, 0, 1]))[2]; };
      const sorted = kids.map((K) => [K, K.three_d_layer || L.three_d_layer ? third(K) : 0]);
      if (L.three_d_layer) sorted.sort((a, b) => b[1] - a[1] || b[0].i - a[0].i);
      const saveT = this._t;
      const subCacheC = new Map();
      for (const [K] of sorted) {
        const mbK = !!(K.motion_blur && L.motion_blur);
        this._t = mbK ? lt : ltc;
        this.drawLayer(sub, K, mbK ? lt : ltc, out, cam, mbK ? subCache : subCacheC, { ...opts, tcL: ltc }, base, op);
      }
      this._t = saveT;
      return;
    }
    const m = parentM ? mm(parentM, w.m) : w.m;
    const is3D = w.is3D || !!parentM;
    if (L.adjustment_layer) { this.drawAdjustment(comp, L, t, out, op); return; }
    // scale hint for rasterisation of vectors/text
    let scaleHint = 1;
    if (is3D) {
      const a = xf(cam.view, xf(m, [0, 0, 0, 1])), b = xf(cam.view, xf(m, [100, 0, 0, 1]));
      const pa = [a[0] / a[2], a[1] / a[2]], pb = [b[0] / b[2], b[1] / b[2]];
      scaleHint = (Math.hypot(pb[0] - pa[0], pb[1] - pa[1]) * cam.zoom) / 100;
    } else scaleHint = Math.hypot(m[0], m[1]);
    const ct = this.content(comp, L, t, { ...opts, scaleHint: Math.min(4, Math.max(0.25, scaleHint)) });
    if (!ct) return;
    let tg = ct.tg;
    const mask = this.maskTarget(L, t, ct);
    if (mask) {
      const o = g.target(tg.w, tg.h);
      g.run('mix', o, { uK: 1, uHasMask: 1 }, { uTex: tg, uDst: g.blank, uMask: mask });
      g.deleteTex(mask); g.release(tg); tg = o;
    }
    const pad = this.effectPad(comp, L, t, tg.w / (ct.rect[2] - ct.rect[0]));
    if (pad > 0) {
      const sx = tg.w / (ct.rect[2] - ct.rect[0]);
      const big = g.target(tg.w + 2 * pad, tg.h + 2 * pad); g.clear(big);
      g.run('copy', big, {}, { uTex: tg }, [[-1 + (2 * pad) / big.w, -1 + (2 * pad) / big.h, 0, 1], [1 - (2 * pad) / big.w, -1 + (2 * pad) / big.h, 0, 1], [-1 + (2 * pad) / big.w, 1 - (2 * pad) / big.h, 0, 1], [1 - (2 * pad) / big.w, 1 - (2 * pad) / big.h, 0, 1]]);
      g.release(tg); tg = big;
      ct.rect = [ct.rect[0] - pad / sx, ct.rect[1] - pad / sx, ct.rect[2] + pad / sx, ct.rect[3] + pad / sx];
    }
    tg = this.applyEffects(comp, L, t, tg, ct.rect);
    // quad corners in layer space → clip
    const [x0, y0, x1, y1] = ct.rect;
    const corners = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]];
    let quad;
    if (is3D) {
      quad = corners.map(([x, y]) => this.clip3(cam, xf(m, [x, y, 0, 1])));
      if (quad.some((q) => q[3] <= 1)) { g.release(tg); return; } // behind camera
    } else quad = corners.map(([x, y]) => this.clip2(out.w, out.h, xf(m, [x, y, 0, 1])));
    // track matte
    let matte = null, matteMode = 0;
    if (L.has_track_matte && L.matte_layer != null) {
      const ML = comp.layers.find((x) => x.i === L.matte_layer);
      if (ML) {
        matte = g.target(out.w, out.h); g.clear(matte);
        const saved = ML.is_track_matte; ML.is_track_matte = false;
        const savedEn = ML.enabled; ML.enabled = true;
        this.drawLayer(comp, ML, t, matte, cam, cache, opts, parentM, 1);
        ML.is_track_matte = saved; ML.enabled = savedEn;
        matteMode = { 5013: 1, 5014: 2, 5015: 3, 5016: 4 }[L.track_matte_type] || 1;
      }
    }
    const mode = BLEND[L.blending_mode] ?? 0;
    if (mode === 0) {
      const gl = g.gl;
      g.run('layer', out, { uOpacity: op, uMode: 10, uMatteMode: matteMode, uHasMask: 0 }, { uTex: tg, uDst: g.blank, uMatte: matte, uMask: null }, quad, [gl.ONE, gl.ONE_MINUS_SRC_ALPHA]);
    } else {
      const dst = g.target(out.w, out.h);
      g.copy(out, dst);
      g.run('layer', out, { uOpacity: op, uMode: mode, uMatteMode: matteMode, uHasMask: 0 }, { uTex: tg, uDst: dst, uMatte: matte, uMask: null }, quad);
      g.release(dst);
    }
    g.release(tg); if (matte) g.release(matte);
  }

  drawAdjustment(comp, L, t, out, op) {
    const g = this.g;
    const below = g.target(out.w, out.h); g.copy(out, below);
    const fx = this.applyEffects(comp, L, t, below, [0, 0, comp.w, comp.h], true);
    const mp = findM(L, 'ADBE Mask Parade');
    let mask = null;
    if (mp?.c?.length) mask = this.maskTarget(L, t, { tg: { w: out.w, h: out.h }, rect: [0, 0, comp.w, comp.h] });
    const dst = g.target(out.w, out.h); g.copy(out, dst);
    g.run('mix', out, { uK: op, uHasMask: mask ? 1 : 0 }, { uTex: fx, uDst: dst, uMask: mask });
    if (mask) g.deleteTex(mask);
    if (fx !== below) g.release(fx);
    g.release(below); g.release(dst);
  }

  // Render a frame of comp at time t with comp motion blur (shutter angle/phase) into the canvas.
  async frame(comp, t) {
    const g = this.g;
    const T = 1 / comp.fps;
    const mb = comp.motion_blur;
    const n = mb ? this.mbSamples : 1;
    const ang = (comp.shutter_angle ?? 180) / 360, ph = (comp.shutter_phase ?? -90) / 360;
    const acc = g.target(comp.w, comp.h); g.clear(acc);
    await this.prepare(comp, t);
    for (let i = 0; i < n; i++) {
      const ts = mb ? t + T * ph + T * ang * ((i + 0.5) / n) : t;
      await this.prepare(comp, ts);
      const f = this.renderComp(comp, ts, { tc: t });
      const dst = g.target(comp.w, comp.h); g.copy(acc, dst);
      g.run('add', acc, { uK: 1 / n }, { uTex: f, uDst: dst });
      g.release(dst); g.release(f);
    }
    return acc;
  }
}

function bezPath(sh) {
  const p = new Path2D(), v = sh.vtx, ti = sh.in, to = sh.out, n = v.length;
  if (!n) return p;
  p.moveTo(v[0][0], v[0][1]);
  const seg = (a, b) => p.bezierCurveTo(v[a][0] + to[a][0], v[a][1] + to[a][1], v[b][0] + ti[b][0], v[b][1] + ti[b][1], v[b][0], v[b][1]);
  for (let i = 0; i < n - 1; i++) seg(i, i + 1);
  if (sh.closed) { seg(n - 1, 0); p.closePath(); }
  return p;
}

// AE Curves: monotone cubic through control points (0..255) per channel.
function curvesLut(ch) {
  const mk = (pts) => {
    const out = new Uint8Array(256);
    if (!pts || pts.length < 2) { for (let i = 0; i < 256; i++) out[i] = i; return out; }
    const P = [...pts].sort((a, b) => a[0] - b[0]);
    for (let i = 0; i < 256; i++) {
      let k = 0;
      while (k < P.length - 2 && i > P[k + 1][0]) k++;
      const [x0, y0] = P[k], [x1, y1] = P[k + 1];
      const f = Math.min(1, Math.max(0, (i - x0) / (x1 - x0 || 1)));
      const s = f * f * (3 - 2 * f) * 0.35 + f * 0.65;
      out[i] = Math.max(0, Math.min(255, Math.round(y0 + (y1 - y0) * s)));
    }
    return out;
  };
  const rgb = mk(ch.rgb);
  const app = (c) => { const m = mk(ch[c]); return Uint8Array.from(rgb, (v) => m[v]); };
  return [app('red'), app('green'), app('blue')];
}
