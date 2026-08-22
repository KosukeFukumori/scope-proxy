import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { changePassword } from '../api/auth'
import { Layout } from '../components/Layout'
import { ErrorAlert, PageHeader } from '../components/ui'
import { errorMessage } from '../lib/format'

export function AccountPage() {
  const { t } = useTranslation()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState(false)

  const changePasswordMutation = useMutation({
    mutationFn: () => changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setConfirmError(true)
      return
    }
    setConfirmError(false)
    changePasswordMutation.mutate()
  }

  return (
    <Layout>
      <PageHeader title={t('account.title')} description={t('account.description')} />

      <form className="stack" onSubmit={handleSubmit}>
        <div className="card">
          <div className="card__body stack">
            <div className="field">
              <label className="field__label" htmlFor="current-password">
                {t('account.form.currentPasswordLabel')}
              </label>
              <input
                id="current-password"
                className="input"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label className="field__label" htmlFor="new-password">
                {t('account.form.newPasswordLabel')}
              </label>
              <input
                id="new-password"
                className="input"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <p className="field__hint">{t('account.form.newPasswordHint')}</p>
            </div>

            <div className="field">
              <label className="field__label" htmlFor="confirm-password">
                {t('account.form.confirmPasswordLabel')}
              </label>
              <input
                id="confirm-password"
                className="input"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </div>
        </div>

        {confirmError && <ErrorAlert>{t('account.form.confirmMismatch')}</ErrorAlert>}
        {changePasswordMutation.isError && (
          <ErrorAlert>{errorMessage(changePasswordMutation.error, t('account.form.saveError'))}</ErrorAlert>
        )}
        {changePasswordMutation.isSuccess && <p className="alert alert--success">{t('account.form.saveSuccess')}</p>}

        <div className="row">
          <button type="submit" className="btn btn--primary" disabled={changePasswordMutation.isPending}>
            {t('account.form.save')}
          </button>
        </div>
      </form>
    </Layout>
  )
}
