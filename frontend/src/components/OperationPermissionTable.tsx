import { useTranslation } from 'react-i18next'
import type { Operation } from '../types/api'
import { Badge, EmptyState, MethodBadge } from './ui'

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

  if (operations.length === 0) {
    return (
      <EmptyState
        title={t('operationPermissionTable.empty.title')}
        description={t('operationPermissionTable.empty.description')}
      />
    )
  }

  const groups = new Map<string, Operation[]>()
  for (const op of operations) {
    const key = groupKey(op.path)
    const list = groups.get(key) ?? []
    list.push(op)
    groups.set(key, list)
  }

  /** グループ内をまとめて選択/解除する。 */
  function toggleGroup(ops: Operation[], select: boolean) {
    for (const op of ops) {
      if (selectedIds.has(op.operation_id) !== select) {
        onToggle(op.operation_id)
      }
    }
  }

  return (
    <div className="stack">
      {[...groups.entries()].map(([group, ops]) => {
        const selectedCount = ops.filter((op) => selectedIds.has(op.operation_id)).length
        const allSelected = selectedCount === ops.length

        return (
          <section key={group} className="permission-group">
            <div className="permission-group__head">
              <span className="permission-group__title">{group}</span>
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
            {ops.map((op) => (
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
