import { NextResponse } from 'next/server'
import { token } from '@/lib/auth'
export async function POST(req: Request) {
  const { password } = await req.json()
  if (!process.env.ADMIN_PASSWORD || password !== process.env.ADMIN_PASSWORD) return NextResponse.json({ error: 'wrong password' }, { status: 401 })
  const res = NextResponse.json({ ok: true })
  res.cookies.set('lb', await token(), { httpOnly: true, secure: req.headers.get('x-forwarded-proto') !== 'http' && !req.url.startsWith('http://localhost'), sameSite: 'strict', path: '/', maxAge: 60 * 60 * 24 * 30 })
  return res
}
