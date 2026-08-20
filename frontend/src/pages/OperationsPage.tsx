import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listOperations } from '../api/operations'
import { Layout } from '../components/Layout'
import { Badge, EmptyState, Loading, MethodBadge, PageHeader } from '../components/ui'

type Filter = 'all' | 'active' | 'inactive'

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'すべて' },
  { value: 'active', label: '有効のみ' },
  { value: 'inactive', label: '無効のみ' },
]

export function OperationsPage() {
  const [filter, setFilter] = useState<Filter>('all')

  const operationsQuery = useQuery({
    queryKey: ['operations', filter],
    queryFn: () => listOperations(filter === 'all' ? undefined : filter === 'active'),
  })

  const operations = operationsQuery.data ?? []

  return (
    <Layout>
      <PageHeader
        title="オペレーション一覧"
        description="接続先 OpenAPI から取得した operationId の一覧です。無効なものは常に拒否されます。"
        actions={
          <div className="segmented">
            {FILTERS.map((item) => (
              <button
                key={item.value}
                type="button"
                className={filter === item.value ? 'segmented__item is-active' : 'segmented__item'}
                onClick={() => setFilter(item.value)}
              >
                {item.label}
              </button>
            ))}
          </div>
        }
      />

      {operationsQuery.isLoading && <Loading />}

      {!operationsQuery.isLoading && operations.length === 0 && (
        <EmptyState
          title="オペレーションがありません"
          description="接続先設定から OpenAPI スキーマを取得してください。"
        />
      )}

      {operations.length > 0 && (
        <div className="table-wrap">
          <table className="table">
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
              {operations.map((op) => (
                <tr key={op.operation_id}>
                  <td>
                    <MethodBadge method={op.method} />
                  </td>
                  <td className="mono">{op.path}</td>
                  <td>{op.operation_id}</td>
                  <td className="muted">{op.summary ?? '—'}</td>
                  <td>
                    {op.is_active ? <Badge tone="success">有効</Badge> : <Badge tone="danger">無効</Badge>}
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
