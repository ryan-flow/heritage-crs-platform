const API_BASE = 'https://heritage.refineyourself.asia/api/v1'

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

  const host = API_BASE.replace(/\/api\/v1\/?$/, '')

  // Absolute storage paths
  if (s.startsWith('/storage/') || s.startsWith('/static/')) return `${host}${s}`

  // /covers/ → /storage/covers/
  if (s.startsWith('/covers/')) return `${host}/storage${s}`

  // /discussion_covers/ → /storage/discussion_covers/
  if (s.startsWith('/discussion_covers/')) return `${host}/storage${s}`

  // /web_crawl/ → /storage/web_crawl/
  if (s.startsWith('/web_crawl/')) return `${host}/storage${s}`

  // /tts/ → /storage/tts/
  if (s.startsWith('/tts/')) return `${host}/storage${s}`

  // Search for storage/static path anywhere in string
  const storageIdx = s.indexOf('/storage/')
  if (storageIdx >= 0) return `${host}${s.slice(storageIdx)}`

  const staticIdx = s.indexOf('/static/')
  if (staticIdx >= 0) return `${host}${s.slice(staticIdx)}`

  // Filename-only fallback: guess storage path by pattern
  const filename = s.replace(/\\/g, '/').split('/').pop() || s
  if (/\.mp3$/i.test(filename)) return `${host}/storage/tts/${filename}`
  if (/^topic_|^discussion_/i.test(filename)) return `${host}/storage/discussion_covers/${filename}`
  if (/\.(png|jpg|jpeg|webp|gif|svg)$/i.test(filename)) return `${host}/storage/covers/${filename}`

  return `${host}/storage/${s.replace(/\\/g, '/')}`
}

export function shortenReason(text: string | null | undefined, fallback: string): string {
  const raw = String(text || '').trim()
  if (!raw) return fallback
  const cleaned = raw.replace(/推荐理由[:：]?/g, '').trim()
  const first = cleaned.split(/[。！？!?,，；;]/)[0].trim()
  const brief = first || cleaned
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief
}
