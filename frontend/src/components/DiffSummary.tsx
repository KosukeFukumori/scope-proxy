import { useTranslation } from 'react-i18next'
import { Badge } from './ui'

interface ParsedDiff {
  added: string[]
  updated: string[]
  removed: string[]
  skipped_admin_conflict: string[]
}

/** Parses the `diff_summary` JSON string stored on a schema snapshot. Falls back to an
 * empty diff if the value cannot be parsed (e.g. legacy/unexpected data). */
function parseDiffSummary(raw: string): ParsedDiff {
  try {
    const parsed = JSON.parse(raw) as Partial<ParsedDiff>
    return {
      added: parsed.added ?? [],
      updated: parsed.updated ?? [],
      removed: parsed.removed ?? [],
      skipped_admin_conflict: parsed.skipped_admin_conflict ?? [],
    }
  } catch {
    return { added: [], updated: [], removed: [], skipped_admin_conflict: [] }
  }
}

function DiffCategory({
  label,
  tone,
  operationIds,
}: {
  label: string
  tone: 'success' | 'warning' | 'danger' | 'neutral'
  operationIds: string[]
}) {
  if (operationIds.length === 0) {
    return null
  }

  return (
    <details>
      <summary style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
        <Badge tone={tone}>
          {label} {operationIds.length}
        </Badge>
      </summary>
      <ul style={{ margin: '0.4rem 0 0', paddingLeft: '1.25rem' }}>
        {operationIds.map((operationId) => (
          <li key={operationId} className="mono" style={{ fontSize: '0.8rem' }}>
            {operationId}
          </li>
        ))}
      </ul>
    </details>
  )
}

/** Renders a `diff_summary` JSON string as count badges with expandable operationId lists,
 * instead of dumping the raw JSON. Shared between DashboardPage and SnapshotsPage. */
export function DiffSummary({ diffSummary }: { diffSummary: string }) {
  const { t } = useTranslation()
  const diff = parseDiffSummary(diffSummary)
  const hasChanges =
    diff.added.length > 0 || diff.updated.length > 0 || diff.removed.length > 0 || diff.skipped_admin_conflict.length > 0

  if (!hasChanges) {
    return <Badge tone="neutral">{t('diffSummary.noChanges')}</Badge>
  }

  return (
    <div className="stack" style={{ gap: '0.3rem' }}>
      <DiffCategory label={t('diffSummary.added')} tone="success" operationIds={diff.added} />
      <DiffCategory label={t('diffSummary.updated')} tone="warning" operationIds={diff.updated} />
      <DiffCategory label={t('diffSummary.removed')} tone="danger" operationIds={diff.removed} />
      <DiffCategory
        label={t('diffSummary.skippedAdminConflict')}
        tone="neutral"
        operationIds={diff.skipped_admin_conflict}
      />
    </div>
  )
}
