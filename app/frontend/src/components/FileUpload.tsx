import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, AlertCircle } from 'lucide-react'
import { FileUploadState } from '../types'

interface FileUploadProps {
  state: FileUploadState
  onFileChange: (file: File | null) => void
  onError: (error: string) => void
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const ACCEPTED_TYPES = {
  'text/plain': ['.txt'],
  'application/pdf': ['.pdf'],
  'message/rfc822': ['.eml'],
}

export function FileUpload({ state, onFileChange, onError }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0]
        if (rejection.errors.some((e: any) => e.code === 'file-too-large')) {
          onError('Arquivo muito grande. Tamanho máximo: 10MB')
        } else if (
          rejection.errors.some((e: any) => e.code === 'file-invalid-type')
        ) {
          onError('Tipo de arquivo não suportado. Use .txt, .pdf ou .eml')
        } else {
          onError('Erro ao processar arquivo')
        }
        return
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        onFileChange(file)
      }
    },
    [onFileChange, onError]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  })

  const removeFile = () => {
    onFileChange(null)
  }

  const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) {
      return '📄'
    } else if (fileName.endsWith('.txt')) {
      return '📝'
    } else if (fileName.endsWith('.eml')) {
      return '📧'
    }
    return '📎'
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="w-full">
      {!state.file ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive || dragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
          onDragEnter={() => setDragActive(true)}
          onDragLeave={() => setDragActive(false)}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <div className="space-y-2">
            <p className="text-lg font-medium text-gray-900">
              {isDragActive
                ? 'Solte o arquivo aqui'
                : 'Clique ou arraste um arquivo'}
            </p>
            <p className="text-sm text-gray-500">
              Suporta arquivos .txt, .pdf e .eml (máx. 10MB)
            </p>
          </div>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getFileIcon(state.file.name)}</span>
              <div>
                <p className="font-medium text-gray-900">{state.file.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(state.file.size)}
                </p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="p-1 hover:bg-gray-200 rounded-full transition-colors duration-200"
              aria-label="Remover arquivo"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>
      )}

      {state.error && (
        <div className="mt-3 flex items-center space-x-2 text-error-600 text-sm">
          <AlertCircle className="w-4 h-4" data-testid="alert-icon" />
          <span>{state.error}</span>
        </div>
      )}
    </div>
  )
}
