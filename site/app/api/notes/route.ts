import { NextResponse } from 'next/server'
import { text, commit, setNotes, CATALOG } from '@/lib/gh'
export async function POST(req: Request) {
  const { id, notes } = await req.json()
  if (typeof notes !== 'string' || notes.length > 600) return NextResponse.json({ error: 'notes: text up to 600 characters' }, { status: 400 })
  const cat = setNotes(await text(CATALOG), id, notes.trim())
  return NextResponse.json({ sha: await commit([{ path: CATALOG, content: cat }], `site: edit notes of ${id}`) })
}
