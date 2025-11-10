import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as inventoryApi from '@/api/inventory'
import type { InventoryFilters } from '@/types/api'
import { useToast } from './useToast'

/**
 * Hook for inventory data fetching with React Query
 */
export function useInventory(filters?: InventoryFilters) {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  // Fetch inventory lots
  const {
    data: lotsData,
    isLoading: isLoadingLots,
    error: lotsError,
    refetch: refetchLots,
  } = useQuery({
    queryKey: ['inventory', 'lots', filters],
    queryFn: () => inventoryApi.getInventoryLots(filters),
  })

  // Fetch inventory stats
  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['inventory', 'stats'],
    queryFn: () => inventoryApi.getInventoryStats(),
  })

  // Upload CSV mutation
  const uploadMutation = useMutation({
    mutationFn: ({ file, notes }: { file: File; notes?: string }) =>
      inventoryApi.uploadInventoryCSV(file, notes),
    onSuccess: (data) => {
      showSuccess(`Upload completato: ${data.total_lots} lotti caricati`)
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
    },
    onError: (error: Error) => {
      showError(`Errore upload: ${error.message}`)
    },
  })

  // Fetch upload history
  const {
    data: uploadHistory,
    isLoading: isLoadingHistory,
    error: historyError,
  } = useQuery({
    queryKey: ['inventory', 'uploads'],
    queryFn: () => inventoryApi.getUploadHistory(),
  })

  return {
    lots: lotsData?.items || [],
    totalLots: lotsData?.total || 0,
    hasMore: lotsData?.has_more || false,
    stats,
    uploadHistory,
    isLoadingLots,
    isLoadingStats,
    isLoadingHistory,
    lotsError,
    statsError,
    historyError,
    refetchLots,
    refetchStats,
    uploadCSV: uploadMutation.mutate,
    isUploading: uploadMutation.isPending,
  }
}

/**
 * Hook for fetching a single inventory lot
 */
export function useInventoryLot(lotId: number) {
  return useQuery({
    queryKey: ['inventory', 'lot', lotId],
    queryFn: () => inventoryApi.getInventoryLot(lotId),
    enabled: !!lotId,
  })
}
