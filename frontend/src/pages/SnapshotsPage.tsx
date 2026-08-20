import { useQuery } from '@tanstack/react-query'
import { listSchemaSnapshots } from '../api/operations'
import { Layout } from '../components/Layout'
import { EmptyState, Loading, PageHeader } from '../components/ui'
import { formatDateTime } from '../lib/format'

export function SnapshotsPage() {
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })
  const snapshots = snapshotsQuery.data ?? []

  return (
    <Layout>
      <PageHeader
        title="スキーマ変更履歴"
        description="OpenAPI スキーマを取得するたびに、内容のハッシュと差分を記録します。"
      />

      {snapshotsQuery.isLoading && <Loading />}

      {!snapshotsQuery.isLoading && snapshots.length === 0 && (
        <EmptyState
          title="まだ更新履歴がありません"
          description="接続先設定から「スキーマを今すぐ更新」を実行してください。"
        />
      )}

      {snapshots.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>取得日時</th>
                <th>spec_hash</th>
                <th>差分</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.map((snapshot) => (
                <tr key={snapshot.id}>
                  <td className="td--num">{formatDateTime(snapshot.fetched_at)}</td>
                  <td className="mono muted" title={snapshot.spec_hash}>
                    {snapshot.spec_hash.slice(0, 12)}
                  </td>
                  <td>
                    <pre style={{ whiteSpace: 'pre-wrap' }}>{snapshot.diff_summary}</pre>
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
