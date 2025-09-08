import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { FileUpload } from '../FileUpload'
import { FileUploadState } from '../../types'

const mockOnFileChange = vi.fn()
const mockOnError = vi.fn()

const defaultProps = {
  state: {
    file: null,
    isUploading: false,
  } as FileUploadState,
  onFileChange: mockOnFileChange,
  onError: mockOnError,
}

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area when no file is selected', () => {
    render(<FileUpload {...defaultProps} />)

    expect(screen.getByText('Clique ou arraste um arquivo')).toBeInTheDocument()
    expect(
      screen.getByText('Suporta arquivos .txt, .pdf e .eml (máx. 10MB)')
    ).toBeInTheDocument()
  })

  it('renders file info when file is selected', () => {
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const props = {
      ...defaultProps,
      state: { ...defaultProps.state, file },
    }

    render(<FileUpload {...props} />)

    expect(screen.getByText('test.txt')).toBeInTheDocument()
    expect(screen.getByText('📝')).toBeInTheDocument()
  })

  it('shows error message when error exists', () => {
    const props = {
      ...defaultProps,
      state: { ...defaultProps.state, error: 'Arquivo muito grande' },
    }

    render(<FileUpload {...props} />)

    expect(screen.getByText('Arquivo muito grande')).toBeInTheDocument()
    // Verifica se o ícone de alerta está presente usando o SVG
    expect(screen.getByTestId('alert-icon')).toBeInTheDocument()
  })

  it('calls onFileChange when file is removed', () => {
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const props = {
      ...defaultProps,
      state: { ...defaultProps.state, file },
    }

    render(<FileUpload {...props} />)

    const removeButton = screen.getByLabelText('Remover arquivo')
    fireEvent.click(removeButton)

    expect(mockOnFileChange).toHaveBeenCalledWith(null)
  })

  it('displays correct file icon for different file types', () => {
    const testCases = [
      { file: new File([''], 'test.pdf'), expectedIcon: '📄' },
      { file: new File([''], 'test.txt'), expectedIcon: '📝' },
      { file: new File([''], 'test.eml'), expectedIcon: '📧' },
      { file: new File([''], 'test.unknown'), expectedIcon: '📎' },
    ]

    testCases.forEach(({ file, expectedIcon }) => {
      const props = {
        ...defaultProps,
        state: { ...defaultProps.state, file },
      }

      const { container } = render(<FileUpload {...props} />)
      expect(container.innerHTML).toContain(expectedIcon)
    })
  })

  it('formats file size correctly', () => {
    const file = new File(['x'.repeat(1024)], 'test.txt', {
      type: 'text/plain',
    })
    const props = {
      ...defaultProps,
      state: { ...defaultProps.state, file },
    }

    render(<FileUpload {...props} />)

    expect(screen.getByText('1 KB')).toBeInTheDocument()
  })
})
