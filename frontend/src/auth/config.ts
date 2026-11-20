export const domain = import.meta.env.VITE_AUTH0_DOMAIN?.trim()
export const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID?.trim()
export const audience = import.meta.env.VITE_AUTH0_AUDIENCE?.trim()

export const authConfigured = Boolean(domain && clientId && audience)

