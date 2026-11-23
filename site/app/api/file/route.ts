import { raw, LIB } from '@/lib/gh'
export const dynamic = 'force-dynamic'
export async function GET(req: Request) {   // /api/file?p=previews/x.mp4  or  assets/x.png  (only inside the library folder)
  const p = new URL(req.url).searchParams.get('p') || ''
  if (!/^(previews|assets)\/[\w.\-\/ ]+$/.test(p) || p.includes('..')) return new Response('bad path', { status: 400 })
  const r = await raw(`${LIB}/${p}`)
  const type = p.endsWith('.mp4') ? 'video/mp4' : p.endsWith('.jpg') ? 'image/jpeg' : p.endsWith('.png') ? 'image/png' : 'application/octet-stream'
  return new Response(r.body, { headers: { 'content-type': type, 'cache-control': 'private, max-age=300' } })
}
