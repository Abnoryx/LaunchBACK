import { NextRequest, NextResponse } from 'next/server'
import { ok } from '@/lib/auth'
export async function middleware(r: NextRequest) {
  const p = r.nextUrl.pathname
  if (p === '/login' || p === '/api/login') return NextResponse.next()
  if (await ok(r.cookies.get('lb')?.value)) return NextResponse.next()
  return p.startsWith('/api') ? NextResponse.json({ error: 'login' }, { status: 401 }) : NextResponse.redirect(new URL('/login', r.url))
}
export const config = { matcher: ['/((?!_next/|favicon).*)'] }
