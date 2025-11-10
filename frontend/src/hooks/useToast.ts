import { useUIStore } from '@/store/ui.store'

/**
 * Hook for displaying toast notifications
 */
export function useToast() {
  const { addToast, removeToast } = useUIStore()

  const showSuccess = (message: string, duration?: number) => {
    addToast({ type: 'success', message, duration })
  }

  const showError = (message: string, duration?: number) => {
    addToast({ type: 'error', message, duration })
  }

  const showWarning = (message: string, duration?: number) => {
    addToast({ type: 'warning', message, duration })
  }

  const showInfo = (message: string, duration?: number) => {
    addToast({ type: 'info', message, duration })
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeToast,
  }
}
