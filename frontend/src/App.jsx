import { useState, useEffect } from 'react'
import { askQuestion, fetchSchema, healthCheck } from './api'
import QueryInput from './components/QueryInput'
import ResultsTable from './components/ResultsTable'
import SqlDisplay from './components/SqlDisplay'
import QueryHistory from './components/QueryHistory'
import SchemaBrowser from './components/SchemaBrowser'

export default function App() {
  const [schema, setSchema] = useState([])
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('asksql_history')
    return saved ? JSON.parse(saved) : []
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSchemaLoading, setIsSchemaLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  
  const [currentResponse, setCurrentResponse] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState('')

  // Check backend health and load schema on mount
  useEffect(() => {
    async function init() {
      try {
        await healthCheck()
        setBackendStatus('connected')
      } catch (err) {
        console.error('Backend healthcheck failed:', err)
        setBackendStatus('disconnected')
      }

      setIsSchemaLoading(true)
      try {
        const data = await fetchSchema()
        setSchema(data.tables || [])
      } catch (err) {
        console.error('Failed to load schema browser:', err)
      } finally {
        setIsSchemaLoading(false)
      }
    }
    init()
  }, [])

  // Persist history to localStorage
  useEffect(() => {
    localStorage.setItem('asksql_history', JSON.stringify(history))
  }, [history])

  const handleQuerySubmit = async (question) => {
    setIsLoading(true)
    setErrorMsg(null)
    setCurrentQuestion(question)
    setCurrentResponse(null)

    try {
      const res = await askQuestion(question)
      setCurrentResponse(res)

      if (res.success) {
        // Add to history
        const newHistoryItem = {
          id: Date.now().toString(),
          question,
          success: true,
          rowCount: res.results ? res.results.length : 0,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        setHistory(prev => [...prev, newHistoryItem])
      } else {
        setErrorMsg(res.error || 'Failed to complete query pipeline.')
        const newHistoryItem = {
          id: Date.now().toString(),
          question,
          success: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        setHistory(prev => [...prev, newHistoryItem])
      }
    } catch (err) {
      console.error(err)
      const errorDetail = err.response?.data?.detail || err.message || 'API request error.'
      setErrorMsg(errorDetail)
      const newHistoryItem = {
        id: Date.now().toString(),
        question,
        success: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setHistory(prev => [...prev, newHistoryItem])
    } finally {
      setIsLoading(false)
    }
  }

  const handleRerunHistory = (q) => {
    handleQuerySubmit(q)
  }

  const handleClearHistory = () => {
    setHistory([])
  }

  return (
    <div className="min-h-screen bg-darkBg text-textPrimary flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-white/[0.04] bg-[#454E5A]/50 sticky top-0 z-50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">⚡</span>
            <span className="font-bold text-lg text-[#F5F0E6] tracking-tight font-serif">
              AskSQL
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Backend connection indicator */}
            <div className="flex items-center gap-2 bg-[#3D4550]/80 px-3 py-1.5 rounded-full border border-white/[0.05]">
              <span className={`w-2 h-2 rounded-full ${
                backendStatus === 'connected' ? 'bg-[#4ADE80] shadow-[0_0_8px_rgba(74,222,128,0.5)]' :
                backendStatus === 'checking' ? 'bg-[#E8B923] animate-pulse' :
                'bg-[#C1443A] shadow-[0_0_8px_rgba(193,68,58,0.5)]'
              }`} />
              <span className="text-xs font-semibold text-[#C2BAA8]">
                {backendStatus === 'connected' ? 'API CONNECTED' :
                 backendStatus === 'checking' ? 'CONNECTING...' :
                 'API DISCONNECTED'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Sidebars - Schema Browser & History */}
        <div className="space-y-6 lg:col-span-1">
          <SchemaBrowser schema={schema} isLoading={isSchemaLoading} />
          <QueryHistory
            history={history}
            onRerun={handleRerunHistory}
            onClear={handleClearHistory}
          />
        </div>

        {/* Center Panel - Input, Output, Results */}
        <div className="lg:col-span-3 space-y-8">
          <div className="glass-card p-6 bg-[#454E5A]/40">
            <QueryInput onSubmit={handleQuerySubmit} isLoading={isLoading} />
          </div>

          {/* Render Error if any */}
          {errorMsg && (
            <div className="bg-[#C1443A]/10 border border-[#C1443A]/30 text-[#F5F0E6] p-5 rounded-xl text-sm leading-relaxed animate-fade-in-up">
              <strong className="block font-semibold mb-1 text-[#C1443A]">Pipeline Execution Failure</strong>
              <span className="text-[#C2BAA8]">{errorMsg}</span>
            </div>
          )}

          {/* Loading Skeleton */}
          {isLoading && (
            <div className="space-y-4">
              <div className="skeleton h-24 w-full" />
              <div className="skeleton h-12 w-full" />
              <div className="skeleton h-64 w-full" />
            </div>
          )}

          {/* Response Displays */}
          {!isLoading && currentResponse && (
            <div className="space-y-6">
              {/* Generated SQL & Explanation details */}
              <SqlDisplay
                sql={currentResponse.sql}
                explanation={currentResponse.explanation}
                retriesUsed={currentResponse.retries_used}
              />
              
              {/* Results table if query succeeded */}
              {currentResponse.success && (
                <ResultsTable results={currentResponse.results} />
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.04] bg-[#454E5A]/25 py-5 mt-auto">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-xs text-[#C2BAA8]">
          <p>© 2026 AskSQL Project</p>
          <div className="flex gap-4">
            <span>Solo Capstone Project</span>
            <span>·</span>
            <span>React + FastAPI + Llama 3</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
