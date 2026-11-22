// Render a comp from a dumped .aep project with the WebGL engine in headless Chromium.
// usage: node render.mjs --project dump.json --footage <dir> --comp "name" --from 8.5 --to 13.6 --out out.mp4 [--samples 8] [--fps N] [--frames-dir dir]
import fs from 'fs';
import path from 'path';
import { spawn, execFileSync } from 'child_process';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const HERE = path.dirname(new URL(import.meta.url).pathname);
const project = JSON.parse(fs.readFileSync(args.project));
const comp = project.comps.find((c) => c.name === args.comp);
const fps = +(args.fps || comp.fps);
const from = +(args.from || 0), to = +(args.to || comp.dur);
const samples = +(args.samples || 8);
const preview = !!args.preview;   // --preview 1|<width>: no 2x supersampling, output scaled to 360 px (or <width>) wide
const PW = preview && +args.preview > 1 ? +args.preview : 360;
const cacheDir = args.cache || '/tmp/engine-cache';
fs.mkdirSync(cacheDir, { recursive: true });

// index footage files by basename
const files = new Map();
const walk = (d) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else files.set(e.name.normalize('NFC'), p); } };
for (const d of (args.footage || '').split(',').filter(Boolean)) walk(d);
const findFile = (name) => files.get(decodeURIComponent(name).normalize('NFC')) || [...files.entries()].find(([k]) => k.replace(/#U[0-9A-F]{4}/g, '') === name.replace(/[^\x00-\x7f]/g, ''))?.[1];

const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif' };
const GPU_ARGS = process.env.RENDER_GPU ? ['--use-angle=vulkan', '--enable-features=Vulkan,VulkanFromANGLE,DefaultANGLEVulkan', '--ignore-gpu-blocklist', '--enable-gpu', '--headless=new'] : [];   // RENDER_GPU=1: real GPU (Kaggle T4)
const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--disable-web-security', ...GPU_ARGS] });
const page = await browser.newPage();
page.on('console', (m) => { if (m.type() === 'warning' || m.type() === 'error') console.error('[page]', m.text()); });
page.on('pageerror', (e) => console.error('[pageerror]', e.message));
await page.route('http://engine.local/**', async (route) => {
  const u = new URL(route.request().url());
  const p = decodeURIComponent(u.pathname);
  try {
    if (p === '/') return route.fulfill({ path: path.join(HERE, 'page.html') });
    if (p === '/project.json') return route.fulfill({ body: JSON.stringify(project), contentType: 'application/json' });
    if (p === '/config.json') return route.fulfill({ body: JSON.stringify({ comp: args.comp, samples, supersample: preview ? 1 : undefined, blurK: args.blurk ? +args.blurk : undefined, modelOpts: args.modelopts ? JSON.parse(fs.readFileSync(args.modelopts)) : {}, luts: args.luts ? JSON.parse(fs.readFileSync(args.luts)) : {} }), contentType: 'application/json' });
    if (p.startsWith('/engine/')) return route.fulfill({ path: path.join(HERE, p.slice(8)), contentType: MIME[path.extname(p)] });
    if (p.startsWith('/nm/')) return route.fulfill({ path: path.join(HERE, '..', 'node_modules', p.slice(4)), contentType: MIME[path.extname(p)] || undefined });
    if (p.startsWith('/file/')) return route.fulfill({ path: p.slice(5) });
    if (p.startsWith('/asset/')) {
      const f = findFile(p.slice(7));
      if (!f) return route.fulfill({ status: 404 });
      const ext = path.extname(f).toLowerCase();
      if (['.png', '.jpg', '.jpeg', '.gif', '.webp'].includes(ext)) return route.fulfill({ path: f, contentType: MIME[ext] });
      if (ext === '.glb') return route.fulfill({ path: f, contentType: 'model/gltf-binary' });
      // psd/ai/other stills: rasterise once via ImageMagick
      const out = path.join(cacheDir, 'still_' + path.basename(f) + '.png');
      if (!fs.existsSync(out)) { try { execFileSync('convert', [f + '[0]', '-background', 'none', out], { stdio: 'ignore' }); } catch { return route.fulfill({ status: 404 }); } }
      return route.fulfill({ path: out, contentType: 'image/png' });
    }
    if (p.startsWith('/vid/')) {
      const [, , id, ms] = p.split('/');
      const name = u.searchParams.get('name');
      const f = findFile(name);
      if (!f) return route.fulfill({ status: 404 });
      const out = path.join(cacheDir, `v${id}_${ms}`);
      if (!fs.existsSync(out)) {
        const alpha = /\.(gif|mov|webm|png)$/i.test(f);
        try { execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(parseInt(ms) / 1000), '-i', f, '-frames:v', '1', ...(alpha ? ['-pix_fmt', 'rgba', '-f', 'image2', '-c:v', 'png'] : ['-q:v', '2', '-f', 'image2', '-c:v', 'mjpeg']), out]); } catch { return route.fulfill({ status: 404 }); }
        // a seek past the clip's end (or any seek in a short GIF) writes nothing: decode all frames once, take the one at
        // this time, holding the last
        if (!fs.existsSync(out)) try {
          const dir = path.join(cacheDir, `all_v${id}`);
          if (!fs.existsSync(dir)) { fs.mkdirSync(dir + '.tmp', { recursive: true }); execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', f, '-vsync', '0', '-pix_fmt', 'rgba', path.join(dir + '.tmp', '%05d.png')]); fs.renameSync(dir + '.tmp', dir); }
          const all = fs.readdirSync(dir).sort();
          const rate = String(execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate', '-of', 'csv=p=0', f])).trim().split('/');
          const fr = +rate[0] / (+rate[1] || 1) || 30;
          const src = path.join(dir, all[Math.min(all.length - 1, Math.floor(parseInt(ms) / 1000 * fr))]);
          execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', src, ...(alpha ? ['-pix_fmt', 'rgba', '-f', 'image2', '-c:v', 'png'] : ['-q:v', '2', '-f', 'image2', '-c:v', 'mjpeg']), out]);
        } catch {}
        if (!fs.existsSync(out)) return route.fulfill({ status: 404 });
      }
      return route.fulfill({ path: out, contentType: /\.(gif|mov|webm|png)$/i.test(f) ? 'image/png' : 'image/jpeg' });
    }
    return route.fulfill({ status: 404 });
  } catch (e) { console.error('route', p, e.message); return route.fulfill({ status: 500 }); }
});
await page.goto('http://engine.local/');
await page.waitForFunction('window.ready === true', null, { timeout: 120000 });

// --serve PORT: keep the page up and answer POST /render {project?, comp?, times:[..], w, h} with small RGBA frames
if (args.serve) {
  const http = await import('http');
  const srv = http.createServer(async (req, res) => {
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', async () => {
      try {
        const q = JSON.parse(body || '{}');
        if (q.project) await page.evaluate(([pj, cn]) => window.setProject(pj, cn), [q.project, q.comp]);
        const frames = [];
        for (const t of q.times || []) frames.push(await page.evaluate(([t, w, h]) => window.renderSmall(t, w, h), [t, q.w || 360, q.h || 640]));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ frames }));
      } catch (e) { res.writeHead(500); res.end(String(e && e.stack || e)); }
    });
  });
  srv.listen(+args.serve, '127.0.0.1', () => console.log('serving on', args.serve));
  await new Promise(() => {});
}
const n = Math.round((to - from) * fps);
const framesDir = args['frames-dir'];
if (framesDir) fs.mkdirSync(framesDir, { recursive: true });
const OW = preview ? PW : comp.w, OH = preview ? 2 * Math.round(comp.h * PW / comp.w / 2) : comp.h;   // even for x264
const ff = args.out ? spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${OW}x${OH}`, '-r', String(fps), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-tune', 'grain', '-pix_fmt', 'yuv420p', args.out], { stdio: ['pipe', 'inherit', 'inherit'] }) : null;
const t0 = Date.now();
for (let k = 0; k < n; k++) {
  const t = from + k / fps;
  const b64 = preview ? await page.evaluate(([t, w, h]) => window.renderSmall(t, w, h), [t, OW, OH]) : await page.evaluate((t) => window.renderFrame(t), t);
  const buf = Buffer.from(b64, 'base64');
  if (ff) await new Promise((r) => (ff.stdin.write(buf) ? r() : ff.stdin.once('drain', r)));
  if (framesDir && (args.every ? k % +args.every === 0 : true)) {
    const raw = path.join(framesDir, `f${String(Math.round(t * comp.fps)).padStart(5, '0')}.rgba`);
    fs.writeFileSync(raw, buf);
    execFileSync('convert', ['-size', `${OW}x${OH}`, '-depth', '8', 'rgba:' + raw, raw.replace('.rgba', '.png')]);
    fs.unlinkSync(raw);
  }
  if (k % 10 === 0) console.log(`frame ${k + 1}/${n} t=${t.toFixed(3)} ${((Date.now() - t0) / (k + 1) / 1000).toFixed(2)}s/frame`);
}
if (ff) { ff.stdin.end(); await new Promise((r) => ff.on('close', r)); }
console.log('warnings:', JSON.stringify(await page.evaluate(() => window.engineWarnings())));
await browser.close();
