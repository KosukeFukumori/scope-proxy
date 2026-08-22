import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { listOperations } from '../api/operations'
import { Layout } from '../components/Layout'
import { Badge, EmptyState, Loading, MethodBadge, PageHeader } from '../components/ui'

type Filter = 'all' | 'active' | 'inactive'
const METHOD_FILTER_ALL = 'all'

export function OperationsPage() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [methodFilter, setMethodFilter] = useState(METHOD_FILTER_ALL)

  const FILTERS: { value: Filter; label: string }[] = [
    { value: 'all', label: t('operations.filters.all') },
    { value: 'active', label: t('operations.filters.active') },
    { value: 'inactive', label: t('operations.filters.inactive') },
  ]

  const operationsQuery = useQuery({
    queryKey: ['operations', filter],
    queryFn: () => listOperations(filter === 'all' ? undefined : filter === 'active'),
  })

  const allOperations = operationsQuery.data ?? []
  const methods = [...new Set(allOperations.map((op) => op.method))].sort()

  const normalizedSearch = search.trim().toLowerCase()
  const operations = allOperations.filter((op) => {
    const matchesMethod = methodFilter === METHOD_FILTER_ALL || op.method === methodFilter
    const matchesSearch =
      normalizedSearch === '' ||
      op.path.toLowerCase().includes(normalizedSearch) ||
      (op.openapi_operation_id ?? '').toLowerCase().includes(normalizedSearch) ||
      (op.summary ?? '').toLowerCase().includes(normalizedSearch)
    return matchesMethod && matchesSearch
  })

  return (
    <Layout>
      <PageHeader
        title={t('operations.title')}
        description={t('operations.description')}
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

      {!operationsQuery.isLoading && allOperations.length > 0 && (
        <div className="row" style={{ marginBottom: '0.75rem' }}>
          <input
            type="text"
            className="input"
            style={{ maxWidth: '20rem' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('operations.search.placeholder')}
          />
          <select
            className="input"
            style={{ width: 'auto' }}
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
          >
            <option value={METHOD_FILTER_ALL}>{t('operations.methodFilter.all')}</option>
            {methods.map((method) => (
              <option key={method} value={method}>
                {method}
              </option>
            ))}
          </select>
        </div>
      )}

      {operationsQuery.isLoading && <Loading />}

      {!operationsQuery.isLoading && allOperations.length === 0 && (
        <EmptyState title={t('operations.empty.title')} description={t('operations.empty.description')} />
      )}

      {!operationsQuery.isLoading && allOperations.length > 0 && operations.length === 0 && (
        <EmptyState
          title={t('operations.searchEmpty.title')}
          description={t('operations.searchEmpty.description')}
        />
      )}

      {operations.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t('operations.table.method')}</th>
                <th>{t('operations.table.path')}</th>
                <th>{t('operations.table.summary')}</th>
                <th>{t('operations.table.status')}</th>
              </tr>
            </thead>
            <tbody>
              {operations.map((op) => (
                <tr key={op.operation_id}>
                  <td>
                    <MethodBadge method={op.method} />
                  </td>
                  <td className="mono">{op.path}</td>
                  <td className="muted">{op.summary ?? '—'}</td>
                  <td>
                    {op.is_active ? (
                      <Badge tone="success">{t('operations.active')}</Badge>
                    ) : (
                      <Badge tone="danger">{t('operations.inactive')}</Badge>
                    )}
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
