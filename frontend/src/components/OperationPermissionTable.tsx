import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Operation } from '../types/api'
import { Badge, EmptyState, MethodBadge } from './ui'

const METHOD_FILTER_ALL = 'all'

const MODE_INDIVIDUAL = 'individual'
const MODE_BY_METHOD = 'byMethod'
type Mode = typeof MODE_INDIVIDUAL | typeof MODE_BY_METHOD

function groupKey(path: string): string {
  const segment = path.split('/').filter(Boolean)[0]
  return segment ? `/${segment}` : '/'
}

// Conventional REST ordering (GET first, DELETE last) instead of alphabetical.
const METHOD_ORDER = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

function sortMethods(methods: string[]): string[] {
  return [...methods].sort((a, b) => {
    const rankA = METHOD_ORDER.indexOf(a.toUpperCase())
    const rankB = METHOD_ORDER.indexOf(b.toUpperCase())
    if (rankA === -1 && rankB === -1) return a.localeCompare(b)
    if (rankA === -1) return 1
    if (rankB === -1) return -1
    return rankA - rankB
  })
}

/** Method-first view: pick a method tab, then bulk-select every operation under it. */
function OperationPermissionByMethod({
  operations,
  methods,
  activeMethod,
  onMethodChange,
  selectedIds,
  onToggle,
}: {
  operations: Operation[]
  methods: string[]
  activeMethod: string
  onMethodChange: (method: string) => void
  selectedIds: Set<string>
  onToggle: (operationId: string) => void
}) {
  const { t } = useTranslation()
  const methodOperations = operations
    .filter((op) => op.method === activeMethod)
    .sort((a, b) => a.path.localeCompare(b.path))
  const selectedCount = methodOperations.filter((op) => selectedIds.has(op.operation_id)).length
  const allSelected = selectedCount === methodOperations.length && methodOperations.length > 0

  function toggleAll(select: boolean) {
    for (const op of methodOperations) {
      if (selectedIds.has(op.operation_id) !== select) {
        onToggle(op.operation_id)
      }
    }
  }

  return (
    <div className="stack stack--tight">
      <div className="segmented">
        {methods.map((method) => (
          <button
            key={method}
            type="button"
            className={method === activeMethod ? 'segmented__item is-active' : 'segmented__item'}
            onClick={() => onMethodChange(method)}
          >
            {method}
          </button>
        ))}
      </div>

      {methodOperations.length === 0 ? (
        <EmptyState
          title={t('operationPermissionTable.searchEmpty.title')}
          description={t('operationPermissionTable.searchEmpty.description')}
        />
      ) : (
        <section className="permission-group">
          <div className="permission-group__head">
            <span className="permission-group__title">{activeMethod}</span>
            <span className="row" style={{ gap: '0.5rem' }}>
              <span className="muted" style={{ fontSize: '0.8rem' }}>
                {t('operationPermissionTable.selectedCount', { selected: selectedCount, total: methodOperations.length })}
              </span>
              <button type="button" className="btn btn--sm btn--ghost" onClick={() => toggleAll(!allSelected)}>
                {allSelected
                  ? t('operationPermissionTable.deselectAll')
                  : t('operationPermissionTable.selectAll')}
              </button>
            </span>
          </div>
          {methodOperations.map((op) => (
            <label
              key={op.operation_id}
              className={op.is_active ? 'permission-item' : 'permission-item is-inactive'}
            >
              <input
                type="checkbox"
                checked={selectedIds.has(op.operation_id)}
                onChange={() => onToggle(op.operation_id)}
              />
              <span className="permission-item__path">{op.path}</span>
              {!op.is_active && <Badge tone="danger">{t('operationPermissionTable.inactive')}</Badge>}
            </label>
          ))}
        </section>
      )}
    </div>
  )
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
  const [mode, setMode] = useState<Mode>(MODE_INDIVIDUAL)
  const [search, setSearch] = useState('')
  const [methodFilter, setMethodFilter] = useState(METHOD_FILTER_ALL)
  const [methodTab, setMethodTab] = useState<string | null>(null)
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

  const methods = sortMethods([...new Set(operations.map((op) => op.method))])
  const activeMethodTab = methodTab && methods.includes(methodTab) ? methodTab : methods[0]

  const normalizedSearch = search.trim().toLowerCase()
  const isFiltering = normalizedSearch !== '' || methodFilter !== METHOD_FILTER_ALL
  const filteredOperations = operations.filter((op) => {
    const matchesMethod = methodFilter === METHOD_FILTER_ALL || op.method === methodFilter
    const matchesSearch =
      normalizedSearch === '' ||
      op.path.toLowerCase().includes(normalizedSearch) ||
      (op.openapi_operation_id ?? '').toLowerCase().includes(normalizedSearch) ||
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
      <div className="segmented">
        <button
          type="button"
          className={mode === MODE_INDIVIDUAL ? 'segmented__item is-active' : 'segmented__item'}
          onClick={() => setMode(MODE_INDIVIDUAL)}
        >
          {t('operationPermissionTable.mode.individual')}
        </button>
        <button
          type="button"
          className={mode === MODE_BY_METHOD ? 'segmented__item is-active' : 'segmented__item'}
          onClick={() => setMode(MODE_BY_METHOD)}
        >
          {t('operationPermissionTable.mode.byMethod')}
        </button>
      </div>

      {mode === MODE_BY_METHOD && activeMethodTab && (
        <OperationPermissionByMethod
          operations={operations}
          methods={methods}
          activeMethod={activeMethodTab}
          onMethodChange={setMethodTab}
          selectedIds={selectedIds}
          onToggle={onToggle}
        />
      )}

      {mode === MODE_INDIVIDUAL && (
        <>
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
                    <span
                      className={isExpanded ? 'permission-group__chevron is-expanded' : 'permission-group__chevron'}
                    >
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
                    </label>
                  ))}
              </section>
            )
          })}
        </>
      )}
    </div>
  )
}
