import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import { safeErrorMessage } from './src/auth/errorMessage.ts'

function authDiagnostics(): Plugin {
  return {
    name: 'run-tib-auth-diagnostics',
    apply: 'serve',
    configureServer(server) {
      server.ws.on('run-tib:auth-error', (payload: unknown) => {
        if (!payload || typeof payload !== 'object') return
        const { stage, message } = payload as Record<string, unknown>
        if (typeof stage !== 'string' || !['callback', 'account', 'sign-in', 'sign-out'].includes(stage)) return
        if (typeof message !== 'string') return
        server.config.logger.error(`[Run Tib auth:${stage}] ${safeErrorMessage(message)}`, { timestamp: true })
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), authDiagnostics()],
  // Auth0 callback URLs include the port; fail clearly instead of switching ports.
  server: { port: 5173, strictPort: true },
})
