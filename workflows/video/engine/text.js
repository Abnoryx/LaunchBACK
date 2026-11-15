// Text layers: font mapping, layout, and AE range/expression selectors, drawn per character on a 2D canvas.
import { evalProp, exprOf, textBounceAmount } from './anim.js';

// Licensed-free substitutes for the fonts used in the reference projects.
const FONT_MAP = [
  // Inter Tight at 0.975x matches SF Pro Display's set width (calibrated on "Solutions" in the 7th-reel render).
  [/^SFPro(Display|Text|Rounded)-(\w+)/, (m) => ({ family: 'Inter Tight Variable', weight: W[m[2]] ?? 500, sizeScale: 0.975 })],
  [/^Helvetica(Neue)?-?Bold/, () => ({ family: 'Inter Variable', weight: 700, tracking: -0.01 })],
  [/^HelveticaNow\w*-Black/, () => ({ family: 'Inter Variable', weight: 900 })],
  [/^HelveticaNow\w*-Bold/, () => ({ family: 'Inter Variable', weight: 800 })],
  // CoolveticaHv metrics in the saved layout are a fallback font's (YOURS is 0.72 em per glyph): use natural widths there
  [/^Helvetica-Compressed/, () => ({ family: 'League Gothic', weight: 400 })],
  [/^Coolvetica-(HeavyComp|Cram)/, () => ({ family: 'League Gothic', weight: 400 })],
  [/^CoolveticaHv/, () => ({ family: 'League Gothic', weight: 400, natural: true })],
  [/^Coolvetica/, () => ({ family: 'Archivo Narrow', weight: 700 })],
  [/^Helvetica/, () => ({ family: 'Inter Variable', weight: 400 })],
  [/^InkFree|BradleyHand|AdobeHandwriting/, () => ({ family: 'Patrick Hand', weight: 400 })],
  // Kokila's Latin glyphs have a small x-height: scale down, width is then fitted to AE's advances
  // the reel renders it narrower than AE's saved layout: natural Tinos widths at 0.77x (fit on "someone" and "buy")
  [/^Kokila/, () => ({ family: 'Tinos', weight: 700, sizeScale: 0.77, natural: true })],
  [/^Didot/, () => ({ family: 'Bodoni Moda', weight: 700 })],
  [/^TimesNewRoman\w*Bold/, () => ({ family: 'Tinos', weight: 700, italic: /Italic/ })],
  [/^TimesNewRoman/, () => ({ family: 'Tinos', weight: 400 })],
  // the user's free Coolvetica cuts (regular weights only)
  [/^CoolCompressed/, () => ({ family: 'Coolvetica Compressed', weight: 400 })],
  [/^CoolCondensed/, () => ({ family: 'Coolvetica Condensed', weight: 400 })],
  [/^CoolCrammed/, () => ({ family: 'Coolvetica Crammed', weight: 400 })],
  [/^CoolRegular/, () => ({ family: 'Coolvetica', weight: 400 })],
  [/^Arimo/, () => ({ family: 'Arimo', weight: 700 })],
  [/^Anton/, () => ({ family: 'Anton', weight: 400 })],
  [/^Montserrat-(\w+)/, (m) => ({ family: 'Inter Variable', weight: W[m[1]] ?? 800 })],
];
const W = { Thin: 100, ExtraLight: 200, Light: 300, Regular: 400, Medium: 500, Semibold: 600, SemiBold: 600, Bold: 700, ExtraBold: 800, Heavy: 800, Black: 900 };

export function mapFont(ps = 'SFProDisplay-Regular') {
  for (const [re, f] of FONT_MAP) {
    const m = ps.match(re);
    if (m) {
      const r = f(m);
      return { ...r, italic: /Italic|Oblique/.test(ps) };
    }
  }
  return { family: 'Inter Variable', weight: 400, italic: /Italic|Oblique/.test(ps) };
}

const find = (node, m) => (node?.c || []).find((c) => c.m === m);
const findDeep = (node, m) => {
  if (!node) return null;
  if (node.m === m) return node;
  for (const c of node.c || []) { const r = findDeep(c, m); if (r) return r; }
  return null;
};

