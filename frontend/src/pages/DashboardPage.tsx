import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getBackendConfig, refreshBackendConfig, upsertBackendConfig } from '../api/backendConfig'
import { listSchemaSnapshots } from '../api/operations'
import { getUsageSummary } from '../api/usage'
import { Layout } from '../components/Layout'
import { EmptyState, ErrorAlert, Loading, PageHeader } from '../components/ui'
import { errorMessage, formatDateTime } from '../lib/format'
import type { BackendConfig } from '../types/api'

const USAGE_SUMMARY_DAYS = 7

function UsageSummaryCard() {
  const { t } = useTranslation()
  const usageQuery = useQuery({
    queryKey: ['usageSummary', USAGE_SUMMARY_DAYS],
    queryFn: () => getUsageSummary(USAGE_SUMMARY_DAYS),
  })

  if (usageQuery.isLoading || !usageQuery.data) {
    return null
  }

  const summary = usageQuery.data

  return (
    <section className="section">
      <div className="section__header">
        <h2>{t('dashboard.usage.title', { days: summary.period_days })}</h2>
      </div>
      <div className="stat-row">
        <div className="card">
          <div className="card__body">
            <p className="muted" style={{ fontSize: '0.8rem' }}>
              {t('dashboard.usage.totalRequests')}
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 600 }}>{summary.total_requests}</p>
          </div>
        </div>
        <div className="card">
          <div className="card__body">
            <p className="muted" style={{ fontSize: '0.8rem' }}>
              {t('dashboard.usage.forwardedRequests')}
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 600 }}>{summary.forwarded_requests}</p>
          </div>
        </div>
        <div className="card">
          <div className="card__body">
            <p className="muted" style={{ fontSize: '0.8rem' }}>
              {t('dashboard.usage.deniedRequests')}
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 600 }}>{summary.denied_requests}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function ConfigForm({ config }: { config: BackendConfig | null }) {
  const { t, i18n } = useTranslation()
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
            {t('dashboard.form.endpointUrlLabel')}
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
          <p className="field__hint">{t('dashboard.form.endpointUrlHint')}</p>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="openapi-url">
            {t('dashboard.form.openapiUrlLabel')}
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
          <p className="field__hint">{t('dashboard.form.openapiUrlHint')}</p>
        </div>

        {saveMutation.isError && (
          <ErrorAlert>{errorMessage(saveMutation.error, t('dashboard.form.saveError'))}</ErrorAlert>
        )}
        {refreshMutation.isError && (
          <ErrorAlert>{errorMessage(refreshMutation.error, t('dashboard.form.refreshError'))}</ErrorAlert>
        )}
        {refreshMutation.isSuccess && (
          <p className="muted" style={{ fontSize: '0.875rem' }}>
            {t('dashboard.form.diffLabel')} <code>{refreshMutation.data.diff_summary}</code>
          </p>
        )}
      </div>

      <div className="card__footer">
        <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? t('dashboard.form.saving') : t('dashboard.form.save')}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending || !config}
        >
          {refreshMutation.isPending ? t('dashboard.form.refreshing') : t('dashboard.form.refreshNow')}
        </button>
        <span className="muted" style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>
          {t('dashboard.form.lastFetched')} {formatDateTime(config?.last_fetched_at, t('dashboard.form.notFetched'), i18n.resolvedLanguage)}
        </span>
      </div>
    </form>
  )
}

export function DashboardPage() {
  const { t, i18n } = useTranslation()
  const configQuery = useQuery({ queryKey: ['backendConfig'], queryFn: getBackendConfig, retry: false })
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })
  const recentSnapshots = snapshotsQuery.data?.slice(0, 5) ?? []

  return (
    <Layout>
      <PageHeader title={t('dashboard.title')} description={t('dashboard.description')} />

      {configQuery.isLoading ? (
        <Loading />
      ) : (
        <ConfigForm key={configQuery.data?.id ?? 'new'} config={configQuery.data ?? null} />
      )}

      <UsageSummaryCard />

      <section className="section">
        <div className="section__header">
          <h2>{t('dashboard.recentSnapshots')}</h2>
          <Link to="/snapshots">{t('dashboard.viewAll')}</Link>
        </div>

        {recentSnapshots.length === 0 ? (
          <EmptyState
            title={t('dashboard.emptySnapshots.title')}
            description={t('dashboard.emptySnapshots.description')}
          />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('dashboard.table.fetchedAt')}</th>
                  <th>{t('dashboard.table.diff')}</th>
                </tr>
              </thead>
              <tbody>
                {recentSnapshots.map((snapshot) => (
                  <tr key={snapshot.id}>
                    <td className="td--num">{formatDateTime(snapshot.fetched_at, undefined, i18n.resolvedLanguage)}</td>
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
