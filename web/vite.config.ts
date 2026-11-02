import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development /api/* is forwarded to the API (`make api`, port 8000; override with CLEARTAB_API).
declare const process: { env: Record<string, string | undefined> }

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': { target: process.env.CLEARTAB_API ?? 'http://localhost:8000', changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') } },
  },
})
