// One-password login: cookie = HMAC(password, 'launchback'), checked in middleware (Edge) and API routes.
export async function token(): Promise<string> {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(process.env.ADMIN_PASSWORD || ''), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const s = await crypto.subtle.sign('HMAC', k, new TextEncoder().encode('launchback'))
  return Array.from(new Uint8Array(s)).map(b => b.toString(16).padStart(2, '0')).join('')
}
export async function ok(cookie?: string) { return !!process.env.ADMIN_PASSWORD && !!cookie && cookie === await token() }
