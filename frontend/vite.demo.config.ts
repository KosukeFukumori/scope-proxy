import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Config for the static GitHub Pages demo build (`npm run build:demo`).
// Unlike vite.config.ts, this serves from the repo name subpath and has no backend to proxy to
// — all API calls are mocked in-browser, see src/demo/mockApi.ts.
export default defineConfig({
  base: '/scope-proxy/',
  plugins: [react()],
  build: {
    outDir: 'dist-demo',
  },
})
