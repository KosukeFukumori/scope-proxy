import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate, useLocation } from 'react-router-dom'
import { getCurrentUser } from '../api/auth'
import { Loading } from './ui'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { data, isLoading, isError } = useQuery({
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

  if (isError || !data) {
    // Keep the current location so LoginPage can send the user back here after signing in.
    const returnTo = `${location.pathname}${location.search}`
    return <Navigate to={`/login?returnTo=${encodeURIComponent(returnTo)}`} replace />
  }

  return <>{children}</>
}
