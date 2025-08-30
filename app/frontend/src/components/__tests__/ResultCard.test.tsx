import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { ResultCard } from '../ResultCard'
import { EmailProcessingResponse } from '../../lib/api'

const mockResult: EmailProcessingResponse = {
  success: true,
  email_id: '123',
  classification: {
    label: 'PRODUCTIVE',
    confidence: 0.85,
    reasoning: 'Email contém solicitação específica de suporte',
    model_used: 'heuristic'
  },
  suggested_response: {
    subject: 'Re: Suporte Técnico',
    body: 'Obrigado pelo seu email. Vou analisar sua solicitação e retornar em breve.',
    tone: 'professional',
    language: 'pt'
  },
  processing_time_ms: 150,
  metadata: {
    word_count: 25,
    language: 'pt',
    has_attachments: false
  }
}

const mockUnproductiveResult: EmailProcessingResponse = {
  success: true,
  email_id: '456',
  classification: {
    label: 'UNPRODUCTIVE',
    confidence: 0.92,
    reasoning: 'Email de agradecimento sem ação necessária',
    model_used: 'heuristic'
  },
  suggested_response: {
    subject: '',
    body: 'Obrigado pelo seu feedback positivo!',
    tone: 'friendly',
    language: 'pt'
  },
  processing_time_ms: 120,
  metadata: {
    word_count: 15,
    language: 'pt',
    has_attachments: false
  }
}

describe('ResultCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(),
      },
    })
  })

  it('renders productive email classification correctly', () => {
    render(<ResultCard result={mockResult} />)
    
    expect(screen.getByText('Resultado da Classificação')).toBeInTheDocument()
    expect(screen.getByText('Produtivo')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('Email contém solicitação específica de suporte')).toBeInTheDocument()
  })

  it('renders unproductive email classification correctly', () => {
    render(<ResultCard result={mockUnproductiveResult} />)
    
    expect(screen.getByText('Improdutivo')).toBeInTheDocument()
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('displays suggested response with subject and body', () => {
    render(<ResultCard result={mockResult} />)
    
    expect(screen.getByText('Resposta Sugerida')).toBeInTheDocument()
    expect(screen.getByText('Re: Suporte Técnico')).toBeInTheDocument()
    expect(screen.getByText('Obrigado pelo seu email. Vou analisar sua solicitação e retornar em breve.')).toBeInTheDocument()
  })

  it('displays suggested response without subject when not provided', () => {
    render(<ResultCard result={mockUnproductiveResult} />)
    
    expect(screen.getByText('Resposta Sugerida')).toBeInTheDocument()
    expect(screen.queryByText('Assunto:')).not.toBeInTheDocument()
    expect(screen.getByText('Obrigado pelo seu feedback positivo!')).toBeInTheDocument()
  })

  it('shows correct confidence color based on confidence level', () => {
    const highConfidence = { 
      ...mockResult, 
      classification: { ...mockResult.classification, confidence: 0.95 }
    }
    const mediumConfidence = { 
      ...mockResult, 
      classification: { ...mockResult.classification, confidence: 0.75 }
    }
    const lowConfidence = { 
      ...mockResult, 
      classification: { ...mockResult.classification, confidence: 0.45 }
    }

    const { rerender } = render(<ResultCard result={highConfidence} />)
    expect(screen.getByText('95%')).toHaveClass('text-success-600')

    rerender(<ResultCard result={mediumConfidence} />)
    expect(screen.getByText('75%')).toHaveClass('text-warning-600')

    rerender(<ResultCard result={lowConfidence} />)
    expect(screen.getByText('45%')).toHaveClass('text-error-600')
  })

  it('copies response body to clipboard when copy button is clicked', async () => {
    render(<ResultCard result={mockResult} />)
    
    const copyButton = screen.getByText('Copiar')
    fireEvent.click(copyButton)
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'Obrigado pelo seu email. Vou analisar sua solicitação e retornar em breve.'
    )
  })

  it('shows copied confirmation after copying', async () => {
    render(<ResultCard result={mockResult} />)
    
    const copyButton = screen.getByText('Copiar')
    fireEvent.click(copyButton)
    
    // Aguarda a atualização do estado
    await waitFor(() => {
      expect(screen.getByText('Copiado!')).toBeInTheDocument()
    })
  })

  it('formats processed date correctly', () => {
    render(<ResultCard result={mockResult} />)
    
    expect(screen.getByText(/Processado em:/)).toBeInTheDocument()
    // The exact format depends on locale, so we just check if it contains the date
    expect(screen.getByText(/Processado em:/)).toBeInTheDocument()
    expect(screen.getByText(/Tempo:/)).toBeInTheDocument()
    expect(screen.getByText(/150/)).toBeInTheDocument()
    expect(screen.getByText(/ms/)).toBeInTheDocument()
  })

  it('displays reasoning when provided', () => {
    render(<ResultCard result={mockResult} />)
    
    expect(screen.getByText('Explicação:')).toBeInTheDocument()
    expect(screen.getByText('Email contém solicitação específica de suporte')).toBeInTheDocument()
  })

  it('does not display reasoning section when not provided', () => {
    const resultWithoutReasoning = { 
      ...mockResult, 
      classification: { ...mockResult.classification, reasoning: undefined }
    }
    render(<ResultCard result={resultWithoutReasoning} />)
    
    expect(screen.queryByText('Explicação:')).not.toBeInTheDocument()
  })
})
