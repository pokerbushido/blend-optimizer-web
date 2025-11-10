import axios, { AxiosInstance, AxiosError } from 'axios'
import { API_BASE_URL, TOKEN_KEY, USER_KEY } from './constants'
import type { ApiError } from '@/types/api'
import { useAuthStore } from '@/store/auth.store'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add JWT token to headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and update auth state
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)

      // Update auth store to trigger React re-render without hard reload
      // This allows React Router to handle the redirect naturally
      useAuthStore.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        error: null,
      })
    }

    // Return formatted error
    let errorMessage: string

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail

      // Handle Pydantic validation errors (array of objects)
      if (Array.isArray(detail)) {
        errorMessage = detail
          .map((err: any) => {
            const field = err.loc ? err.loc.join('.') : 'field'
            return `${field}: ${err.msg || 'validation error'}`
          })
          .join('; ')
      } else if (typeof detail === 'string') {
        errorMessage = detail
      } else {
        // Fallback for other object types
        errorMessage = JSON.stringify(detail)
      }
    } else {
      errorMessage = error.message || 'An error occurred'
    }

    return Promise.reject(new Error(errorMessage))
  }
)

export default apiClient

// Helper function for handling API errors
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}
