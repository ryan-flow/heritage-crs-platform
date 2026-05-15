const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

interface RequestOptions {
  method?: string
  data?: Record<string, unknown>
  timeout?: number
  headers?: Record<string, string>
}

function getSession() {
  try {
    const raw = localStorage.getItem('session')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export async function apiRequest<T = unknown>(
  url: string,
  options: RequestOptions = {}
): Promise<T> {
  const session = getSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (session?.userId) headers['X-User-Id'] = String(session.userId)
  if (session?.token) headers['X-Admin-Token'] = session.token

  const controller = new AbortController()
  const timeout = options.timeout || 30000
  const timer = setTimeout(() => controller.abort(), timeout)

  try {
    const method = (options.method || 'GET').toUpperCase()
    const fullUrl = `${API_BASE}${url}`

    const res = await fetch(fullUrl, {
      method,
      headers,
      body: options.data ? JSON.stringify(options.data) : undefined,
      signal: controller.signal,
    })

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
    }

    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

export function buildImageUrl(raw: string | null | undefined): string {
  if (!raw) return ''
  const s = String(raw).trim()
  if (!s) return ''
  if (s.startsWith('http://') || s.startsWith('https://')) return s
  if (s.startsWith('/storage/') || s.startsWith('/static/')) {
    return `${API_BASE.replace('/api/v1', '')}${s}`
  }
  const idx = s.indexOf('/storage/')
  if (idx >= 0) return `${API_BASE.replace('/api/v1', '')}${s.slice(idx)}`
  const idx2 = s.indexOf('/static/')
  if (idx2 >= 0) return `${API_BASE.replace('/api/v1', '')}${s.slice(idx2)}`
  return `${API_BASE.replace('/api/v1', '')}/storage/${s.replace(/\\/g, '/')}`
}

export function shortenReason(text: string | null | undefined, fallback: string): string {
  const raw = String(text || '').trim()
  if (!raw) return fallback
  const cleaned = raw.replace(/推荐理由[:：]?/g, '').trim()
  const first = cleaned.split(/[。！？!?,，；;]/)[0].trim()
  const brief = first || cleaned
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief
}
