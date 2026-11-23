// GitHub access for the library site: reads main live, writes one atomic commit per action (Git Data API).
const REPO = process.env.REPO || 'abnoryx/launchback', BRANCH = process.env.BRANCH || 'main'
export const LIB = 'workflows/video/library'
const API = `${process.env.GITHUB_API || 'https://api.github.com'}/repos/${REPO}`
const H = () => ({ Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' })

async function gh(path: string, init: RequestInit = {}) {
  const r = await fetch(API + path, { ...init, headers: { ...H(), ...(init.headers || {}) }, cache: 'no-store' })
  if (!r.ok) throw new Error(`GitHub ${r.status} ${path}: ${(await r.text()).slice(0, 200)}`)
  return r
}

export async function tree(): Promise<{ path: string; size?: number; type: string }[]> {
  const j = await (await gh(`/git/trees/${BRANCH}?recursive=1`)).json()
  return j.tree.filter((t: any) => t.path.startsWith(LIB + '/'))
}
export async function raw(path: string): Promise<Response> {
  return gh(`/contents/${path.split('/').map(encodeURIComponent).join('/')}?ref=${BRANCH}`, { headers: { Accept: 'application/vnd.github.raw+json' } })
}
export async function text(path: string) { return (await raw(path)).text() }

export type Change = { path: string; content: string | null; base64?: boolean }   // content null = delete
export async function commit(changes: Change[], message: string) {
  const ref = await (await gh(`/git/ref/heads/${BRANCH}`)).json(); const head = ref.object.sha
  const base = (await (await gh(`/git/commits/${head}`)).json()).tree.sha
  const entries = []
  for (const c of changes) {
    if (c.content === null) { entries.push({ path: c.path, mode: '100644', type: 'blob', sha: null }); continue }
    const b = await (await gh('/git/blobs', { method: 'POST', body: JSON.stringify({ content: c.content, encoding: c.base64 ? 'base64' : 'utf-8' }) })).json()
    entries.push({ path: c.path, mode: '100644', type: 'blob', sha: b.sha })
  }
  const t = await (await gh('/git/trees', { method: 'POST', body: JSON.stringify({ base_tree: base, tree: entries }) })).json()
  const c = await (await gh('/git/commits', { method: 'POST', body: JSON.stringify({ message, tree: t.sha, parents: [head] }) })).json()
  await gh(`/git/refs/heads/${BRANCH}`, { method: 'PATCH', body: JSON.stringify({ sha: c.sha }) })
  return c.sha as string
}

// catalog.json edits are done on the text so the rest of the file stays byte-identical (a JSON round trip rewrites floats).
export const CATALOG = `${LIB}/catalog.json`
function block(txt: string, section: string, id: string) {
  const s = txt.indexOf(`\n "${section}": {`); if (s < 0) return null
  const key = `\n  ${JSON.stringify(id)}: {`; const a = txt.indexOf(key, s); if (a < 0) return null
  const end = txt.indexOf('\n  }', a + key.length); if (end < 0) return null
  const after = txt[end + 4] === ',' ? 5 : 4
  return [a, end + after] as const
}
export function removeEntry(txt: string, section: string, id: string) {
  const b = block(txt, section, id); if (!b) return txt
  let out = txt.slice(0, b[0]) + txt.slice(b[1])
  out = out.replace(/,(\n \})/g, '$1')   // last entry removed -> drop the trailing comma
  JSON.parse(out); return out
}
export function setNotes(txt: string, id: string, notes: string) {
  const b = block(txt, 'templates', id); if (!b) throw new Error('not in catalog')
  const seg = txt.slice(b[0], b[1]), line = /("use": )"(?:[^"\\]|\\.)*"/
  let out: string
  if (line.test(seg)) out = txt.slice(0, b[0]) + seg.replace(line, (_m, k) => k + JSON.stringify(notes)) + txt.slice(b[1])
  else { const c = JSON.parse(txt); c.templates[id].gen = { ...(c.templates[id].gen || {}), use: notes }; out = JSON.stringify(c, null, 1) + '\n' }
  JSON.parse(out); return out
}
