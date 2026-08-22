import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { getCurrentUser } from '../api/auth'
import { createUser, deleteUser, listUsers } from '../api/users'
import { Layout } from '../components/Layout'
import { ErrorAlert, Loading, PageHeader } from '../components/ui'
import { errorMessage, formatDateTime } from '../lib/format'

function CreateUserForm() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const createMutation = useMutation({
    mutationFn: () => createUser({ email, password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setEmail('')
      setPassword('')
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    createMutation.mutate()
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="card__body stack">
        <h2>{t('users.form.title')}</h2>
        <div className="row">
          <div className="field" style={{ flex: 1 }}>
            <label className="field__label" htmlFor="new-user-email">
              {t('users.form.emailLabel')}
            </label>
            <input
              id="new-user-email"
              className="input"
              type="email"
              autoComplete="off"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label className="field__label" htmlFor="new-user-password">
              {t('users.form.passwordLabel')}
            </label>
            <input
              id="new-user-password"
              className="input"
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </div>

        {createMutation.isError && (
          <ErrorAlert>{errorMessage(createMutation.error, t('users.form.saveError'))}</ErrorAlert>
        )}

        <div className="row">
          <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>
            {t('users.form.create')}
          </button>
        </div>
      </div>
    </form>
  )
}

export function UsersPage() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const usersQuery = useQuery({ queryKey: ['users'], queryFn: listUsers })
  const currentUserQuery = useQuery({ queryKey: ['currentUser'], queryFn: getCurrentUser })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const users = usersQuery.data ?? []
  const currentUserId = currentUserQuery.data?.id

  return (
    <Layout>
      <PageHeader title={t('users.title')} description={t('users.description')} />

      <CreateUserForm />

      {usersQuery.isLoading && <Loading />}

      {deleteMutation.isError && (
        <ErrorAlert>{errorMessage(deleteMutation.error, t('users.deleteError'))}</ErrorAlert>
      )}

      {!usersQuery.isLoading && users.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t('users.table.email')}</th>
                <th>{t('users.table.createdAt')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.email}</td>
                  <td className="td--num">{formatDateTime(user.created_at, undefined, i18n.resolvedLanguage)}</td>
                  <td className="td--actions">
                    {user.id !== currentUserId && (
                      <button
                        type="button"
                        className="btn btn--sm btn--danger"
                        onClick={() => deleteMutation.mutate(user.id)}
                        disabled={deleteMutation.isPending}
                      >
                        {t('users.delete')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  )
}
