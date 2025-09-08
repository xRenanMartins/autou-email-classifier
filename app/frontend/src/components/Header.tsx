import { Mail, Zap, Brain } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Email Classifier
              </h1>
              <p className="text-sm text-gray-500">
                Classificação Inteligente com IA
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
              <Zap className="w-4 h-4" />
              <span>Processamento Rápido</span>
            </div>
            <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
              <Brain className="w-4 h-4" />
              <span>IA Avançada</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
