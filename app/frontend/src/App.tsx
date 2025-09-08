import { Routes, Route } from 'react-router-dom'
import { EmailClassifierPage } from './pages/EmailClassifierPage'
import { Header } from './components/Header'
import { Footer } from './components/Footer'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<EmailClassifierPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
