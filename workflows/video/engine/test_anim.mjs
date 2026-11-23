// Compare engine keyframe evaluation with py_aep's value_at_time samples.
import fs from 'fs';
import { keyValue } from './anim.js';
const [,, dumpPath, refPath] = process.argv;
const dump = JSON.parse(fs.readFileSync(dumpPath));
const ref = JSON.parse(fs.readFileSync(refPath));
const comps = {}; for (const c of dump.comps) comps[c.name] ??= c;
function find(node, mns) {
  if (!mns.length) return node;
  for (const c of node.c || []) if (c.m === mns[0]) { const r = find(c, mns.slice(1)); if (r) return r; }
  return null;
}
let n = 0, bad = 0, worst = [];
for (const r of ref) {
  const [cn, li, ...mns] = r.path;
  const L = comps[cn]?.layers.find((l) => l.i === li); if (!L) continue;
  const top = L.props.find((p) => p.m === mns[0]); if (!top) continue;
  const p = find(top, mns.slice(1)); if (!p || !p.k) continue;
  r.ts.forEach((t, j) => {
    const a = keyValue(p, t), b = r.vals[j];
    const av = [].concat(a), bv = [].concat(b);
    const isAng = /Orientation|Rotate/.test(mns.at(-1)); const err = Math.max(...bv.map((x, d) => { let e = Math.abs(x - av[d]); if (isAng) { e = e % 360; e = Math.min(e, 360 - e); } return e / Math.max(1, Math.abs(x)); }));
    n++; if (err > 1e-3) { bad++; worst.push([err, cn, L.name, mns.at(-1), t.toFixed(3), JSON.stringify(a).slice(0, 60), JSON.stringify(b).slice(0, 60)]); }
  });
}
worst.sort((x, y) => y[0] - x[0]);
console.log(`samples ${n}, mismatches ${bad} (${(100 * bad / n).toFixed(1)}%)`);
for (const w of worst.slice(0, 12)) console.log(w.join(' | '));
