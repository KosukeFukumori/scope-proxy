/** Formats an ISO string into a human-readable date/time. Returns fallback when value is null. */
export function formatDateTime(value: string | null | undefined, fallback = '—', locale?: string): string {
  if (!value) {
    return fallback
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return fallback
  }
  return date.toLocaleString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Extracts a user-facing message from an API error. */
export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}
