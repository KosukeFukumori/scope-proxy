import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate } from 'react-router-dom'
import { getCurrentUser } from '../api/auth'
import { Loading } from './ui'

export function ProtectedRoute({ children }: { children: ReactNode }) {
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
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
