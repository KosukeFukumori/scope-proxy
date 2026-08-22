import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { SetupPage } from './pages/SetupPage'
import { DashboardPage } from './pages/DashboardPage'
import { OperationsPage } from './pages/OperationsPage'
import { SnapshotsPage } from './pages/SnapshotsPage'
import { TokensPage } from './pages/TokensPage'
import { TokenEditPage } from './pages/TokenEditPage'
import { UsagePage } from './pages/UsagePage'
import { AccountPage } from './pages/AccountPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { RedirectIfAuthenticated } from './components/RedirectIfAuthenticated'

/** List of pages that require login. */
const PROTECTED_ROUTES: { path: string; element: ReactNode }[] = [
  { path: '/', element: <DashboardPage /> },
  { path: '/operations', element: <OperationsPage /> },
  { path: '/snapshots', element: <SnapshotsPage /> },
  { path: '/tokens', element: <TokensPage /> },
  { path: '/tokens/new', element: <TokenEditPage /> },
  { path: '/tokens/:id', element: <TokenEditPage /> },
  { path: '/usage', element: <UsagePage /> },
  { path: '/account', element: <AccountPage /> },
]

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthenticated>
            <LoginPage />
          </RedirectIfAuthenticated>
        }
      />
      <Route
        path="/setup"
        element={
          <RedirectIfAuthenticated>
            <SetupPage />
          </RedirectIfAuthenticated>
        }
      />
      {PROTECTED_ROUTES.map((route) => (
        <Route key={route.path} path={route.path} element={<ProtectedRoute>{route.element}</ProtectedRoute>} />
      ))}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
