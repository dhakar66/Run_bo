export interface Account {
  id: string
  email: string | null
  display_name: string | null
  avatar_url: string | null
  is_active: boolean
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export async function getAccount(accessToken: string, signal: AbortSignal): Promise<Account> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    signal,
  })
  if (!response.ok) {
    const requestId = response.headers.get('X-Request-ID')
    const body: unknown = await response.json().catch(() => null)
    const detail = body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
      ? body.detail : 'We could not load your Run Tib account. Please try again.'
    throw new Error(`${detail} (HTTP ${response.status}${requestId ? `, request ${requestId}` : ''})`)
  }
  return response.json() as Promise<Account>
}
