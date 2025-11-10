import apiClient from '@/utils/api.client'
import type { LoginRequest, Token, User, PasswordChange } from '@/types/api'

/**
 * Login with username and password
 */
export async function login(credentials: LoginRequest): Promise<Token> {
  const formData = new FormData()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  const response = await apiClient.post<Token>('/api/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return response.data
}

/**
 * Get current authenticated user
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/api/auth/me')
  return response.data
}

/**
 * Logout (client-side only - clear token)
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/api/auth/logout')
  } catch (error) {
    // Ignore errors on logout
  }
}

/**
 * Change current user password
 */
export async function changePassword(data: PasswordChange): Promise<void> {
  await apiClient.post('/api/users/me/password', data)
}
