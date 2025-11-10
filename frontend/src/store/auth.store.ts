import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Token } from '@/types/api'
import * as authApi from '@/api/auth'
import { TOKEN_KEY, USER_KEY } from '@/utils/constants'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: localStorage.getItem(TOKEN_KEY),
      isAuthenticated: !!localStorage.getItem(TOKEN_KEY),
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const tokenData: Token = await authApi.login({ username, password })
          localStorage.setItem(TOKEN_KEY, tokenData.access_token)
          set({ token: tokenData.access_token })

          // Fetch user info after login
          await get().fetchCurrentUser()

          set({ isAuthenticated: true, isLoading: false })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed'
          set({ error: errorMessage, isLoading: false, isAuthenticated: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } finally {
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem(USER_KEY)
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null,
          })
        }
      },

      fetchCurrentUser: async () => {
        try {
          const user = await authApi.getCurrentUser()
          set({ user })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to fetch user'
          set({ error: errorMessage })
          throw error
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
