/**
 * Cliente API para comunicação com o backend FastAPI
 */

// URL da API - será configurada pela Vercel
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface EmailProcessingRequest {
  text?: string
  subject?: string
  metadata?: Record<string, any>
}

export interface EmailProcessingResponse {
  success: boolean
  email_id: string
  classification: {
    label: string
    confidence: number
    reasoning?: string
    model_used?: string
  }
  suggested_response: {
    subject: string
    body: string
    tone: string
    language: string
  }
  processing_time_ms: number
  metadata: {
    word_count: number
    language: string
    has_attachments: boolean
  }
  error?: string
}

export interface HealthCheckResponse {
  status: string
  timestamp: string
  service: string
}

export interface ProcessingStats {
  total_emails: number
  productive_count: number
  unproductive_count: number
  average_confidence: number
  average_processing_time_ms: number
  last_processed_at?: string
}

export interface SupportedLabelsResponse {
  labels: string[]
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.message || `HTTP error! status: ${response.status}`
        )
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  /**
   * Processa email em formato texto
   */
  async processEmailText(
    request: EmailProcessingRequest
  ): Promise<EmailProcessingResponse> {
    return this.request<EmailProcessingResponse>('/api/v1/process', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Processa arquivo de email
   */
  async processEmailFile(
    file: File,
    subject?: string
  ): Promise<EmailProcessingResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (subject) {
      formData.append('subject', subject)
    }

    const url = `${this.baseUrl}/api/v1/process/file`

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.message || `HTTP error! status: ${response.status}`
        )
      }

      return await response.json()
    } catch (error) {
      console.error('File upload failed:', error)
      throw error
    }
  }

  /**
   * Obtém estatísticas de processamento
   */
  async getProcessingStats(): Promise<ProcessingStats> {
    return this.request<ProcessingStats>('/api/v1/stats')
  }

  /**
   * Obtém labels suportados pelo classificador
   */
  async getSupportedLabels(): Promise<SupportedLabelsResponse> {
    return this.request<SupportedLabelsResponse>('/api/v1/labels')
  }

  /**
   * Verifica saúde da API
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health')
  }

  /**
   * Obtém status detalhado da aplicação
   */
  async getDetailedStatus(): Promise<any> {
    return this.request<any>('/status')
  }

  /**
   * Obtém métricas Prometheus
   */
  async getMetrics(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/metrics`)
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.status}`)
    }
    return await response.text()
  }
}

// Instância singleton do cliente API
export const apiClient = new ApiClient()

// Hook personalizado para usar o cliente API
export const useApi = () => {
  return {
    processEmailText: apiClient.processEmailText.bind(apiClient),
    processEmailFile: apiClient.processEmailFile.bind(apiClient),
    getProcessingStats: apiClient.getProcessingStats.bind(apiClient),
    getSupportedLabels: apiClient.getSupportedLabels.bind(apiClient),
    healthCheck: apiClient.healthCheck.bind(apiClient),
    getDetailedStatus: apiClient.getDetailedStatus.bind(apiClient),
    getMetrics: apiClient.getMetrics.bind(apiClient),
  }
}
