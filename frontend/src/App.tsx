import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { OperationsPage } from './pages/OperationsPage'
import { SnapshotsPage } from './pages/SnapshotsPage'
import { TokensPage } from './pages/TokensPage'
import { TokenEditPage } from './pages/TokenEditPage'
import { ProtectedRoute } from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/operations"
        element={
          <ProtectedRoute>
            <OperationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/snapshots"
        element={
          <ProtectedRoute>
            <SnapshotsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tokens"
        element={
          <ProtectedRoute>
            <TokensPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tokens/new"
        element={
          <ProtectedRoute>
            <TokenEditPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tokens/:id"
        element={
          <ProtectedRoute>
            <TokenEditPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
