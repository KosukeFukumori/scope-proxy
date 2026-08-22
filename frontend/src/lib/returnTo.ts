/**
 * Validates that a `returnTo` value is a safe, same-app relative path.
 *
 * Only accepts paths starting with a single `/` (not `//` or `/\`, which
 * browsers can interpret as protocol-relative URLs pointing to another
 * host) so that it can never be used for an open redirect to an external
 * site. Returns `fallback` when the value is missing or unsafe.
 */
export function sanitizeReturnTo(value: string | null | undefined, fallback = '/'): string {
  if (!value) {
    return fallback
  }
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) {
    return fallback
  }
  return value
}
