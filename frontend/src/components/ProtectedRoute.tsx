import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate } from 'react-router-dom'
import { getCurrentUser } from '../api/auth'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['currentUser'],
    queryFn: getCurrentUser,
  })

  if (isLoading) {
    return <p style={{ padding: '2rem' }}>読み込み中...</p>
  }

  if (isError || !data) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
