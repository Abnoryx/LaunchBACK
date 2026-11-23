// Per-frame camera tracks for every scene of a dumped AE project, evaluated with the engine's AE keyframe maths.
// usage: node camtrack.mjs <project.json> <rootComp> <out.tsv>
// For each master frame: which comp holds the active camera, camera world position (x,y,z), zoom, and the
// on-screen scale of the z=0 plane (1050-zoom convention: s = zoom / (0 - camZ) for a camera looking +z).
import fs from 'fs';
import { evalProp } from './anim.js';

const [, , projPath, rootName, outPath] = process.argv;
const P = JSON.parse(fs.readFileSync(projPath));
const byId = new Map(P.comps.map((c) => [c.id, c]));
const root = P.comps.find((c) => c.name === rootName);

const find = (node, m) => (node?.c || node?.props || []).find((x) => x.m === m);
const tg = (L) => find(L, 'ADBE Transform Group');
const val = (L, m, t, d) => { const p = find(tg(L), m); return p ? evalProp(p, t) : d; };

// translation-only world position of a layer's origin-chain point (camera rigs here use translate + nulls)
function worldPoint(comp, L, t, local = [0, 0, 0]) {
  let p = local.slice();
  let cur = L;
  while (cur) {
    const a = cur.type === 'CameraLayer' ? [0, 0, 0] : val(cur, 'ADBE Anchor Point', t, [0, 0, 0]);
    const sep = ['ADBE Position_0', 'ADBE Position_1', 'ADBE Position_2'].map((m) => find(tg(cur), m));
    let pos = val(cur, 'ADBE Position', t, [comp.w / 2, comp.h / 2, 0]);
    if (sep.some((s) => s && s.k)) pos = sep.map((s, i) => (s ? evalProp(s, t) : pos[i] || 0));
    const sc = cur.type === 'CameraLayer' ? [100, 100, 100] : val(cur, 'ADBE Scale', t, [100, 100, 100]);
    p = [0, 1, 2].map((i) => (pos[i] || 0) + ((p[i] - (a[i] || 0)) * (sc[i] ?? 100)) / 100);
    cur = cur.parent != null ? comp.layers.find((x) => x.i === cur.parent) : null;
  }
  return p;
}

const active = (L, t) => L.enabled === true && t >= L.in_point - 1e-3 && t < L.out_point - 1e-3;
const localT = (L, t) => (t - (L.start_time || 0)) / ((L.stretch || 100) / 100);

// find the deepest visible comp that owns an active camera at master time t (topmost precomp layer wins)
function cameraAt(comp, t, depth = 0) {
  const cams = comp.layers.filter((L) => L.type === 'CameraLayer' && active(L, t)).sort((a, b) => a.i - b.i);
  const subs = comp.layers.filter((L) => L.src_id != null && byId.has(L.src_id) && active(L, t)).sort((a, b) => a.i - b.i);
  if (cams.length) {
    // a camera in this comp: check whether a precomp above it covers the frame (topmost layer wins)
    const topSub = subs.find((s) => s.i < cams[0].i && !s.adjustment_layer && depth < 6);
    if (topSub) { const r = cameraAt(byId.get(topSub.src_id), localT(topSub, t), depth + 1); if (r) return r; }
    const C = cams[0];
    const co = find(C, 'ADBE Camera Options Group');
    const zp = co && find(co, 'ADBE Camera Zoom');
    return { comp: comp.name, cam: C.name, t, pos: worldPoint(comp, C, t), zoom: zp ? evalProp(zp, t) : 1050 };
  }
  for (const s of subs) {
    if (s.adjustment_layer || depth > 6) continue;
    const r = cameraAt(byId.get(s.src_id), localT(s, t), depth + 1);
    if (r) return r;
  }
  return null;
}

const rows = ['frame\tt\tcomp\tcamera\tx\ty\tz\tzoom\tplane_scale\tdx\tdy\tdscale'];
let prev = null;
const n = Math.round(root.dur * root.fps);
for (let f = 0; f < n; f++) {
  const t = f / root.fps;
  const c = cameraAt(root, t);
  if (!c) { rows.push(`${f}\t${t.toFixed(3)}\t-\t-`); prev = null; continue; }
  const [x, y, z] = c.pos;
  const s = c.zoom / Math.max(1, -z);
  const same = prev && prev.comp === c.comp;
  const dx = same ? (x - prev.x) * s : 0, dy = same ? (y - prev.y) * s : 0, ds = same ? s / prev.s : 1;
  rows.push([f, t.toFixed(3), c.comp, c.cam, x.toFixed(1), y.toFixed(1), z.toFixed(1), c.zoom.toFixed(0), s.toFixed(3), dx.toFixed(1), dy.toFixed(1), ds.toFixed(4)].join('\t'));
  prev = { comp: c.comp, x, y, s };
}
fs.writeFileSync(outPath, rows.join('\n') + '\n');
console.log(`${n} frames -> ${outPath}`);
