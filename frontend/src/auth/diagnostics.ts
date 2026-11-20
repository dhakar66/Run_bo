import { authErrorMessage } from './errorMessage'

type AuthStage = 'callback' | 'account' | 'sign-in' | 'sign-out'

export function reportAuthError(stage: AuthStage, cause: unknown) {
  const message = authErrorMessage(cause)
  console.error(`[Run Tib auth:${stage}] ${message}`)
  // The existing Vite development websocket forwards browser errors to npm run dev.
  if (import.meta.hot) {
    import.meta.hot.send('run-tib:auth-error', { stage, message })
  }
}
