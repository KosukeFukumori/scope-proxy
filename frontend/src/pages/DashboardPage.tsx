import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getBackendConfig, refreshBackendConfig, upsertBackendConfig } from '../api/backendConfig'
import { listSchemaSnapshots } from '../api/operations'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { DiffSummary } from '../components/DiffSummary'
import { Layout } from '../components/Layout'
import { EmptyState, ErrorAlert, Loading, PageHeader, SuccessAlert } from '../components/ui'
import { diffSummaryHasChanges } from '../lib/diffSummary'
import { errorMessage, formatDateTime } from '../lib/format'
import type { BackendConfig } from '../types/api'

/** Notice modal shown after a schema refresh detected changes. */
function SchemaChangeModal({ diffSummary, onClose }: { diffSummary: string; onClose: () => void }) {
  const { t } = useTranslation()

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="schema-change-modal-title">
      <div className="modal">
        <div className="stack stack--tight" style={{ overflowY: 'auto' }}>
          <h2 id="schema-change-modal-title">{t('dashboard.schemaChangeModal.title')}</h2>
          <p>{t('dashboard.schemaChangeModal.message')}</p>
          <DiffSummary diffSummary={diffSummary} />
        </div>
        <div className="modal__actions">
          <button type="button" className="btn btn--primary" onClick={onClose}>
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  )
}

function ConfigForm({ config }: { config: BackendConfig | null }) {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const [endpointUrl, setEndpointUrl] = useState(config?.endpoint_url ?? '')
  const [openapiUrl, setOpenapiUrl] = useState(config?.openapi_url ?? '')
  const [switchConfirmOpen, setSwitchConfirmOpen] = useState(false)
  const [schemaChangeDiff, setSchemaChangeDiff] = useState<string | null>(null)

  const refreshMutation = useMutation({
    mutationFn: refreshBackendConfig,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['backendConfig'] })
      queryClient.invalidateQueries({ queryKey: ['schemaSnapshots'] })
      queryClient.invalidateQueries({ queryKey: ['operations'] })
      if (diffSummaryHasChanges(data.diff_summary)) {
        setSchemaChangeDiff(data.diff_summary)
      }
    },
  })

  const saveMutation = useMutation({
    mutationFn: () => upsertBackendConfig(endpointUrl, openapiUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backendConfig'] })
      // Switching the backend resets operations and token permissions server-side.
      queryClient.invalidateQueries({ queryKey: ['operations'] })
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      // Fetch the new backend's schema right away so the proxy doesn't sit
      // without operations until someone presses "refresh" manually.
      refreshMutation.mutate()
    },
  })

  const urlChanged =
    config !== null && (endpointUrl !== config.endpoint_url || openapiUrl !== config.openapi_url)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (urlChanged) {
      // Warn before switching: this wipes operations and all token permissions.
      setSwitchConfirmOpen(true)
      return
    }
    saveMutation.mutate()
  }

  return (
    <>
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
        {saveMutation.isSuccess && <SuccessAlert>{t('dashboard.form.saveSuccess')}</SuccessAlert>}
        {refreshMutation.isError && (
          <ErrorAlert>{errorMessage(refreshMutation.error, t('dashboard.form.refreshError'))}</ErrorAlert>
        )}
        {refreshMutation.isSuccess && (
          <div className="muted" style={{ fontSize: '0.875rem' }}>
            <p style={{ margin: '0 0 0.3rem' }}>{t('dashboard.form.diffLabel')}</p>
            <DiffSummary diffSummary={refreshMutation.data.diff_summary} />
          </div>
        )}      </div>

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

    {switchConfirmOpen && (
      <ConfirmDialog
        title={t('dashboard.switchConfirm.title')}
        message={t('dashboard.switchConfirm.message')}
        confirmLabel={t('dashboard.switchConfirm.confirm')}
        onConfirm={() => {
          setSwitchConfirmOpen(false)
          saveMutation.mutate()
        }}
        onCancel={() => setSwitchConfirmOpen(false)}
      />
    )}

    {schemaChangeDiff !== null && (
      <SchemaChangeModal diffSummary={schemaChangeDiff} onClose={() => setSchemaChangeDiff(null)} />
    )}
    </>
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
                      <DiffSummary diffSummary={snapshot.diff_summary} />
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
