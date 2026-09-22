export type ChallengeStatus = 'draft' | 'published' | 'cancelled'

export interface Challenge {
  id: string
  name: string
  description: string | null
  starts_at: string
  ends_at: string
  status: ChallengeStatus
  created_at: string
  updated_at: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export async function getChallenges(signal?: AbortSignal): Promise<Challenge[]> {
  const response = await fetch(`${API_BASE_URL}/challenges`, { signal })

  if (!response.ok) {
    throw new Error(`The challenges request failed with status ${response.status}.`)
  }

  return response.json() as Promise<Challenge[]>
}
