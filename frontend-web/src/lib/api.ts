const API_BASE = import.meta.env.VITE_API_BASE || 'https://crs.refineyourself.asia/api/v1'

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
    const fullUrl = `${API_BASE}${url}`.endsWith('/') ? `${API_BASE}${url}`.slice(0, -1) : `${API_BASE}${url}`

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

  // 使用相对路径时，直接返回相对路径
  // 因为 storage 也通过 vercel.json 代理了
  return s
}

export function shortenReason(text: string | null | undefined, fallback: string): string {
  const raw = String(text || '').trim()
  if (!raw) return fallback
  const cleaned = raw.replace(/推荐理由[:：]?/g, '').trim()
  const first = cleaned.split(/[。！？!?,，；;]/)[0].trim()
  const brief = first || cleaned
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief
}