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
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const returnTo = sanitizeReturnTo(searchParams.get('returnTo'))

  const loginMutation = useMutation({
    mutationFn: () => login(username, password),
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
    <div className="login-page">
      <DemoBanner />
      <div className="login-screen">
        <form className="login-card" onSubmit={handleSubmit}>
          <div className="login-card__head">
            <img
              src={`${import.meta.env.BASE_URL}favicon.svg`}
              alt=""
              className="app-brand__mark"
              style={{ width: '2.25rem', height: '2.25rem' }}
            />
            <h1>{t('common.appName')}</h1>
            <p className="page-header__description">{t('login.subtitle')}</p>
            {IS_DEMO && (
              <p className="page-header__description">
                {t('demo.credentialsHint', {
                  username: DEMO_CREDENTIALS.username,
                  password: DEMO_CREDENTIALS.password,
                })}
              </p>
            )}
          </div>

          <div className="stack">
            <div className="field">
              <label className="field__label" htmlFor="username">
                {t('login.username')}
              </label>
              <input
                id="username"
                className="input"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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
    </div>
  )
}
