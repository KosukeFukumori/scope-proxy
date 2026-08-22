import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { logout } from '../api/auth'
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from '../i18n'
import { DemoBanner } from '../demo/DemoBanner'

const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  ja: '日本語',
  en: 'English',
  zh: '中文',
}

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? 'app-nav__link is-active' : 'app-nav__link'
}

export function Layout({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const NAV_ITEMS = [
    { to: '/', label: t('layout.nav.dashboard'), end: true },
    { to: '/operations', label: t('layout.nav.operations'), end: false },
    { to: '/snapshots', label: t('layout.nav.snapshots'), end: false },
    { to: '/tokens', label: t('layout.nav.tokens'), end: false },
    { to: '/usage', label: t('layout.nav.usage'), end: false },
    { to: '/account', label: t('layout.nav.account'), end: false },
  ]

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/login', { replace: true })
    },
  })

  return (
    <div className="app-shell">
      <DemoBanner />
      <header className="app-header">
        <NavLink to="/" className="app-brand">
          <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" className="app-brand__mark" />
          {t('common.appName')}
        </NavLink>
        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <select
          className="input"
          style={{ width: 'auto' }}
          aria-label={t('layout.language')}
          value={i18n.resolvedLanguage}
          onChange={(e) => i18n.changeLanguage(e.target.value)}
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option key={lang} value={lang}>
              {LANGUAGE_LABELS[lang]}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="btn btn--sm"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
        >
          {t('layout.logout')}
        </button>
      </header>
      <main className="app-main">{children}</main>
    </div>
  )
}
