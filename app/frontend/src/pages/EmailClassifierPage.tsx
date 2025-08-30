import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'react-hot-toast'
import { Send, FileText, AlertCircle, RefreshCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

import { FileUpload } from '../components/FileUpload'
import { ResultCard } from '../components/ResultCard'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useEmailProcessing } from '../hooks/useEmailProcessing'
import { useApiHealth } from '../hooks/useApiHealth'

const formSchema = z.object({
  text: z.string().min(10, 'O texto deve ter pelo menos 10 caracteres'),
})

type FormSchema = z.infer<typeof formSchema>

export function EmailClassifierPage() {
  const [fileState, setFileState] = useState<{
    file: File | null;
    isUploading: boolean;
    error?: string;
  }>({
    file: null,
    isUploading: false,
  })

  // Hooks personalizados para API
  const { 
    isLoading, 
    error: processingError, 
    result, 
    processEmailText, 
    processEmailFile, 
    reset: resetProcessing 
  } = useEmailProcessing()

  const { 
    isHealthy, 
    isLoading: healthLoading, 
    stats, 
    refresh: refreshHealth 
  } = useApiHealth()

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    watch,
  } = useForm<FormSchema>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
  })

  const watchedText = watch('text', '')

  const handleFileChange = (file: File | null) => {
    setFileState(prev => ({ ...prev, file, error: undefined }))
  }

  const handleFileError = (error: string) => {
    setFileState(prev => ({ ...prev, error }))
    toast.error(error)
  }

  const onSubmit = async (data: FormSchema) => {
    if (!data.text.trim() && !fileState.file) {
      toast.error('Por favor, insira um texto ou faça upload de um arquivo')
      return
    }

    try {
      if (fileState.file) {
        // Processa arquivo
        await processEmailFile(fileState.file, data.text.trim() || undefined)
      } else if (data.text.trim()) {
        // Processa texto
        await processEmailText({
          text: data.text.trim(),
          subject: data.text.trim().substring(0, 100), // Usa início do texto como assunto
        })
      }
      
      toast.success('Email processado com sucesso!')
      
      // Reset form after successful processing
      reset()
      setFileState({ file: null, isUploading: false })
      
    } catch (error: any) {
      const errorMessage = error.message || 'Erro ao processar email'
      toast.error(errorMessage)
    }
  }

  const hasContent = watchedText.trim() || fileState.file

  return (
    <div className="w-full">
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status da API */}
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            API: {isHealthy ? 'Online' : 'Offline'}
          </span>
          {stats && (
            <span className="text-sm text-gray-500">
              • {stats.total_emails} emails processados
            </span>
          )}
          <button
            onClick={refreshHealth}
            disabled={healthLoading}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${healthLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Hero Section */}
        <div className="text-center mb-12">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-4xl font-bold text-gray-900 mb-4"
          >
            Classifique Emails com IA
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-xl text-gray-600 max-w-2xl mx-auto"
          >
            Identifique automaticamente se um email é produtivo ou improdutivo e receba respostas sugeridas inteligentes
          </motion.p>
        </div>

        {/* Main Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="card mb-8"
        >
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Text Input */}
            <div>
              <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
                Conteúdo do Email
              </label>
              <textarea
                {...register('text')}
                id="text"
                placeholder="Cole aqui o conteúdo do email que deseja classificar..."
                className="textarea-field"
                rows={6}
              />
              {errors.text && (
                <p className="mt-2 text-sm text-error-600 flex items-center space-x-1">
                  <AlertCircle className="w-4 h-4" />
                  <span>{errors.text.message}</span>
                </p>
              )}
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">ou</span>
              </div>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload de Arquivo
              </label>
              <FileUpload
                state={fileState}
                onFileChange={handleFileChange}
                onError={handleFileError}
              />
            </div>

            {/* Submit Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={!hasContent || !isValid || isLoading}
                className="btn-primary flex items-center space-x-2 px-8 py-3 text-lg"
              >
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Processando...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    <span>Classificar Email</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
            >
              <ResultCard result={result} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        {processingError && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card border-error-200 bg-error-50"
          >
            <div className="flex items-center space-x-3 text-error-700">
              <AlertCircle className="w-5 h-5" />
              <div>
                <h3 className="font-medium">Erro no Processamento</h3>
                <p className="text-sm">{processingError}</p>
              </div>
            </div>
            <button
              onClick={resetProcessing}
              className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
            >
              Tentar novamente
            </button>
          </motion.div>
        )}

        {/* Features Section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-16 grid md:grid-cols-3 gap-8"
        >
          <div className="text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Múltiplos Formatos
            </h3>
            <p className="text-gray-600">
              Suporte para texto, PDF e arquivos .eml
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-success-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Respostas Inteligentes
            </h3>
            <p className="text-gray-600">
              Sugestões personalizadas baseadas no contexto
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-warning-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-warning-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Classificação Rápida
            </h3>
            <p className="text-gray-600">
              Processamento em segundos com alta precisão
            </p>
          </div>
        </motion.div>
      </main>
    </div>
  )
}

