import apiClient from '@/utils/api.client'
import type {
  BlendRequirements,
  OptimizationRequest,
  OptimizationResult,
} from '@/types/api'

/**
 * Create a new blend optimization request
 * Returns OptimizationResult with solutions directly (synchronous execution)
 */
export async function createOptimization(
  requirements: BlendRequirements
): Promise<OptimizationResult> {
  const response = await apiClient.post<OptimizationResult>('/api/optimize/blend', requirements)
  return response.data
}

/**
 * Get optimization request status
 */
export async function getOptimizationStatus(requestId: string): Promise<OptimizationRequest> {
  const response = await apiClient.get<OptimizationRequest>(`/api/optimize/${requestId}/status`)
  return response.data
}

/**
 * Get optimization results
 */
export async function getOptimizationResults(requestId: string): Promise<OptimizationResult> {
  const response = await apiClient.get<OptimizationResult>(`/api/optimize/${requestId}/results`)
  return response.data
}

/**
 * Download optimization results as Excel file
 */
export async function downloadOptimizationExcel(requestId: string): Promise<Blob> {
  const response = await apiClient.get(`/api/optimize/${requestId}/excel`, {
    responseType: 'blob',
  })
  return response.data
}

/**
 * Helper to trigger browser download of Excel file
 */
export function triggerExcelDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
