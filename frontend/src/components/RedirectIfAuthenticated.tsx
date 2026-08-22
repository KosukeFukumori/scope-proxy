import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate, useSearchParams } from 'react-router-dom'
import { getCurrentUser } from '../api/auth'
import { sanitizeReturnTo } from '../lib/returnTo'
import { Loading } from './ui'

/** Redirects an already-authenticated user away from a guest-only page (e.g. /login). */
export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const [searchParams] = useSearchParams()
  const { data, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: getCurrentUser,
  })

  if (isLoading) {
    return (
      <div className="app-main">
        <Loading />
      </div>
    )
  }

  if (data) {
    const returnTo = sanitizeReturnTo(searchParams.get('returnTo'))
    return <Navigate to={returnTo} replace />
  }

  return <>{children}</>
}
