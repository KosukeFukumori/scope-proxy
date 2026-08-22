import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { setup, getSetupStatus } from '../api/auth'
import { errorMessage } from '../lib/format'
import { ErrorAlert, Loading } from '../components/ui'

export function SetupPage() {
  const { t } = useTranslation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const setupStatusQuery = useQuery({
    queryKey: ['setupStatus'],
    queryFn: getSetupStatus,
  })

  const setupMutation = useMutation({
    mutationFn: () => setup(username, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['currentUser'], user)
      navigate('/', { replace: true })
    },
  })

  if (setupStatusQuery.isLoading) {
    return (
      <div className="app-main">
        <Loading />
      </div>
    )
  }

  // Setup was already completed (e.g. by another tab, or ADMIN_USERNAME/ADMIN_PASSWORD_HASH
  // at startup) — there's nothing left to set up here.
  if (setupStatusQuery.data && !setupStatusQuery.data.needs_setup) {
    return <Navigate to="/login" replace />
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setupMutation.mutate()
  }

  const passwordMismatch = confirmPassword.length > 0 && password !== confirmPassword

  return (
    <div className="login-page">
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
            <p className="page-header__description">{t('setup.subtitle')}</p>
          </div>

          <div className="stack">
            <div className="field">
              <label className="field__label" htmlFor="username">
                {t('setup.username')}
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
                {t('setup.password')}
              </label>
              <input
                id="password"
                className="input"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label className="field__label" htmlFor="confirm-password">
                {t('setup.confirmPassword')}
              </label>
              <input
                id="confirm-password"
                className="input"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            {passwordMismatch && <ErrorAlert>{t('setup.passwordMismatch')}</ErrorAlert>}

            {setupMutation.isError && (
              <ErrorAlert>{errorMessage(setupMutation.error, t('setup.error'))}</ErrorAlert>
            )}

            <button
              type="submit"
              className="btn btn--primary btn--block"
              disabled={setupMutation.isPending || passwordMismatch}
            >
              {setupMutation.isPending ? t('setup.submitting') : t('setup.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
