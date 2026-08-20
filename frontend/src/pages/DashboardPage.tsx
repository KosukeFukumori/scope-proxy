import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getBackendConfig, refreshBackendConfig, upsertBackendConfig } from '../api/backendConfig'
import { listSchemaSnapshots } from '../api/operations'
import { Layout } from '../components/Layout'
import { EmptyState, ErrorAlert, Loading, PageHeader } from '../components/ui'
import { errorMessage, formatDateTime } from '../lib/format'
import type { BackendConfig } from '../types/api'

function ConfigForm({ config }: { config: BackendConfig | null }) {
  const queryClient = useQueryClient()
  const [endpointUrl, setEndpointUrl] = useState(config?.endpoint_url ?? '')
  const [openapiUrl, setOpenapiUrl] = useState(config?.openapi_url ?? '')

  const saveMutation = useMutation({
    mutationFn: () => upsertBackendConfig(endpointUrl, openapiUrl),
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
    <form className="card" onSubmit={handleSubmit}>
      <div className="card__body stack">
        <div className="field">
          <label className="field__label" htmlFor="endpoint-url">
            エンドポイントURL
          </label>
          <input
            id="endpoint-url"
            className="input"
            type="url"
            value={endpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            placeholder="https://api.example.com"
            required
          />
          <p className="field__hint">リクエストの転送先となるバックエンドのベースURL。</p>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="openapi-url">
            OpenAPI JSON URL
          </label>
          <input
            id="openapi-url"
            className="input"
            type="url"
            value={openapiUrl}
            onChange={(e) => setOpenapiUrl(e.target.value)}
            placeholder="https://api.example.com/openapi.json"
            required
          />
          <p className="field__hint">operationId 単位の権限管理に使用するスキーマの取得元。</p>
        </div>

        {saveMutation.isError && <ErrorAlert>{errorMessage(saveMutation.error, '保存に失敗しました')}</ErrorAlert>}
        {refreshMutation.isError && (
          <ErrorAlert>{errorMessage(refreshMutation.error, 'スキーマの更新に失敗しました')}</ErrorAlert>
        )}
        {refreshMutation.isSuccess && (
          <p className="muted" style={{ fontSize: '0.875rem' }}>
            差分: <code>{refreshMutation.data.diff_summary}</code>
          </p>
        )}
      </div>

      <div className="card__footer">
        <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? '保存中...' : '保存'}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending || !config}
        >
          {refreshMutation.isPending ? '更新中...' : 'スキーマを今すぐ更新'}
        </button>
        <span className="muted" style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>
          最終取得: {formatDateTime(config?.last_fetched_at, '未取得')}
        </span>
      </div>
    </form>
  )
}

export function DashboardPage() {
  const configQuery = useQuery({ queryKey: ['backendConfig'], queryFn: getBackendConfig, retry: false })
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })
  const recentSnapshots = snapshotsQuery.data?.slice(0, 5) ?? []

  return (
    <Layout>
      <PageHeader title="接続先設定" description="プロキシ先のバックエンドと OpenAPI スキーマの取得元を設定します。" />

      {configQuery.isLoading ? (
        <Loading />
      ) : (
        <ConfigForm key={configQuery.data?.id ?? 'new'} config={configQuery.data ?? null} />
      )}

      <section className="section">
        <div className="section__header">
          <h2>直近の変更履歴</h2>
          <Link to="/snapshots">すべて表示</Link>
        </div>

        {recentSnapshots.length === 0 ? (
          <EmptyState
            title="まだ更新履歴がありません"
            description="「スキーマを今すぐ更新」を実行すると履歴が記録されます。"
          />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>取得日時</th>
                  <th>差分</th>
                </tr>
              </thead>
              <tbody>
                {recentSnapshots.map((snapshot) => (
                  <tr key={snapshot.id}>
                    <td className="td--num">{formatDateTime(snapshot.fetched_at)}</td>
                    <td>
                      <code>{snapshot.diff_summary}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Layout>
  )
}
