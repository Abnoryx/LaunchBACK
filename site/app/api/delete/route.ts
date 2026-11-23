import { NextResponse } from 'next/server'
import { tree, text, commit, removeEntry, CATALOG, LIB } from '@/lib/gh'
export async function POST(req: Request) {
  const { kind, id } = await req.json()
  if (!/^[\w.\-\/ ]+$/.test(id) || id.includes('..')) return NextResponse.json({ error: 'bad id' }, { status: 400 })
  const files = new Set((await tree()).map(x => x.path))
  if (kind === 'asset') {
    const p = `${LIB}/assets/${id}`; if (!files.has(p)) return NextResponse.json({ error: 'no such asset' }, { status: 404 })
    return NextResponse.json({ sha: await commit([{ path: p, content: null }], `site: delete asset ${id}`) })
  }
  const py = `${LIB}/templates/${id}.py`; if (!files.has(py)) return NextResponse.json({ error: 'only our own templates can be deleted here' }, { status: 400 })
  const gone = [py, `${LIB}/previews/${id}.mp4`, `${LIB}/previews/${id}.jpg`].filter(p => files.has(p))
  const cat = removeEntry(await text(CATALOG), 'templates', id)
  const sha = await commit([...gone.map(p => ({ path: p, content: null })), { path: CATALOG, content: cat }], `site: delete template ${id}`)
  return NextResponse.json({ sha, removed: gone.length + 1 })
}
