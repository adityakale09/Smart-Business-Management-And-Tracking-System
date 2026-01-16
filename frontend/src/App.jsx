import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Sales from './pages/Sales'
import Inventory from './pages/Inventory'
import ReceiptsPage from './pages/ReceiptsPage'
import Employees from './pages/Employees'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import UserManagement from './pages/UserManagement'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
          <Route path="sales" element={<ErrorBoundary><Sales /></ErrorBoundary>} />
          <Route path="inventory" element={<ErrorBoundary><Inventory /></ErrorBoundary>} />
          <Route path="receipts" element={<ErrorBoundary><ReceiptsPage /></ErrorBoundary>} />
          <Route path="employees" element={<ErrorBoundary><Employees /></ErrorBoundary>} />
          <Route path="analytics" element={<ErrorBoundary><Analytics /></ErrorBoundary>} />
          <Route path="settings" element={<ErrorBoundary><Settings /></ErrorBoundary>} />
          <Route path="users" element={<ErrorBoundary><UserManagement /></ErrorBoundary>} />
        </Route>
      </Routes>
    </ErrorBoundary>
  )
}

export default App




