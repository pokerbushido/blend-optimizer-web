import apiClient from '@/utils/api.client'
import type {
  InventoryLot,
  InventoryUpload,
  InventoryStats,
  InventoryFilters,
  PaginatedResponse,
} from '@/types/api'

/**
 * Get list of inventory lots with optional filters
 */
export async function getInventoryLots(
  filters?: InventoryFilters
): Promise<PaginatedResponse<InventoryLot>> {
  const response = await apiClient.get<PaginatedResponse<InventoryLot>>('/api/inventory/lots', {
    params: filters,
  })
  return response.data
}

/**
 * Get a single inventory lot by ID
 */
export async function getInventoryLot(lotId: number): Promise<InventoryLot> {
  const response = await apiClient.get<InventoryLot>(`/api/inventory/lots/${lotId}`)
  return response.data
}

/**
 * Get inventory statistics
 */
export async function getInventoryStats(): Promise<InventoryStats> {
  const response = await apiClient.get<InventoryStats>('/api/inventory/stats')
  return response.data
}

/**
 * Upload CSV file with inventory data
 */
export async function uploadInventoryCSV(
  file: File,
  notes?: string
): Promise<InventoryUpload> {
  const formData = new FormData()
  formData.append('file', file)
  if (notes) {
    formData.append('notes', notes)
  }

  const response = await apiClient.post<InventoryUpload>('/api/inventory/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * Get upload history
 */
export async function getUploadHistory(): Promise<InventoryUpload[]> {
  const response = await apiClient.get<InventoryUpload[]>('/api/inventory/uploads')
  return response.data
}
