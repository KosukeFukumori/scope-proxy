import type { Operation } from '../types/api'

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
  const groups = new Map<string, Operation[]>()
  for (const op of operations) {
    const key = groupKey(op.path)
    const list = groups.get(key) ?? []
    list.push(op)
    groups.set(key, list)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {[...groups.entries()].map(([group, ops]) => (
        <fieldset key={group} style={{ border: '1px solid #e5e7eb', borderRadius: '6px' }}>
          <legend style={{ padding: '0 0.5rem' }}>
            <code>{group}</code>
          </legend>
          {ops.map((op) => (
            <label
              key={op.operation_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.25rem 0',
                opacity: op.is_active ? 1 : 0.5,
              }}
            >
              <input
                type="checkbox"
                checked={selectedIds.has(op.operation_id)}
                onChange={() => onToggle(op.operation_id)}
              />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.85rem' }}>
                {op.method} {op.path}
              </span>
              <span style={{ color: '#6b7280' }}>{op.operation_id}</span>
              {!op.is_active && <span style={{ color: '#dc2626' }}>(無効)</span>}
            </label>
          ))}
        </fieldset>
      ))}
      {operations.length === 0 && <p style={{ color: '#6b7280' }}>オペレーションがありません。</p>}
    </div>
  )
}
