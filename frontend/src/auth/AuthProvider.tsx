import { Auth0Provider } from '@auth0/auth0-react'
import type { PropsWithChildren } from 'react'

import { domain, clientId, audience, authConfigured } from './config'

export function AuthProvider({ children }: PropsWithChildren) {
  if (!authConfigured) return children

  return (
    <Auth0Provider
      domain={domain!}
      clientId={clientId!}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience,
        scope: 'openid profile email',
      }}
      cacheLocation="localstorage"
      useRefreshTokens
      useRefreshTokensFallback
      onRedirectCallback={() => {
        window.history.replaceState({}, document.title, window.location.pathname)
      }}
    >
      {children}
    </Auth0Provider>
  )
}
