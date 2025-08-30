export interface EmailProcessingRequest {
  text?: string
  file?: File
  metadata?: Record<string, any>
}

export interface EmailProcessingResponse {
  id: string
  label: 'PRODUCTIVE' | 'UNPRODUCTIVE'
  confidence: number
  reasoning?: string
  suggested: {
    subject?: string
    body: string
  }
  processed_at: string
}

export interface ClassificationResult {
  label: 'PRODUCTIVE' | 'UNPRODUCTIVE'
  confidence: number
  reasoning?: string
}

export interface SuggestedResponseResult {
  subject?: string
  body: string
  tone: 'professional' | 'friendly'
  language: string
}

export interface EmailMetadata {
  from?: string
  to?: string
  subject?: string
  received_at?: string
  attachments?: string[]
}

export interface ProcessingStats {
  total_processed: number
  productive_count: number
  unproductive_count: number
  average_confidence: number
  last_processed?: string
}

export interface ApiError {
  detail: string
  error_code?: string
  timestamp: string
}

export interface FileUploadState {
  file: File | null
  isUploading: boolean
  error?: string
}

export interface ProcessingState {
  isProcessing: boolean
  result?: EmailProcessingResponse
  error?: string
}

export interface FormData {
  text: string
  file: File | null
  metadata: EmailMetadata
}

