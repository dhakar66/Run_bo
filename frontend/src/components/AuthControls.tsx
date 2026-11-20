import { useAuth0 } from '@auth0/auth0-react'
import { useEffect, useRef, useState } from 'react'
import { reportAuthError } from '../auth/diagnostics'
import { authErrorMessage } from '../auth/errorMessage'
import { authConfigured } from '../auth/config'
import { getAccount, type Account } from '../services/auth'

export function AuthControls() {
  if (!authConfigured) {
    return <span className="auth-status">Sign-in coming soon</span>
  }
  return <ConnectedAuthControls />
}

function ConnectedAuthControls() {
  const { isLoading, isAuthenticated, user, error, loginWithRedirect, logout, getAccessTokenSilently } = useAuth0()
  const lastReportedError = useRef<Error | undefined>(undefined)
  useEffect(() => {
    if (error && lastReportedError.current !== error) {
      lastReportedError.current = error
      reportAuthError('callback', error)
    }
  }, [error])

  const [result, setResult] = useState<{ key: string; account?: Account; error?: string } | null>(null)
  const [actionError, setActionError] = useState('')
  const [retry, setRetry] = useState(0)
  const [busy, setBusy] = useState(false)
  const requestKey = `${user?.sub ?? ''}:${retry}`
  const account = result?.key === requestKey ? result.account : undefined
  const accountError = result?.key === requestKey ? result.error : undefined

  useEffect(() => {
    if (!isAuthenticated) return
    const controller = new AbortController()
    void (async () => {
      try {
        const token = await getAccessTokenSilently()
        if (controller.signal.aborted) return
        if (!token) throw new Error('Please sign out and sign in again to continue.')
        const profile = await getAccount(token, controller.signal)
        if (!controller.signal.aborted) setResult({ key: requestKey, account: profile })
      } catch (cause) {
        if (!controller.signal.aborted) {
          reportAuthError('account', cause)
          setResult({ key: requestKey, error: authErrorMessage(cause) })
        }
      }
    })()
    return () => controller.abort()
  }, [isAuthenticated, requestKey, getAccessTokenSilently])

  async function signIn() {
    setBusy(true)
    setActionError('')
    try {
      await loginWithRedirect({ authorizationParams: { connection: 'google-oauth2' } })
    } catch (cause) {
      reportAuthError('sign-in', cause)
      setActionError(authErrorMessage(cause))
      setBusy(false)
    }
  }

  async function signOut() {
    setBusy(true)
    setActionError('')
    try {
      await logout({ logoutParams: { returnTo: window.location.origin } })
    } catch (cause) {
      reportAuthError('sign-out', cause)
      setActionError(authErrorMessage(cause))
      setBusy(false)
    }
  }

  if (isLoading) return <span className="auth-status" role="status">Checking sign-in…</span>

  const message = actionError || accountError || (error ? authErrorMessage(error) : '')

  return (
    <div className="auth-controls">
      {isAuthenticated ? (
        <>
          <span className="auth-status" role="status">
            {account ? (account.display_name ?? account.email ?? 'Signed in') : accountError ? 'Account unavailable' : 'Loading account…'}
          </span>
          <button className="auth-button" disabled={busy} onClick={() => void signOut()}>Sign out</button>
        </>
      ) : (
        <button className="auth-button" disabled={busy} onClick={() => void signIn()}>
          {busy ? 'Redirecting…' : 'Continue with Google'}
        </button>
      )}
      {message && (
        <div className="auth-error" role="alert">
          <p>{message}</p>
          {accountError && <button onClick={() => setRetry(value => value + 1)}>Retry</button>}
        </div>
      )}
    </div>
  )
}
