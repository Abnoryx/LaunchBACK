import { NextResponse } from 'next/server'
import { existsSync } from 'fs'
import path from 'path'
import { tree, text, CATALOG, LIB } from '@/lib/gh'
export const dynamic = 'force-dynamic'
export async function GET() {
  const [t, cat] = await Promise.all([tree(), text(CATALOG)]); const files = new Set(t.map(x => x.path)); const c = JSON.parse(cat)
  const shots = Object.entries<any>(c.templates).map(([id, e]) => {
    const ours = e.file?.startsWith('templates/') && files.has(`${LIB}/${e.file}`)
    return { id, ours, file: e.file, status: e.status, slots: e.slots || [], notes: e.gen?.use || e.use || e.source || '',
      preview: files.has(`${LIB}/previews/${id}.mp4`) || existsSync(path.join(process.cwd(), 'private', 'previews', `${id}.mp4`)), world: e.gen?.world || '' }
  })
  const assets = t.filter(x => x.path.startsWith(`${LIB}/assets/`) && x.type === 'blob').map(x => ({ name: x.path.slice(`${LIB}/assets/`.length), size: x.size || 0 }))
  return NextResponse.json({ shots, assets })
}
