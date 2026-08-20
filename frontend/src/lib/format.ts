/** ISO文字列を人間が読める日時表記へ。null の場合は fallback を返す。 */
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

/** API エラーからユーザー向けメッセージを取り出す。 */
export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}
