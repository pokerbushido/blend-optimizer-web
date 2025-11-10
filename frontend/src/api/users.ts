import apiClient from '@/utils/api.client'
import type { User, UserCreate, UserUpdate } from '@/types/api'

/**
 * Get all users (admin only)
 */
export async function getUsers(): Promise<User[]> {
  const response = await apiClient.get<User[]>('/api/users/')
  return response.data
}

/**
 * Get a single user by ID (admin only)
 */
export async function getUser(userId: number): Promise<User> {
  const response = await apiClient.get<User>(`/api/users/${userId}`)
  return response.data
}

/**
 * Create a new user (admin only)
 */
export async function createUser(data: UserCreate): Promise<User> {
  const response = await apiClient.post<User>('/api/users/', data)
  return response.data
}

/**
 * Update an existing user (admin only)
 */
export async function updateUser(userId: number, data: UserUpdate): Promise<User> {
  const response = await apiClient.patch<User>(`/api/users/${userId}`, data)
  return response.data
}

/**
 * Delete a user (admin only)
 */
export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/api/users/${userId}`)
}
