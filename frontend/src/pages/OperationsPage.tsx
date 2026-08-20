import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listOperations } from '../api/operations'
import { Layout } from '../components/Layout'

type Filter = 'all' | 'active' | 'inactive'

export function OperationsPage() {
  const [filter, setFilter] = useState<Filter>('all')

  const operationsQuery = useQuery({
    queryKey: ['operations', filter],
    queryFn: () => listOperations(filter === 'all' ? undefined : filter === 'active'),
  })

  return (
    <Layout>
      <h1>オペレーション一覧</h1>

      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
        {(['all', 'active', 'inactive'] as const).map((value) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            style={{
              padding: '0.4rem 0.8rem',
              background: filter === value ? '#2563eb' : '#fff',
              color: filter === value ? '#fff' : '#1a1a1a',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
            }}
          >
            {value === 'all' ? 'すべて' : value === 'active' ? '有効のみ' : '無効のみ'}
          </button>
        ))}
      </div>

      {operationsQuery.isLoading && <p>読み込み中...</p>}

      {operationsQuery.data && (
        <table>
          <thead>
            <tr>
              <th>Method</th>
              <th>Path</th>
              <th>operationId</th>
              <th>Summary</th>
              <th>状態</th>
            </tr>
          </thead>
          <tbody>
            {operationsQuery.data.map((op) => (
              <tr key={op.operation_id}>
                <td>{op.method}</td>
                <td>
                  <code>{op.path}</code>
                </td>
                <td>{op.operation_id}</td>
                <td>{op.summary ?? '-'}</td>
                <td>{op.is_active ? '有効' : '無効'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Layout>
  )
}
