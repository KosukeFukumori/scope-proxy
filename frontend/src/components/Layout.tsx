import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { logout } from '../api/auth'

const NAV_ITEMS = [
  { to: '/', label: '接続先設定', end: true },
  { to: '/operations', label: 'オペレーション', end: false },
  { to: '/snapshots', label: '変更履歴', end: false },
  { to: '/tokens', label: 'トークン', end: false },
]

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? 'app-nav__link is-active' : 'app-nav__link'
}

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
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="app-brand">
          <span className="app-brand__mark">SP</span>
          scope-proxy
        </NavLink>
        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          className="btn btn--sm"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
        >
          ログアウト
        </button>
      </header>
      <main className="app-main">{children}</main>
    </div>
  )
}