// Smooth curve used by the selector Ease High / Ease Low controls.
function easeHL(f, low, high) {
  const x1 = low / 100, x2 = 1 - high / 100;
  if (x1 === 0 && x2 === 1) return f;
  // cubic bezier (x1,0) (x2,1): solve x(u)=f
  let lo = 0, hi = 1, u = f;
  for (let i = 0; i < 30; i++) {
    const m = 1 - u, x = 3 * m * m * u * x1 + 3 * m * u * u * x2 + u * u * u;
    if (x < f) lo = u; else hi = u;
    u = (lo + hi) / 2;
  }
  const m = 1 - u;
  return 3 * m * u * u + u * u * u;
}

function shuffled(n, seed) {
  const a = [...Array(n).keys()];
  let s = (seed * 9301 + 49297) % 233280 || 1;
  for (let i = n - 1; i > 0; i--) {
    s = (s * 9301 + 49297) % 233280;
    const j = Math.floor((s / 233280) * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Amount (0..1) of one Range Selector for each unit.
function rangeAmounts(sel, t, nUnits, ctx) {
  const ev = (m, d) => { const p = findDeep(sel, m); return p ? evalProp(p, t, ctx) : d; };
  const adv = find(sel, 'ADBE Text Range Advanced');
  const shape = adv ? (evalProp(find(adv, 'ADBE Text Range Shape'), t) ?? 1) : 1;
  const units = adv ? (evalProp(find(adv, 'ADBE Text Range Units'), t) ?? 1) : 1;
  const low = adv ? (evalProp(find(adv, 'ADBE Text Levels Min Ease'), t) ?? 0) : 0;
  const high = adv ? (evalProp(find(adv, 'ADBE Text Levels Max Ease'), t) ?? 0) : 0;
  const amount = (adv ? (evalProp(find(adv, 'ADBE Text Selector Max Amount'), t) ?? 100) : 100) / 100;
  const smooth = (adv ? (evalProp(find(adv, 'ADBE Text Levels Smoothness'), t) ?? 100) : 100) / 100;
  const random = adv ? !!evalProp(find(adv, 'ADBE Text Randomize Order'), t) : false;
  const seed = adv ? (evalProp(find(adv, 'ADBE Text Random Seed'), t) ?? 0) : 0;
  let S, E, O;
  if (units === 2) { // index units
    S = (ev('ADBE Text Index Start', 0) / nUnits) * 100; E = (ev('ADBE Text Index End', nUnits) / nUnits) * 100; O = (ev('ADBE Text Index Offset', 0) / nUnits) * 100;
  } else {
    S = ev('ADBE Text Percent Start', 0); E = ev('ADBE Text Percent End', 100); O = ev('ADBE Text Percent Offset', 0);
  }
  if (S > E) [S, E] = [E, S];
  const lo = S + O, hi = E + O, w = Math.max(hi - lo, 1e-6);
  const order = random ? shuffled(nUnits, Math.round(seed) + 1) : null;
  const out = new Array(nUnits);
  for (let k = 0; k < nUnits; k++) {
    const i = order ? order[k] : k;
    const a0 = (i / nUnits) * 100, a1 = ((i + 1) / nUnits) * 100, c = (a0 + a1) / 2;
    let v;
    switch (shape) {
      case 2: v = (c - lo) / w; break;               // ramp up
      case 3: v = 1 - (c - lo) / w; break;           // ramp down
      case 4: v = 1 - Math.abs(((c - lo) / w) * 2 - 1); break; // triangle
      case 5: { const x = ((c - lo) / w) * 2 - 1; v = Math.sqrt(Math.max(0, 1 - x * x)); break; } // round
      case 6: { const x = (c - lo) / w; v = x <= 0 || x >= 1 ? 0 : 0.5 - 0.5 * Math.cos(x * 2 * Math.PI); break; } // smooth
      default: { // square: coverage of the unit, blended by smoothness
        const cov = Math.max(0, Math.min(a1, hi) - Math.max(a0, lo)) / (a1 - a0);
        v = smooth >= 0.5 ? cov : cov >= 0.5 ? 1 : 0;
      }
    }
    if (shape >= 2 && shape <= 3) v = easeHL(Math.min(1, Math.max(0, v)), low, high);
    out[k] = Math.min(1, Math.max(0, v)) * amount;
  }
  return out;
}

function unitIndex(text, basedOn) {
  // returns per-character unit index and unit count. basedOn: 1 chars, 2 chars w/o spaces, 3 words, 4 lines
  const idx = new Array(text.length).fill(-1);
  let n = 0;
  if (basedOn === 3) {
    let inWord = false;
    for (let i = 0; i < text.length; i++) {
      const sp = /\s/.test(text[i]);
      if (!sp && !inWord) n++;
      inWord = !sp;
      idx[i] = sp ? -1 : n - 1;
    }
  } else if (basedOn === 4) {
    for (let i = 0; i < text.length; i++) { if (text[i] === '\r' || text[i] === '\n') n++; idx[i] = n; }
    n++;
  } else {
    for (let i = 0; i < text.length; i++) {
      if (basedOn === 2 && /\s/.test(text[i])) continue;
      idx[i] = n++;
    }
  }
  return { idx, n: Math.max(n, 1) };
}

// Evaluate all animators: per-character overrides.
export function textAnimation(layer, tComp, ctx) {
  const textGrp = layer.props.find((p) => p.m === 'ADBE Text Properties');
  const docProp = find(textGrp, 'ADBE Text Document');
  const doc = docProp ? evalProp(docProp, tComp) : null;
  const base = layer.text || {};
  const text = (doc && doc._text ? doc.text : base.text) ?? '';
  const font = (doc && doc._text && doc.font) || base.font;
  const size = (doc && doc._text && doc.size) || base.font_size || 72;
  const fill = (doc && doc._text && doc.fill) || base.fill_color || [1, 1, 1];
  const tracking = (doc && doc._text && doc.tracking) ?? base.tracking ?? 0;
  const chars = [...text].map((ch) => ({ ch, op: 1, dx: 0, dy: 0, dz: 0, sx: 1, sy: 1, rot: 0, blur: 0, fill: null, fillAmt: 0, track: 0 }));
  const anims = find(textGrp, 'ADBE Text Animators');
  for (const an of anims?.c || []) {
    const props = find(an, 'ADBE Text Animator Properties');
    const sels = find(an, 'ADBE Text Selectors');
    // Combined per-char amount across selectors.
    let amt = chars.map(() => 1);
    let first = true;
    for (const sel of sels?.c || []) {
      let a;
      if (sel.m === 'ADBE Text Selector') {
        const adv = find(sel, 'ADBE Text Range Advanced');
        const basedOn = adv ? (evalProp(find(adv, 'ADBE Text Range Type2'), tComp) ?? 1) : 1;
        const { idx, n } = unitIndex(text, basedOn);
        const u = rangeAmounts(sel, tComp, n, ctx);
        a = idx.map((k) => (k < 0 ? (basedOn === 3 ? 0 : 0) : u[k]));
        if (basedOn === 3) a = a.map((v, i) => (idx[i] < 0 ? (u[Math.max(0, idx[i + 1] ?? 0)] ?? 0) : v));
      } else if (sel.m === 'ADBE Text Expressible Selector') {
        const ap = findDeep(sel, 'ADBE Text Expressible Amount');
        const e = ap && exprOf(ap);
        const tLocal = tComp - (layer.in_point ?? 0);
        if (e && e.kind === 'textBounce') a = chars.map((_, i) => textBounceAmount(e, i, chars.length, tLocal, ctx) / 100);
        else if (e && e.kind === 'lastChar') a = chars.map((_, i) => (i === chars.length - 1 ? 1 : 0));
        else a = chars.map(() => (ap ? (evalProp(ap, tComp) ?? 100) : 100) / 100);
      } else continue; // wiggly selectors: ignored
      amt = first ? a : amt.map((v, i) => Math.min(1, v + a[i]));
      first = false;
    }
    for (const p of props?.c || []) {
      if (p.syn) continue; // filler default the creator never added
      const v = evalProp(p, tComp, ctx);
      chars.forEach((c, i) => {
        const k = amt[i];
        if (!k) return;
        switch (p.m) {
          case 'ADBE Text Opacity': c.op *= 1 + (v / 100 - 1) * Math.min(1, Math.max(0, k)); break;
          case 'ADBE Text Position 3D': c.dx += v[0] * k; c.dy += v[1] * k; c.dz += (v[2] || 0) * k; break;
          case 'ADBE Text Scale 3D': c.sx *= 1 + (v[0] / 100 - 1) * k; c.sy *= 1 + (v[1] / 100 - 1) * k; break;
          case 'ADBE Text Rotation': c.rot += v * k; break;
          case 'ADBE Text Rotation X': c.rx = (c.rx || 0) + v * k; break;
          case 'ADBE Text Rotation Y': c.ry = (c.ry || 0) + v * k; break;
          case 'ADBE Text Blur': c.blur += (Array.isArray(v) ? v[0] : v) * Math.abs(k); break;
          case 'ADBE Text Fill Color': c.fill = v; c.fillAmt = Math.max(c.fillAmt, Math.min(1, k)); break;
          case 'ADBE Text Tracking Amount': c.track += v * k; break;
          case 'ADBE Text Character Offset': c.charOff = (c.charOff || 0) + v * k; break;
          default: break;
        }
      });
    }
  }
  return { text, font, size, fill, tracking, chars, justify: base.justification ?? 7413, leading: base.leading,
    stroke: base.apply_stroke ? base.stroke_color : null, strokeWidth: base.stroke_width || 0,
    box: base.box_text ? base.box_text_size : null,
    // AE's own saved layout (line baselines + per-glyph advances) and style runs; valid while the text is unchanged
    lines: base.lines && text === base.text ? base.lines : null, runs: base.runs || null,
    caps: !!base.all_caps, vscale: base.vertical_scale ?? 1 };
}

// Lay out and draw using AE's cached layout: exact line and glyph positions whatever the substitute font is.
function drawTextAE(anim, ss) {
  const meas = drawText._m || (drawText._m = document.createElement('canvas').getContext('2d'));
  const runAt = (i) => (anim.runs || []).find((r) => i >= r.s && i < r.e) || {};
  const glyphs = [];
  let maxSize = anim.size;
  for (const ln of anim.lines) {
    // AE's cached advances exclude tracking and (for point text) justification: add both here
    const row = [];
    let trAcc = 0, xAcc = 0;
    for (let k = 0; k < ln.e - ln.s; k++) {
      const i = ln.s + k;
      let ch = anim.text[i];
      if (ch === undefined || ch === '\r' || ch === '\n' || ch === '\u0003') continue;
      const r = runAt(i);
      const size = r.size || anim.size, font = r.font || anim.font;
      maxSize = Math.max(maxSize, size);
      const a0 = k ? ln.adv[k - 1] : 0, a1 = ln.adv[k] ?? a0;
      if (anim.caps || r.caps) ch = ch.toUpperCase();
      const fm = mapFont(font);
      let w = Math.max(0, a1 - a0);
      if (fm.natural) { meas.font = `${fm.italic ? 'italic ' : ''}${fm.weight} ${size * (fm.sizeScale || 1)}px "${fm.family}"`; w = meas.measureText(ch).width; }
      row.push({ c: anim.chars[i], ch, x: ln.x + xAcc + trAcc, w, y: ln.y - (r.bshift || 0), size, font,
        fill: r.fill || anim.fill, vs: r.vs ?? anim.vscale ?? 1 });
      xAcc += w;
      trAcc += ((r.tracking ?? anim.tracking) / 1000) * size;
    }
    while (row.length && /\s/.test(row[row.length - 1].ch)) row.pop();
    if (!row.length) continue;
    const lw = row[row.length - 1].x + row[row.length - 1].w - ln.x;
    const J = anim.justify, bw = anim.box ? anim.box[0] : 0;
    const off = anim.box ? (J === 7415 ? (bw - lw) / 2 : J === 7414 ? bw - lw : 0) : (J === 7415 ? -lw / 2 : J === 7414 ? -lw : 0);
    for (const gl of row) { gl.x += off; glyphs.push(gl); }
  }
  if (!glyphs.length) return null;
  let maxBlur = 0, maxD = 0;
  for (const g of glyphs) { maxBlur = Math.max(maxBlur, g.c?.blur || 0); maxD = Math.max(maxD, Math.abs(g.c?.dx || 0), Math.abs(g.c?.dy || 0)); }
  const minX = Math.min(...glyphs.map((g) => g.x)), maxX = Math.max(...glyphs.map((g) => g.x + g.w));
  const minY = Math.min(...glyphs.map((g) => g.y - g.size * 1.05)), maxY = Math.max(...glyphs.map((g) => g.y + g.size * 0.4));
  const pad = Math.ceil((maxBlur * 3 + maxD + maxSize * 0.3) * ss) + 8;
  const cv = document.createElement('canvas');
  cv.width = Math.max(4, Math.ceil((maxX - minX) * ss + 2 * pad)); cv.height = Math.max(4, Math.ceil((maxY - minY) * ss + 2 * pad));
  const ctx = cv.getContext('2d');
  ctx.textBaseline = 'alphabetic';
  const ox = pad - minX * ss, oy = pad - minY * ss;
  const css = (rgb) => `rgb(${rgb.map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255)).join(',')})`;
  for (const g of glyphs) {
    const c = g.c;
    if (!c || c.op <= 0.002 || /\s/.test(g.ch)) continue;
    if (c.charOff) g.ch = shiftChar(g.ch, Math.round(c.charOff));
    const f = mapFont(g.font);
    const fs = g.size * (f.sizeScale || 1) * ss;
    ctx.font = `${f.italic ? 'italic ' : ''}${f.weight} ${fs}px "${f.family}"`;
    meas.font = ctx.font;
    const nw = meas.measureText(g.ch).width;
    const hs = nw > 0 && g.w > 0 ? Math.min(1.6, Math.max(0.6, (g.w * ss) / nw)) : 1;
    ctx.save();
    ctx.globalAlpha = Math.min(1, c.op);
    const col = c.fill && c.fillAmt ? g.fill.map((v, i) => v + (c.fill[i] - v) * c.fillAmt) : g.fill;
    ctx.fillStyle = css(col);
    ctx.filter = c.blur > 0.3 ? `blur(${(c.blur * ss) / 2}px)` : 'none';
    ctx.translate(ox + (g.x + g.w / 2 + c.dx) * ss, oy + (g.y + c.dy) * ss);
    if (c.rot) ctx.rotate((c.rot * Math.PI) / 180);
    ctx.scale(c.sx * hs, c.sy * (g.vs > 3 ? g.vs / 100 : g.vs));
    if (anim.stroke && anim.strokeWidth > 0) { ctx.lineJoin = 'round'; ctx.strokeStyle = css(anim.stroke); ctx.lineWidth = (anim.strokeWidth * ss) / hs; ctx.strokeText(g.ch, -nw / 2, 0); }
    ctx.fillText(g.ch, -nw / 2, 0);
    ctx.restore();
  }
  return { canvas: cv, ox: ox / ss, oy: oy / ss, scale: ss };
}

// AE Character Offset with "Preserve Case & Digits": wraps within a-z, A-Z, 0-9
function shiftChar(ch, n) {
  const wrap = (base, len) => String.fromCharCode(base + ((((ch.charCodeAt(0) - base + n) % len) + len) % len));
  if (/[a-z]/.test(ch)) return wrap(97, 26);
  if (/[A-Z]/.test(ch)) return wrap(65, 26);
  if (/[0-9]/.test(ch)) return wrap(48, 10);
  return ch;
}

const fontsReady = new Set();
export async function ensureFont(f) {
  const key = `${f.italic ? 'italic ' : ''}${f.weight} 64px "${f.family}"`;
  if (fontsReady.has(key)) return;
  await document.fonts.load(key);
  fontsReady.add(key);
}

// Draw the text into a canvas. Returns {canvas, ox, oy, scale}: layer-space origin of the canvas.
export function drawText(anim, ss = 2) {
  if (anim.lines) { const r = drawTextAE(anim, ss); if (r) return r; }
  const f = mapFont(anim.font);
  const size = anim.size * (f.sizeScale || 1);
  const fontStr = `${f.italic ? 'italic ' : ''}${f.weight} ${size * ss}px "${f.family}"`;
  const meas = drawText._m || (drawText._m = document.createElement('canvas').getContext('2d'));
  meas.font = fontStr;
  let lines = anim.text.split(/\r\n|\r|\n/);
  if (anim.box && anim.box[0] > 0) { // AE paragraph text: wrap to the box width
    const maxW = anim.box[0] * ss, out = [];
    for (const ln of lines) {
      let cur = '';
      for (const w of ln.split(/ +/)) { const tr = cur ? cur + ' ' + w : w; if (meas.measureText(tr).width > maxW && cur) { out.push(cur); cur = w; } else cur = tr; }
      out.push(cur);
    }
    lines = out;
  }
  const lead = (anim.leading || size * 1.2) * ss;
  const track = ((anim.tracking / 1000) + (f.tracking || 0)) * size * ss;
  // layout chars
  const glyphs = [];
  let ci = 0, maxW = 0;
  lines.forEach((ln, li) => {
    let x = 0;
    const row = [];
    for (const ch of [...ln]) {
      const c = anim.chars[ci++];
      const w = meas.measureText(ch).width;
      row.push({ c, ch, x, w });
      x += w + track + (c ? (c.track / 1000) * size * ss : 0);
    }
    ci++; // newline char
    const lw = x - track;
    maxW = Math.max(maxW, lw);
    const jx = anim.justify === 7415 ? -lw / 2 : anim.justify === 7414 ? -lw : 0;
    row.forEach((g) => { g.x += jx; g.y = li * lead; glyphs.push(g); });
  });
  let maxBlur = 0, maxD = 0;
  for (const g of glyphs) { maxBlur = Math.max(maxBlur, g.c?.blur || 0); maxD = Math.max(maxD, Math.abs(g.c?.dx || 0), Math.abs(g.c?.dy || 0)); }
  const pad = Math.ceil((maxBlur * 3 + maxD + size * 0.6) * ss) + 8;
  const asc = size * ss * 1.0;
  const W = Math.ceil(maxW + 2 * pad), H = Math.ceil(lead * (lines.length - 1) + asc + size * ss * 0.4 + 2 * pad);
  const cv = document.createElement('canvas');
  cv.width = Math.max(4, W); cv.height = Math.max(4, H);
  const ctx = cv.getContext('2d');
  ctx.font = fontStr;
  ctx.textBaseline = 'alphabetic';
  const ox = pad + (anim.justify === 7415 ? maxW / 2 : anim.justify === 7414 ? maxW : 0);
  const oy = pad + asc;
  const css = (rgb) => `rgb(${rgb.map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255)).join(',')})`;
  for (const g of glyphs) {
    const c = g.c;
    if (!c || c.op <= 0.002 || /\s/.test(g.ch)) continue;
    if (c.charOff) g.ch = shiftChar(g.ch, Math.round(c.charOff));
    ctx.save();
    ctx.globalAlpha = Math.min(1, c.op);
    const col = c.fill && c.fillAmt ? anim.fill.map((v, i) => v + (c.fill[i] - v) * c.fillAmt) : anim.fill;
    ctx.fillStyle = css(col);
    ctx.filter = c.blur > 0.3 ? `blur(${(c.blur * ss) / 2}px)` : 'none';
    const cx = ox + g.x + g.w / 2 + c.dx * ss, cy = oy + g.y + c.dy * ss;
    ctx.translate(cx, cy);
    if (c.rot) ctx.rotate((c.rot * Math.PI) / 180);
    if (c.sx !== 1 || c.sy !== 1) ctx.scale(c.sx, c.sy);
    if (anim.stroke && anim.strokeWidth > 0) { ctx.lineJoin = 'round'; ctx.strokeStyle = css(anim.stroke); ctx.lineWidth = anim.strokeWidth * ss; if (anim.strokeOver) { ctx.fillText(g.ch, -g.w / 2, 0); ctx.strokeText(g.ch, -g.w / 2, 0); } else { ctx.strokeText(g.ch, -g.w / 2, 0); ctx.fillText(g.ch, -g.w / 2, 0); } }
    else ctx.fillText(g.ch, -g.w / 2, 0);
    ctx.restore();
  }
  return { canvas: cv, ox: ox / ss, oy: oy / ss, scale: ss, fontInfo: f };
}

// One glyph rasterised for per-character 3D: canvas + baseline-centre anchor (in px at scale ss).
export function glyphSprite(ch, fontPS, size, fill, ss) {
  const f = mapFont(fontPS);
  const fs = size * (f.sizeScale || 1) * ss;
  const font = `${f.italic ? 'italic ' : ''}${f.weight} ${fs}px "${f.family}"`;
  const meas = drawText._m || (drawText._m = document.createElement('canvas').getContext('2d'));
  meas.font = font;
  const w = Math.ceil(meas.measureText(ch).width) + 8, h = Math.ceil(fs * 1.5) + 8;
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const c = cv.getContext('2d'); c.font = font; c.textBaseline = 'alphabetic';
  c.fillStyle = `rgb(${fill.map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255)).join(',')})`;
  const ax = w / 2, ay = 4 + fs * 1.05;
  c.fillText(ch, ax - meas.measureText(ch).width / 2, ay);
  return { canvas: cv, ax: ax / ss, ay: ay / ss, w: w / ss, h: h / ss };
}
