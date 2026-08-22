import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { login } from '../api/auth'
import { errorMessage } from '../lib/format'
import { sanitizeReturnTo } from '../lib/returnTo'
import { ErrorAlert } from '../components/ui'
import { DemoBanner } from '../demo/DemoBanner'
import { DEMO_CREDENTIALS } from '../demo/mockApi'

const IS_DEMO = import.meta.env.MODE === 'demo'

export function LoginPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const returnTo = sanitizeReturnTo(searchParams.get('returnTo'))

  const loginMutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['currentUser'], user)
      navigate(returnTo, { replace: true })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    loginMutation.mutate()
  }

  return (
    <div className="login-screen">
      <DemoBanner />
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-card__head">
          <span className="app-brand__mark" style={{ width: '2.25rem', height: '2.25rem', fontSize: '0.9rem' }}>
            SP
          </span>
          <h1>{t('common.appName')}</h1>
          <p className="page-header__description">{t('login.subtitle')}</p>
          {IS_DEMO && (
            <p className="page-header__description">
              {t('demo.credentialsHint', {
                email: DEMO_CREDENTIALS.email,
                password: DEMO_CREDENTIALS.password,
              })}
            </p>
          )}
        </div>

        <div className="stack">
          <div className="field">
            <label className="field__label" htmlFor="email">
              {t('login.email')}
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="password">
              {t('login.password')}
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {loginMutation.isError && (
            <ErrorAlert>{errorMessage(loginMutation.error, t('login.error'))}</ErrorAlert>
          )}

          <button type="submit" className="btn btn--primary btn--block" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? t('login.submitting') : t('login.submit')}
          </button>
        </div>
      </form>
    </div>
  )
}
