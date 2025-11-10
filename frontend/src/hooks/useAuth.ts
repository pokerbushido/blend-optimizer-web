import { useAuthStore } from '@/store/auth.store'
import { UserRole } from '@/types/api'

/**
 * Hook for authentication utilities
 */
export function useAuth() {
  const { user, isAuthenticated, isLoading, error, login, logout, clearError } = useAuthStore()

  /**
   * Check if user has required role
   */
  const hasRole = (requiredRole: UserRole): boolean => {
    if (!user) return false

    // Admin has access to everything
    if (user.role === UserRole.ADMIN) return true

    // Operatore has access to Operatore and Visualizzatore
    if (user.role === UserRole.OPERATORE) {
      return requiredRole === UserRole.OPERATORE || requiredRole === UserRole.VISUALIZZATORE
    }

    // Visualizzatore only has access to Visualizzatore
    return user.role === requiredRole
  }

  /**
   * Check if user is admin
   */
  const isAdmin = (): boolean => {
    return user?.role === UserRole.ADMIN
  }

  /**
   * Check if user can edit (admin or operatore)
   */
  const canEdit = (): boolean => {
    return user?.role === UserRole.ADMIN || user?.role === UserRole.OPERATORE
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
    hasRole,
    isAdmin,
    canEdit,
  }
}
