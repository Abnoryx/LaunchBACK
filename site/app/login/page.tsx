'use client'
import { useState } from 'react'
import ShinyText from '@/components/ShinyText'
export default function Login() {
  const [pw, setPw] = useState(''), [err, setErr] = useState('')
  async function go(e: React.FormEvent) {
    e.preventDefault()
    const r = await fetch('/api/login', { method: 'POST', body: JSON.stringify({ password: pw }) })
    if (r.ok) location.href = '/'; else setErr('Wrong password')
  }
  return <form className="login" onSubmit={go}>
    <h1><ShinyText text="LaunchBack Library" /></h1>
    <label htmlFor="pw" className="note">Password</label>
    <input id="pw" type="password" autoFocus value={pw} onChange={e => setPw(e.target.value)} />
    <button className="btn pri" type="submit">Enter</button>
    {err && <div role="alert" style={{ color: '#fca5a5' }}>{err}</div>}
  </form>
}
