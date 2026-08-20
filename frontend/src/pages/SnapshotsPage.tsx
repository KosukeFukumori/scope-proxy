import { useQuery } from '@tanstack/react-query'
import { listSchemaSnapshots } from '../api/operations'
import { Layout } from '../components/Layout'

export function SnapshotsPage() {
  const snapshotsQuery = useQuery({ queryKey: ['schemaSnapshots'], queryFn: listSchemaSnapshots })

  return (
    <Layout>
      <h1>スキーマ変更履歴</h1>

      {snapshotsQuery.isLoading && <p>読み込み中...</p>}

      {snapshotsQuery.data && snapshotsQuery.data.length === 0 && (
        <p style={{ color: '#6b7280' }}>まだ更新履歴がありません。</p>
      )}

      {snapshotsQuery.data && snapshotsQuery.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>取得日時</th>
              <th>spec_hash</th>
              <th>差分</th>
            </tr>
          </thead>
          <tbody>
            {snapshotsQuery.data.map((snapshot) => (
              <tr key={snapshot.id}>
                <td>{new Date(snapshot.fetched_at).toLocaleString()}</td>
                <td>
                  <code>{snapshot.spec_hash.slice(0, 12)}...</code>
                </td>
                <td>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{snapshot.diff_summary}</pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Layout>
  )
}
