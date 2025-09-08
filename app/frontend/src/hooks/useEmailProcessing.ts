import { useState, useCallback } from 'react'
import {
  apiClient,
  EmailProcessingRequest,
  EmailProcessingResponse,
} from '../lib/api'

export interface ProcessingState {
  isLoading: boolean
  error: string | null
  result: EmailProcessingResponse | null
}

export interface UseEmailProcessingReturn extends ProcessingState {
  processEmailText: (request: EmailProcessingRequest) => Promise<void>
  processEmailFile: (file: File, subject?: string) => Promise<void>
  reset: () => void
  clearError: () => void
}

export const useEmailProcessing = (): UseEmailProcessingReturn => {
  const [state, setState] = useState<ProcessingState>({
    isLoading: false,
    error: null,
    result: null,
  })

  const processEmailText = useCallback(
    async (request: EmailProcessingRequest) => {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      try {
        const result = await apiClient.processEmailText(request)
        setState(prev => ({
          ...prev,
          isLoading: false,
          result,
          error: null,
        }))
      } catch (error) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Erro desconhecido',
        }))
      }
    },
    []
  )

  const processEmailFile = useCallback(async (file: File, subject?: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const result = await apiClient.processEmailFile(file, subject)
      setState(prev => ({
        ...prev,
        isLoading: false,
        result,
        error: null,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Erro desconhecido',
      }))
    }
  }, [])

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      error: null,
      result: null,
    })
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  return {
    ...state,
    processEmailText,
    processEmailFile,
    reset,
    clearError,
  }
}
