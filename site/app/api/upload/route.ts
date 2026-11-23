import { NextResponse } from 'next/server'
import { commit, LIB } from '@/lib/gh'
export async function POST(req: Request) {   // multipart: one or more files -> library/assets/<name> (Vercel body limit ~4 MB)
  const f = await req.formData(); const changes = []
  for (const v of f.getAll('file')) {
    if (!(v instanceof File)) continue
    const name = v.name.replace(/[^\w.\-]/g, '_'); if (!/\.(png|jpg|jpeg|glb|webp|svg|json)$/i.test(name)) return NextResponse.json({ error: `${name}: type not allowed` }, { status: 400 })
    changes.push({ path: `${LIB}/assets/${name}`, content: Buffer.from(await v.arrayBuffer()).toString('base64'), base64: true })
  }
  if (!changes.length) return NextResponse.json({ error: 'no file' }, { status: 400 })
  return NextResponse.json({ sha: await commit(changes, `site: upload ${changes.length} asset(s)`), n: changes.length })
}
