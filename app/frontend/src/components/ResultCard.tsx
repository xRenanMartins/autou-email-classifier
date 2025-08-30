import { CheckCircle, XCircle, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { EmailProcessingResponse } from '../lib/api'
import { motion } from 'framer-motion'

interface ResultCardProps {
  result: EmailProcessingResponse
}

export function ResultCard({ result }: ResultCardProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Erro ao copiar para área de transferência:', err)
    }
  }

  const getLabelColor = (label: string) => {
    return label === 'PRODUCTIVE' 
      ? 'bg-success-100 text-success-800 border-success-200' 
      : 'bg-warning-100 text-warning-800 border-warning-200'
  }

  const getLabelIcon = (label: string) => {
    return label === 'PRODUCTIVE' 
      ? <CheckCircle className="w-5 h-5" />
      : <XCircle className="w-5 h-5" />
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600'
    if (confidence >= 0.6) return 'text-warning-600'
    return 'text-error-600'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Classification Result */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Resultado da Classificação
          </h3>
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getLabelColor(result.classification.label)}`}>
            {getLabelIcon(result.classification.label)}
            <span className="font-medium">
              {result.classification.label === 'PRODUCTIVE' ? 'Produtivo' : 'Improdutivo'}
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Confiança:</span>
            <span className={`font-semibold ${getConfidenceColor(result.classification.confidence)}`}>
              {Math.round(result.classification.confidence * 100)}%
            </span>
          </div>

          {result.classification.reasoning && (
            <div>
              <span className="text-sm font-medium text-gray-600 block mb-2">
                Explicação:
              </span>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                {result.classification.reasoning}
              </p>
            </div>
          )}

          <div className="text-xs text-gray-500">
            Processado em: {new Date().toLocaleString('pt-BR')} • Tempo: {result.processing_time_ms}ms
          </div>
        </div>
      </div>

      {/* Suggested Response */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Resposta Sugerida
          </h3>
          <button
            onClick={() => copyToClipboard(result.suggested_response.body)}
            className="flex items-center space-x-2 px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-colors duration-200"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                <span>Copiado!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copiar</span>
              </>
            )}
          </button>
        </div>

        <div className="space-y-4">
          {result.suggested_response.subject && (
            <div>
              <span className="text-sm font-medium text-gray-600 block mb-2">
                Assunto:
              </span>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                {result.suggested_response.subject}
              </p>
            </div>
          )}

          <div>
            <span className="text-sm font-medium text-gray-600 block mb-2">
              Corpo da Mensagem:
            </span>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {result.suggested_response.body}
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

