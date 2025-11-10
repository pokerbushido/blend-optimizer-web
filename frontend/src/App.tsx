import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth.store'
import { UserRole } from './types/api'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/layout/ProtectedRoute'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Optimize from './pages/Optimize'
import Results from './pages/Results'
import UploadCSV from './pages/UploadCSV'
import Users from './pages/Users'
import History from './pages/History'
import Stats from './pages/Stats'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      {/* Public route */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
      />

      {/* Protected routes */}
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/optimize" element={<Optimize />} />
        <Route path="/results/:requestId" element={<Results />} />
        <Route path="/history" element={<History />} />
        <Route path="/stats" element={<Stats />} />

        {/* Admin only routes */}
        <Route
          path="/upload"
          element={<ProtectedRoute requiredRole={UserRole.ADMIN}><UploadCSV /></ProtectedRoute>}
        />
        <Route
          path="/users"
          element={<ProtectedRoute requiredRole={UserRole.ADMIN}><Users /></ProtectedRoute>}
        />
      </Route>

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
