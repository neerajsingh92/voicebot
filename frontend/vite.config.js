import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiHost = env.VITE_API_HOST || 'http://localhost:8000'
  const port    = parseInt(env.VITE_PORT || '3000', 10)

  return {
    plugins: [react()],
    build: {
      outDir: '../backend/static',
      emptyOutDir: true,
    },
    server: {
      port,
      proxy: {
        '/api':    { target: apiHost, changeOrigin: true },
        '/health': { target: apiHost, changeOrigin: true },
      },
    },
  }
})
