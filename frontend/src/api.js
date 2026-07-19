export const SESSION_KEY = 'bijiang_visitor_session_id'

const API_ROOT = '/api/v1'

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options = {}, includeSession = false) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) }
  if (options.body) headers['Content-Type'] = 'application/json'
  if (includeSession) {
    const sessionId = localStorage.getItem(SESSION_KEY)
    if (sessionId) headers['X-Visitor-Session-ID'] = sessionId
  }
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = payload.detail || Object.values(payload).flat().join('、') || '请求失败'
    throw new ApiError(detail, response.status)
  }
  return payload
}

export async function ensureVisitorSession() {
  const current = localStorage.getItem(SESSION_KEY)
  if (current) return current
  const session = await request('/sessions/', { method: 'POST', body: '{}' })
  localStorage.setItem(SESSION_KEY, session.id)
  return session.id
}

export function getBootstrap() {
  return request('/bootstrap/')
}

export function generateItinerary(values) {
  return request(
    '/itineraries/generate/',
    { method: 'POST', body: JSON.stringify(values) },
    true,
  )
}

export function getAttraction(slug) {
  return request(`/attractions/${encodeURIComponent(slug)}/`)
}
