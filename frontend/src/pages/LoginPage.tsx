import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { errorMessage } from '../lib/format'
import { ErrorAlert } from '../components/ui'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['currentUser'], user)
      navigate('/', { replace: true })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    loginMutation.mutate()
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-card__head">
          <span className="app-brand__mark" style={{ width: '2.25rem', height: '2.25rem', fontSize: '0.9rem' }}>
            SP
          </span>
          <h1>scope-proxy</h1>
          <p className="page-header__description">管理画面にログイン</p>
        </div>

        <div className="stack">
          <div className="field">
            <label className="field__label" htmlFor="email">
              メールアドレス
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
              パスワード
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
            <ErrorAlert>{errorMessage(loginMutation.error, 'ログインに失敗しました')}</ErrorAlert>
          )}

          <button type="submit" className="btn btn--primary btn--block" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? 'ログイン中...' : 'ログイン'}
          </button>
        </div>
      </form>
    </div>
  )
}
