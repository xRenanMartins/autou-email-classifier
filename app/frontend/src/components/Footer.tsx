import { Github, Heart } from 'lucide-react'

export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2 text-gray-600">

          </div>
          
          <div className="flex items-center space-x-6 text-sm text-gray-500">
            <a 
              href="#" 
              className="hover:text-primary-600 transition-colors duration-200"
            >
              Sobre
            </a>
            <a 
              href="#" 
              className="hover:text-primary-600 transition-colors duration-200"
            >
              Privacidade
            </a>
            <a 
              href="#" 
              className="hover:text-primary-600 transition-colors duration-200"
            >
              Termos
            </a>
            <a 
              href="https://github.com/xRenanMartins/autou-email-classifier" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center space-x-1 hover:text-primary-600 transition-colors duration-200"
            >
              <Github className="w-4 h-4" />
              <span>GitHub</span>
            </a>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>&copy; 2025 Email Classifier. Todos os direitos reservados.</p>
        </div>
      </div>
    </footer>
  )
}

