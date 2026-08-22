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
  const [mismatch, setMismatch] = useState(false)

  const changePasswordMutation = useMutation({
    mutationFn: () => changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setMismatch(true)
      return
    }
    setMismatch(false)
    changePasswordMutation.mutate()
  }

  return (
    <Layout>
      <PageHeader title={t('account.title')} description={t('account.description')} />

      <form className="card" onSubmit={handleSubmit}>
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
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
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
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          {mismatch && <ErrorAlert>{t('account.form.mismatchError')}</ErrorAlert>}
          {changePasswordMutation.isError && (
            <ErrorAlert>{errorMessage(changePasswordMutation.error, t('account.form.saveError'))}</ErrorAlert>
          )}
          {changePasswordMutation.isSuccess && <p className="muted">{t('account.form.success')}</p>}
        </div>

        <div className="card__footer">
          <button type="submit" className="btn btn--primary" disabled={changePasswordMutation.isPending}>
            {changePasswordMutation.isPending ? t('account.form.saving') : t('account.form.save')}
          </button>
        </div>
      </form>
    </Layout>
  )
}
