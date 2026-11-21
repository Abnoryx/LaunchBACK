import {createServer} from 'node:http';
import {createReadStream} from 'node:fs';
import {stat} from 'node:fs/promises';
import {resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('.',import.meta.url)).replace(/[\\/]$/, '');
const types = {html:'text/html',js:'text/javascript',mjs:'text/javascript',json:'application/json',png:'image/png',webp:'image/webp',woff2:'font/woff2'};
export async function serve(port = 0) {
  const server = createServer(async (request,response) => {
    try {
      const url = new URL(request.url,'http://127.0.0.1');
      const path = resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
      if (!path.startsWith(root + sep) || !(await stat(path)).isFile()) throw new Error('Not found');
      const type = types[path.split('.').at(-1)] ?? 'application/octet-stream';
      response.writeHead(200, {'Content-Type': type, 'Cache-Control':'no-store'});
      createReadStream(path).pipe(response);
    } catch {
      response.writeHead(404).end('Not found.');
    }
  });
  await new Promise((accept,reject) => {
    server.once('error',reject);
    server.listen(port,'127.0.0.1',accept);
  });
  return {url:'http://127.0.0.1:' + server.address().port, close:() => server.close()};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const server = await serve(Number(process.argv[2] ?? 4173));
  console.log(server.url);
}
