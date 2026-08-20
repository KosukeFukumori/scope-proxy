import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBackendConfig, refreshBackendConfig, upsertBackendConfig } from '../api/backendConfig'
import { listSchemaSnapshots } from '../api/operations'
import { ApiError } from '../api/client'
import { Layout } from '../components/Layout'

export function DashboardPage() {
  const queryClient = useQueryClient()
  const configQuery = useQuery({ queryKey: ['backendConfig'], queryFn: getBackendConfig, retry: false })
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })

  const [endpointUrl, setEndpointUrl] = useState('')
  const [openapiUrl, setOpenapiUrl] = useState('')

  const config = configQuery.data
  const formEndpointUrl = endpointUrl || config?.endpoint_url || ''
  const formOpenapiUrl = openapiUrl || config?.openapi_url || ''

  const saveMutation = useMutation({
    mutationFn: () => upsertBackendConfig(formEndpointUrl, formOpenapiUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backendConfig'] })
    },
  })

  const refreshMutation = useMutation({
    mutationFn: refreshBackendConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backendConfig'] })
      queryClient.invalidateQueries({ queryKey: ['schemaSnapshots'] })
      queryClient.invalidateQueries({ queryKey: ['operations'] })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    saveMutation.mutate()
  }

  return (
    <Layout>
      <h1>接続先設定</h1>

      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          background: '#fff',
          padding: '1.5rem',
          borderRadius: '8px',
          maxWidth: '480px',
        }}
      >
        <label>
          エンドポイントURL
          <input
            type="url"
            value={formEndpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            placeholder="https://api.example.com"
            required
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </label>
        <label>
          OpenAPI JSON URL
          <input
            type="url"
            value={formOpenapiUrl}
            onChange={(e) => setOpenapiUrl(e.target.value)}
            placeholder="https://api.example.com/openapi.json"
            required
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </label>
        {saveMutation.isError && (
          <p style={{ color: '#dc2626', margin: 0 }}>
            {saveMutation.error instanceof ApiError ? saveMutation.error.message : '保存に失敗しました'}
          </p>
        )}
        <button type="submit" disabled={saveMutation.isPending} style={{ alignSelf: 'flex-start', padding: '0.5rem 1rem' }}>
          保存
        </button>
      </form>

      <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button onClick={() => refreshMutation.mutate()} disabled={refreshMutation.isPending || !config}>
          {refreshMutation.isPending ? '更新中...' : '今すぐ更新'}
        </button>
        {config?.last_fetched_at && (
          <span style={{ color: '#6b7280' }}>
            最終取得: {new Date(config.last_fetched_at).toLocaleString()}
          </span>
        )}
      </div>
      {refreshMutation.isError && (
        <p style={{ color: '#dc2626' }}>
          {refreshMutation.error instanceof ApiError ? refreshMutation.error.message : '更新に失敗しました'}
        </p>
      )}

      <h2 style={{ marginTop: '2rem' }}>直近の変更履歴</h2>
      {snapshotsQuery.data && snapshotsQuery.data.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>取得日時</th>
              <th>差分</th>
            </tr>
          </thead>
          <tbody>
            {snapshotsQuery.data.slice(0, 5).map((snapshot) => (
              <tr key={snapshot.id}>
                <td>{new Date(snapshot.fetched_at).toLocaleString()}</td>
                <td>
                  <code>{snapshot.diff_summary}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: '#6b7280' }}>まだ更新履歴がありません。</p>
      )}
    </Layout>
  )
}
