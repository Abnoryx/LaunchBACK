'use client'
import { useCallback, useEffect, useState } from 'react'
import ShinyText from '@/components/ShinyText'
import GlareHover from '@/components/GlareHover'
type Shot = { id: string; ours: boolean; file: string; status: string; slots: string[]; notes: string; preview: boolean; world: string }
type Asset = { name: string; size: number }
const file = (p: string) => '/api/file?p=' + encodeURIComponent(p).replace(/%2F/g, '/')

export default function Home() {
  const [tab, setTab] = useState<'shots' | 'assets'>('shots'), [q, setQ] = useState(''), [shots, setShots] = useState<Shot[]>([]), [assets, setAssets] = useState<Asset[]>([])
  const [busy, setBusy] = useState(false), [msg, setMsg] = useState(''), [ask, setAsk] = useState<{ kind: 'template' | 'asset'; id: string } | null>(null), [edit, setEdit] = useState<Shot | null>(null), [notes, setNotes] = useState('')
  const load = useCallback(async () => {
    setBusy(true); const r = await fetch('/api/library'); setBusy(false)
    if (!r.ok) return setMsg('Could not load: ' + (await r.text()).slice(0, 160))
    const j = await r.json(); setShots(j.shots); setAssets(j.assets)
  }, [])
  useEffect(() => { load() }, [load])
  async function act(url: string, body: any, ok: string) {
    setBusy(true); const r = await fetch(url, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body) }); const j = await r.json().catch(() => ({}))
    setBusy(false); setAsk(null); setEdit(null)
    if (!r.ok) return setMsg('Failed: ' + (j.error || r.status))
    setMsg(ok + ' (commit ' + String(j.sha).slice(0, 7) + ')'); setTimeout(load, 1500)
  }
  const f = q.toLowerCase(), S = shots.filter(s => !f || (s.id + s.notes + s.slots.join(' ')).toLowerCase().includes(f)), A = assets.filter(a => !f || a.name.toLowerCase().includes(f))
  return <div className="wrap">
    <header>
      <h1><ShinyText text="LaunchBack Library" /></h1>
      <div className="tabs" role="tablist">
        <button role="tab" className={tab === 'shots' ? 'on' : ''} onClick={() => setTab('shots')}>Shots ({shots.length})</button>
        <button role="tab" className={tab === 'assets' ? 'on' : ''} onClick={() => setTab('assets')}>Assets ({assets.length})</button>
        <button className="btn" onClick={load} disabled={busy}>{busy ? '…' : 'Refresh'}</button>
      </div>
    </header>
    <input type="search" aria-label="Search" placeholder="Search…" value={q} onChange={e => setQ(e.target.value)} />
    {tab === 'shots' && <div className="grid">{S.map(s => <GlareHover key={s.id} width="100%" height="100%" borderRadius="14px" background="transparent" glareOpacity={0.18}>
      <div className="card">
        <div className="thumb">{s.preview
          ? <video src={file(`previews/${s.id}.mp4`)} poster={file(`previews/${s.id}.jpg`)} muted loop playsInline preload="none"
              onMouseEnter={e => e.currentTarget.play()} onMouseLeave={e => e.currentTarget.pause()} controls />
          : <div className="none">no preview yet</div>}</div>
        <div className="body">
          <span className="id">{s.id}</span>
          <div><span className={'tag' + (s.ours ? ' ours' : '')}>{s.ours ? 'ours' : 'bought'}</span> <span className="tag">{s.status}</span> {s.world && <span className="tag">{s.world}</span>}</div>
          <div className="note" title={s.notes}>{s.notes || 'no notes'}</div>
          <div className="row">
            <button className="btn" onClick={() => { setEdit(s); setNotes(s.notes) }}>Edit notes</button>
            {s.ours && <button className="btn bad" onClick={() => setAsk({ kind: 'template', id: s.id })}>Delete</button>}
          </div>
        </div>
      </div></GlareHover>)}</div>}
    {tab === 'assets' && <>
      <p><label className="btn pri" style={{ display: 'inline-block' }}>Upload files (max ~4 MB each)
        <input type="file" multiple hidden accept=".png,.jpg,.jpeg,.webp,.svg,.glb,.json" onChange={e => { const fd = new FormData(); Array.from(e.target.files || []).forEach(x => fd.append('file', x)); if (fd.has('file')) act('/api/upload', fd, 'Uploaded') }} /></label></p>
      <div className="assets">{A.map(a => <div className="asset" key={a.name}>
        <div className="pv">{/\.(png|jpg|jpeg|webp|svg)$/i.test(a.name) ? <img loading="lazy" alt={a.name} src={file('assets/' + a.name)} /> : <span className="mono">{a.name.split('.').pop()}</span>}</div>
        <span className="mono" style={{ wordBreak: 'break-all' }}>{a.name}</span><span className="note">{(a.size / 1024).toFixed(0)} KB</span>
        <button className="btn bad" onClick={() => setAsk({ kind: 'asset', id: a.name })}>Delete</button></div>)}</div></>}
    {ask && <div className="modal" role="dialog" aria-modal><div>
      <h2 style={{ marginTop: 0 }}>Delete {ask.kind} <code>{ask.id}</code>?</h2>
      <p className="note">{ask.kind === 'template' ? 'Removes its code, preview and catalog entry in one commit on main.' : 'Removes the file in one commit on main.'} You can undo it by reverting that commit on GitHub.</p>
      <div className="row"><button className="btn bad" onClick={() => act('/api/delete', ask, 'Deleted')} disabled={busy}>Yes, delete</button><button className="btn" onClick={() => setAsk(null)}>Cancel</button></div></div></div>}
    {edit && <div className="modal" role="dialog" aria-modal><div>
      <h2 style={{ marginTop: 0 }}>Notes for <code>{edit.id}</code></h2>
      <p className="note">/gen ranks shots against this text, so say what the shot looks like and when to use it.</p>
      <textarea rows={5} maxLength={600} value={notes} onChange={e => setNotes(e.target.value)} />
      <div className="row"><button className="btn pri" onClick={() => act('/api/notes', { id: edit.id, notes }, 'Notes saved')} disabled={busy}>Save</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></div></div></div>}
    {msg && <div className="toast" role="status" onClick={() => setMsg('')}>{msg}</div>}
  </div>
}
