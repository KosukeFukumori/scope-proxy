export interface ParsedDiff {
  added: string[]
  updated: string[]
  removed: string[]
  skipped_admin_conflict: string[]
}

/** Parses the `diff_summary` JSON string stored on a schema snapshot. Falls back to an
 * empty diff if the value cannot be parsed (e.g. legacy/unexpected data). */
export function parseDiffSummary(raw: string): ParsedDiff {
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

/** Returns true if the given `diff_summary` JSON string contains any change. */
export function diffSummaryHasChanges(raw: string): boolean {
  const diff = parseDiffSummary(raw)
  return (
    diff.added.length > 0 ||
    diff.updated.length > 0 ||
    diff.removed.length > 0 ||
    diff.skipped_admin_conflict.length > 0
  )
}
