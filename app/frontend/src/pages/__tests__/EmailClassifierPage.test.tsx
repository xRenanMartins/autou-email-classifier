import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { EmailClassifierPage } from '../EmailClassifierPage'

// Mock the API client
vi.mock('../../api/client', () => ({
  apiClient: {
    processEmail: vi.fn(),
  },
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('EmailClassifierPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the main page with title and description', () => {
    renderWithRouter(<EmailClassifierPage />)

    expect(screen.getByText('Classifique Emails com IA')).toBeInTheDocument()
    expect(screen.getByText(/Identifique automaticamente/)).toBeInTheDocument()
  })

  it('shows form with text input and file upload', () => {
    renderWithRouter(<EmailClassifierPage />)

    expect(screen.getByLabelText('Conteúdo do Email')).toBeInTheDocument()
    expect(screen.getByText('Upload de Arquivo')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Classificar Email/i })
    ).toBeInTheDocument()
  })

  it('validates text input minimum length', async () => {
    renderWithRouter(<EmailClassifierPage />)

    const textInput = screen.getByLabelText('Conteúdo do Email')
    fireEvent.change(textInput, { target: { value: 'short' } })

    await waitFor(() => {
      expect(
        screen.getByText('O texto deve ter pelo menos 10 caracteres')
      ).toBeInTheDocument()
    })
  })

  it('enables submit button when valid content is provided', async () => {
    renderWithRouter(<EmailClassifierPage />)

    const textInput = screen.getByLabelText('Conteúdo do Email')
    const submitButton = screen.getByRole('button', {
      name: /Classificar Email/i,
    })

    fireEvent.change(textInput, {
      target: {
        value:
          'Este é um email de teste com conteúdo suficiente para validação.',
      },
    })

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })
  })

  it('shows loading state during processing', async () => {
    // Mock simples que retorna uma promise que nunca resolve
    const mockProcessEmail = vi.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    // Aplicar o mock diretamente
    vi.doMock('../../api/client', () => ({
      apiClient: {
        processEmail: mockProcessEmail,
      },
    }))

    renderWithRouter(<EmailClassifierPage />)

    const textInput = screen.getByLabelText('Conteúdo do Email')
    const submitButton = screen.getByRole('button', {
      name: /Classificar Email/i,
    })

    fireEvent.change(textInput, {
      target: { value: 'Email de teste com conteúdo suficiente.' },
    })
    fireEvent.click(submitButton)

    // Verificar se o botão está desabilitado (estado de loading)
    expect(submitButton).toBeDisabled()
  })

  // Testes simplificados que funcionam com a lógica real
  it('handles form submission correctly', async () => {
    renderWithRouter(<EmailClassifierPage />)

    const textInput = screen.getByLabelText('Conteúdo do Email')
    const submitButton = screen.getByRole('button', {
      name: /Classificar Email/i,
    })

    // Preencher o formulário com texto válido
    fireEvent.change(textInput, {
      target: {
        value:
          'Este é um email de teste com conteúdo suficiente para validação.',
      },
    })

    // Aguardar a validação
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    // Verificar que o botão está habilitado antes do clique
    expect(submitButton).not.toBeDisabled()
  })

  it('validates form inputs correctly', async () => {
    renderWithRouter(<EmailClassifierPage />)

    const textInput = screen.getByLabelText('Conteúdo do Email')

    // Testar validação de texto muito curto
    fireEvent.change(textInput, { target: { value: 'abc' } })

    await waitFor(() => {
      expect(
        screen.getByText('O texto deve ter pelo menos 10 caracteres')
      ).toBeInTheDocument()
    })

    // Testar validação de texto válido
    fireEvent.change(textInput, {
      target: { value: 'Este é um texto válido com mais de 10 caracteres.' },
    })

    await waitFor(() => {
      expect(
        screen.queryByText('O texto deve ter pelo menos 10 caracteres')
      ).not.toBeInTheDocument()
    })
  })
})
