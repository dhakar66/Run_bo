// Only diagnostic text is logged: never pass token objects, headers, or profiles.
export function safeErrorMessage(value: unknown): string {
  return String(value)
    .replace(/https?:\/\/[^\s]+/gi, '[URL]')
    .replace(/\bBearer\s+\S+/gi, 'Bearer [redacted]')
    .replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]*)?/g, '[token]')
    .replace(/\b(access_token|id_token|refresh_token|client_secret|password|code|state)\s*[:=]\s*[^\s,;&]+/gi, '$1=[redacted]')
    // Strip terminal escape/control characters to prevent forged log lines.
    // eslint-disable-next-line no-control-regex
    .replace(/[\u0000-\u001f\u007f-\u009f]/g, ' ')
    .slice(0, 600)
}

export function authErrorMessage(cause: unknown): string {
  return safeErrorMessage(cause instanceof Error ? cause.message : 'Authentication failed. Please try again.')
}
