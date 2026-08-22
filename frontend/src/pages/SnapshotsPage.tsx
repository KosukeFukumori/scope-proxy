import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { listSchemaSnapshots } from '../api/operations'
import { DiffSummary } from '../components/DiffSummary'
import { Layout } from '../components/Layout'
import { EmptyState, Loading, PageHeader } from '../components/ui'
import { formatDateTime } from '../lib/format'

export function SnapshotsPage() {
  const { t, i18n } = useTranslation()
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })
  const snapshots = snapshotsQuery.data ?? []

  return (
    <Layout>
      <PageHeader title={t('snapshots.title')} description={t('snapshots.description')} />

      {snapshotsQuery.isLoading && <Loading />}

      {!snapshotsQuery.isLoading && snapshots.length === 0 && (
        <EmptyState title={t('snapshots.empty.title')} description={t('snapshots.empty.description')} />
      )}

      {snapshots.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t('snapshots.table.fetchedAt')}</th>
                <th>{t('snapshots.table.specHash')}</th>
                <th>{t('snapshots.table.diff')}</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.map((snapshot) => (
                <tr key={snapshot.id}>
                  <td className="td--num">{formatDateTime(snapshot.fetched_at, undefined, i18n.resolvedLanguage)}</td>
                  <td className="mono muted" title={snapshot.spec_hash}>
                    {snapshot.spec_hash.slice(0, 12)}
                  </td>
                  <td>
                    <DiffSummary diffSummary={snapshot.diff_summary} />
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
