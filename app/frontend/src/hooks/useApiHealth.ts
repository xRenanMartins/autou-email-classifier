import { useState, useEffect, useCallback } from 'react'
import { apiClient, HealthCheckResponse, ProcessingStats } from '../lib/api'

export interface ApiHealthState {
  isHealthy: boolean
  isLoading: boolean
  error: string | null
  healthCheck: HealthCheckResponse | null
  stats: ProcessingStats | null
  lastChecked: Date | null
}

export interface UseApiHealthReturn extends ApiHealthState {
  checkHealth: () => Promise<void>
  getStats: () => Promise<void>
  refresh: () => Promise<void>
}

export const useApiHealth = (): UseApiHealthReturn => {
  const [state, setState] = useState<ApiHealthState>({
    isHealthy: false,
    isLoading: false,
    error: null,
    healthCheck: null,
    stats: null,
    lastChecked: null,
  })

  const checkHealth = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const healthCheck = await apiClient.healthCheck()
      setState(prev => ({
        ...prev,
        isLoading: false,
        isHealthy: healthCheck.status === 'healthy',
        healthCheck,
        lastChecked: new Date(),
        error: null,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        isHealthy: false,
        error:
          error instanceof Error
            ? error.message
            : 'Erro ao verificar saúde da API',
      }))
    }
  }, [])

  const getStats = useCallback(async () => {
    try {
      const stats = await apiClient.getProcessingStats()
      setState(prev => ({
        ...prev,
        stats,
        error: null,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error:
          error instanceof Error ? error.message : 'Erro ao obter estatísticas',
      }))
    }
  }, [])

  const refresh = useCallback(async () => {
    await Promise.all([checkHealth(), getStats()])
  }, [checkHealth, getStats])

  // Verifica saúde da API na montagem do componente
  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  // Atualiza estatísticas periodicamente
  useEffect(() => {
    const interval = setInterval(() => {
      if (state.isHealthy) {
        getStats()
      }
    }, 30000) // Atualiza a cada 30 segundos

    return () => clearInterval(interval)
  }, [state.isHealthy, getStats])

  return {
    ...state,
    checkHealth,
    getStats,
    refresh,
  }
}
