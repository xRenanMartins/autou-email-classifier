import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  EmailProcessingRequest, 
  EmailProcessingResponse, 
  ProcessingStats,
  ApiError 
} from '../types'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: `${baseURL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          const apiError: ApiError = {
            detail: error.response.data?.detail || 'Erro desconhecido',
            error_code: error.response.data?.error_code,
            timestamp: new Date().toISOString(),
          }
          return Promise.reject(apiError)
        } else if (error.request) {
          // Request made but no response received
          const apiError: ApiError = {
            detail: 'Servidor não respondeu. Verifique sua conexão.',
            error_code: 'NETWORK_ERROR',
            timestamp: new Date().toISOString(),
          }
          return Promise.reject(apiError)
        } else {
          // Something else happened
          const apiError: ApiError = {
            detail: 'Erro inesperado ocorreu',
            error_code: 'UNKNOWN_ERROR',
            timestamp: new Date().toISOString(),
          }
          return Promise.reject(apiError)
        }
      }
    )
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  async processEmail(request: EmailProcessingRequest): Promise<EmailProcessingResponse> {
    const formData = new FormData()
    
    if (request.text) {
      formData.append('text', request.text)
    }
    
    if (request.file) {
      formData.append('file', request.file)
    }
    
    if (request.metadata) {
      formData.append('metadata', JSON.stringify(request.metadata))
    }

    const response = await this.client.post<EmailProcessingResponse>('/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  }

  async getEmailClassification(emailId: string): Promise<EmailProcessingResponse> {
    const response = await this.client.get<EmailProcessingResponse>(`/emails/${emailId}`)
    return response.data
  }

  async getProcessingStats(): Promise<ProcessingStats> {
    const response = await this.client.get<ProcessingStats>('/stats')
    return response.data
  }

  async getSupportedLabels(): Promise<string[]> {
    const response = await this.client.get<string[]>('/labels')
    return response.data
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health')
    return response.data
  }
}

export const apiClient = new ApiClient()

