import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Operation } from '../types/api'
import { Badge, EmptyState, MethodBadge } from './ui'

const METHOD_FILTER_ALL = 'all'

function groupKey(path: string): string {
  const segment = path.split('/').filter(Boolean)[0]
  return segment ? `/${segment}` : '/'
}

export function OperationPermissionTable({
  operations,
  selectedIds,
  onToggle,
}: {
  operations: Operation[]
  selectedIds: Set<string>
  onToggle: (operationId: string) => void
}) {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [methodFilter, setMethodFilter] = useState(METHOD_FILTER_ALL)
  // Groups collapsed manually by the user. Absent from this set means expanded.
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  if (operations.length === 0) {
    return (
      <EmptyState
        title={t('operationPermissionTable.empty.title')}
        description={t('operationPermissionTable.empty.description')}
      />
    )
  }

  const methods = [...new Set(operations.map((op) => op.method))].sort()

  const normalizedSearch = search.trim().toLowerCase()
  const isFiltering = normalizedSearch !== '' || methodFilter !== METHOD_FILTER_ALL
  const filteredOperations = operations.filter((op) => {
    const matchesMethod = methodFilter === METHOD_FILTER_ALL || op.method === methodFilter
    const matchesSearch =
      normalizedSearch === '' ||
      op.path.toLowerCase().includes(normalizedSearch) ||
      op.operation_id.toLowerCase().includes(normalizedSearch) ||
      (op.summary ?? '').toLowerCase().includes(normalizedSearch)
    return matchesMethod && matchesSearch
  })

  const groups = new Map<string, Operation[]>()
  for (const op of filteredOperations) {
    const key = groupKey(op.path)
    const list = groups.get(key) ?? []
    list.push(op)
    groups.set(key, list)
  }

  /** Selects/deselects all operations within a group. */
  function toggleGroup(ops: Operation[], select: boolean) {
    for (const op of ops) {
      if (selectedIds.has(op.operation_id) !== select) {
        onToggle(op.operation_id)
      }
    }
  }

  function toggleGroupCollapsed(group: string) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(group)) {
        next.delete(group)
      } else {
        next.add(group)
      }
      return next
    })
  }

  return (
    <div className="stack">
      <div className="row">
        <input
          type="text"
          className="input"
          style={{ maxWidth: '20rem' }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('operationPermissionTable.search.placeholder')}
        />
        <select
          className="input"
          style={{ width: 'auto' }}
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
        >
          <option value={METHOD_FILTER_ALL}>{t('operationPermissionTable.methodFilter.all')}</option>
          {methods.map((method) => (
            <option key={method} value={method}>
              {method}
            </option>
          ))}
        </select>
      </div>

      {filteredOperations.length === 0 && (
        <EmptyState
          title={t('operationPermissionTable.searchEmpty.title')}
          description={t('operationPermissionTable.searchEmpty.description')}
        />
      )}

      {[...groups.entries()].map(([group, ops]) => {
        const selectedCount = ops.filter((op) => selectedIds.has(op.operation_id)).length
        const allSelected = selectedCount === ops.length
        // While filtering, force matching groups open so results are visible immediately.
        const isExpanded = isFiltering || !collapsedGroups.has(group)

        return (
          <section key={group} className="permission-group">
            <div className="permission-group__head">
              <button
                type="button"
                className="permission-group__toggle"
                onClick={() => toggleGroupCollapsed(group)}
                aria-expanded={isExpanded}
                aria-label={
                  isExpanded
                    ? t('operationPermissionTable.collapseGroup')
                    : t('operationPermissionTable.expandGroup')
                }
              >
                <span className={isExpanded ? 'permission-group__chevron is-expanded' : 'permission-group__chevron'}>
                  {'▸'}
                </span>
                <span className="permission-group__title">{group}</span>
              </button>
              <span className="row" style={{ gap: '0.5rem' }}>
                <span className="muted" style={{ fontSize: '0.8rem' }}>
                  {t('operationPermissionTable.selectedCount', { selected: selectedCount, total: ops.length })}
                </span>
                <button
                  type="button"
                  className="btn btn--sm btn--ghost"
                  onClick={() => toggleGroup(ops, !allSelected)}
                >
                  {allSelected
                    ? t('operationPermissionTable.deselectAll')
                    : t('operationPermissionTable.selectAll')}
                </button>
              </span>
            </div>
            {isExpanded &&
              ops.map((op) => (
                <label
                  key={op.operation_id}
                  className={op.is_active ? 'permission-item' : 'permission-item is-inactive'}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(op.operation_id)}
                    onChange={() => onToggle(op.operation_id)}
                  />
                  <MethodBadge method={op.method} />
                  <span className="permission-item__path">{op.path}</span>
                  {!op.is_active && <Badge tone="danger">{t('operationPermissionTable.inactive')}</Badge>}
                  <span className="permission-item__id">{op.operation_id}</span>
                </label>
              ))}
          </section>
        )
      })}
    </div>
  )
}
