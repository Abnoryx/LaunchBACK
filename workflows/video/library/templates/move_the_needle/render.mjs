import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {access, mkdir, readFile, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {parseArgs} from 'node:util';
import {chromium} from 'playwright';
import {serve} from './preview.mjs';
import {makeShot} from './src/shot.mjs';

const {values} = parseArgs({options:{out:{type:'string'},frames:{type:'string'},from:{type:'string'},count:{type:'string'}}});
const shot = makeShot(JSON.parse(await readFile(new URL('./shot.json',import.meta.url))));
const start = Number(values.from ?? 0);
const numFrames = Number(values.count ?? shot.frameCount - start);
if (!Number.isInteger(start) || !Number.isInteger(numFrames) || start < 0 || numFrames < 1 || start + numFrames > shot.frameCount) {
  throw new Error('Frame range is outside the shot.');
}
const out = resolve(values.out ?? 'move-the-needle.mp4');
const server = await serve();
let browser;
let encoder;
try {
  let executablePath = process.env.CHROMIUM_PATH;
  if (!executablePath) {
    try { await access('/usr/bin/chromium'); executablePath = '/usr/bin/chromium'; } catch {}
  }
  browser = await chromium.launch({executablePath,args:['--enable-unsafe-swiftshader','--no-sandbox']});
  const page = await browser.newPage({viewport:{width:shot.width,height:shot.height}});
  const pageFailure = new Promise((_, reject) => page.once('pageerror',reject));
  await page.goto(server.url + '/?capture');
  await Promise.race([page.waitForFunction(() => window.shotReady, undefined, {timeout:15000}),pageFailure]);
  if (values.frames) await mkdir(values.frames,{recursive:true});
  encoder = spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(shot.fps),
    '-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-preset','medium','-crf','14','-pix_fmt','yuv420p',
    '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',out],
  {stdio:['pipe','inherit','inherit']});
  const finished = once(encoder,'exit');
  encoder.stdin.on('error', (error) => { if (error.code !== 'EPIPE') console.error(error); });
  for (let index = start; index < start + numFrames; index++) {
    const base64 = await page.evaluate((i) => window.captureFrame(i),index);
    const frame = Buffer.from(base64,'base64');
    if (values.frames) await writeFile(resolve(values.frames,'frame-' + String(index).padStart(3,'0') + '.png'),frame);
    if (!encoder.stdin.write(frame)) await Promise.race([once(encoder.stdin,'drain'),finished.then(() => { throw new Error('FFmpeg stopped early.'); })]);
  }
  encoder.stdin.end();
  const [exitCode] = await finished;
  if (exitCode !== 0) throw new Error('FFmpeg exited with code ' + exitCode);
  console.log('Rendered ' + numFrames + ' frames to ' + out);
} finally {
  if (encoder && encoder.exitCode === null) encoder.kill();
  if (browser) await browser.close();
  server.close();
}
