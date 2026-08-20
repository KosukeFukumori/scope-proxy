import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

/** HTTPメソッドを色分けして表示する。 */
export function MethodBadge({ method }: { method: string }) {
  const key = method.toLowerCase()
  const known = ['get', 'post', 'put', 'patch', 'delete']
  const variant = known.includes(key) ? key : 'other'
  return <span className={`method method--${variant}`}>{method.toUpperCase()}</span>
}

type BadgeTone = 'neutral' | 'success' | 'danger' | 'warning'

export function Badge({ tone = 'neutral', children }: { tone?: BadgeTone; children: ReactNode }) {
  const className = tone === 'neutral' ? 'badge' : `badge badge--${tone}`
  return <span className={className}>{children}</span>
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

export function Loading({ label }: { label?: string }) {
  const { t } = useTranslation()
  return (
    <div className="loading" role="status">
      <Spinner />
      {label ?? t('ui.loading')}
    </div>
  )
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <p style={{ fontWeight: 600 }}>{title}</p>
      {description && <p>{description}</p>}
      {action}
    </div>
  )
}

export function ErrorAlert({ children }: { children: ReactNode }) {
  return (
    <p className="alert alert--error" role="alert">
      {children}
    </p>
  )
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="page-header">
      <div className="page-header__title">
        <h1>{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions}
    </header>
  )
}
