import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { logout } from '../api/auth'

const navLinkStyle = ({ isActive }: { isActive: boolean }) => ({
  padding: '0.5rem 0.75rem',
  borderRadius: '6px',
  textDecoration: 'none',
  color: isActive ? '#fff' : '#1a1a1a',
  background: isActive ? '#2563eb' : 'transparent',
})

export function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/login', { replace: true })
    },
  })

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1.5rem',
          background: '#fff',
          borderBottom: '1px solid #e5e7eb',
        }}
      >
        <strong>scope-proxy</strong>
        <nav style={{ display: 'flex', gap: '0.5rem' }}>
          <NavLink to="/" end style={navLinkStyle}>
            接続先設定
          </NavLink>
          <NavLink to="/operations" style={navLinkStyle}>
            オペレーション
          </NavLink>
          <NavLink to="/snapshots" style={navLinkStyle}>
            変更履歴
          </NavLink>
          <NavLink to="/tokens" style={navLinkStyle}>
            トークン
          </NavLink>
        </nav>
        <button onClick={() => logoutMutation.mutate()} disabled={logoutMutation.isPending}>
          ログアウト
        </button>
      </header>
      <main style={{ flex: 1, padding: '1.5rem', maxWidth: '960px', width: '100%', margin: '0 auto' }}>
        {children}
      </main>
    </div>
  )
}
