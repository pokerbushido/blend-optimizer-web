import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as optimizeApi from '@/api/optimize'
import type { BlendRequirements } from '@/types/api'
import { useToast } from './useToast'

/**
 * Hook for optimization operations with React Query
 */
export function useOptimization(requestId?: string) {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  // Create optimization mutation
  const createMutation = useMutation({
    mutationFn: (requirements: BlendRequirements) =>
      optimizeApi.createOptimization(requirements),
    onSuccess: () => {
      showSuccess('Ottimizzazione avviata con successo')
      queryClient.invalidateQueries({ queryKey: ['optimization'] })
    },
    onError: (error: Error) => {
      showError(`Errore ottimizzazione: ${error.message}`)
    },
  })

  // Fetch optimization status
  const {
    data: status,
    isLoading: isLoadingStatus,
    error: statusError,
  } = useQuery({
    queryKey: ['optimization', 'status', requestId],
    queryFn: () => optimizeApi.getOptimizationStatus(requestId!),
    enabled: !!requestId,
    refetchInterval: (query) => {
      // Keep polling if status is pending or processing
      const data = query.state.data
      return data && (data.status === 'pending' || data.status === 'processing') ? 2000 : false
    },
  })

  // Fetch optimization results
  const {
    data: results,
    isLoading: isLoadingResults,
    error: resultsError,
  } = useQuery({
    queryKey: ['optimization', 'results', requestId],
    queryFn: () => optimizeApi.getOptimizationResults(requestId!),
    enabled: !!requestId && !!status && status.status === 'completed',
  })

  // Download Excel mutation
  const downloadMutation = useMutation({
    mutationFn: (requestId: string) => optimizeApi.downloadOptimizationExcel(requestId),
    onSuccess: (blob, requestId) => {
      const filename = `blend_optimization_${requestId}_${new Date().toISOString().split('T')[0]}.xlsx`
      optimizeApi.triggerExcelDownload(blob, filename)
      showSuccess('Download Excel completato')
    },
    onError: (error: Error) => {
      showError(`Errore download: ${error.message}`)
    },
  })

  return {
    status,
    results,
    isLoadingStatus,
    isLoadingResults,
    statusError,
    resultsError,
    createOptimization: createMutation.mutate,
    isCreating: createMutation.isPending,
    downloadExcel: downloadMutation.mutate,
    isDownloading: downloadMutation.isPending,
  }
}
