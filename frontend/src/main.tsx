import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './i18n'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

// The normal build is embedded in the backend under /_admin/. The demo build (see
// vite.demo.config.ts) has no backend and is served from the GitHub Pages repo subpath instead,
// so it routes from that path directly rather than nesting under /_admin/.
const basename = import.meta.env.MODE === 'demo' ? import.meta.env.BASE_URL.replace(/\/$/, '') : '/_admin'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={basename}>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
