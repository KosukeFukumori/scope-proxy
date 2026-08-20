import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/_admin/',
  plugins: [react()],
  server: {
    proxy: {
      '/_admin/login': 'http://127.0.0.1:8000',
      '/_admin/logout': 'http://127.0.0.1:8000',
      '/_admin/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
