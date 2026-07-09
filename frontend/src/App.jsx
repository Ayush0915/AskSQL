import { useState, useEffect } from 'react'
import { askQuestion, fetchSchema, healthCheck } from './api'
import QueryInput from './components/QueryInput'
import ResultsTable from './components/ResultsTable'
import SqlDisplay from './components/SqlDisplay'
import QueryHistory from './components/QueryHistory'
import SchemaBrowser from './components/SchemaBrowser'

export default function App() {
  const [sessionId, setSessionId] = useState(() => {
    return sessionStorage.getItem('asksql_session_id') || ''
  })

  const [schema, setSchema] = useState([])
  const [isDatasetLoaded, setIsDatasetLoaded] = useState(false)
  const [exampleQuestions, setExampleQuestions] = useState([])
  const [history, setHistory] = useState([])
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSchemaLoading, setIsSchemaLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  
  const [currentResponse, setCurrentResponse] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState('')

  // Load history when sessionId changes
  useEffect(() => {
    if (sessionId) {
      const saved = localStorage.getItem(`asksql_history_${sessionId}`)
      setHistory(saved ? JSON.parse(saved) : [])
    } else {
      setHistory([])
    }
  }, [sessionId])

  // Check backend health and load schema on mount / sessionId change
  useEffect(() => {
    async function init() {
      try {
        await healthCheck()
        setBackendStatus('connected')
      } catch (err) {
        console.error('Backend healthcheck failed:', err)
        setBackendStatus('disconnected')
      }

      if (sessionId) {
        setIsSchemaLoading(true)
        try {
          const data = await fetchSchema(sessionId)
          setSchema(data.tables || [])
          setExampleQuestions(data.example_questions || [])
          if (data.tables && data.tables.length > 0) {
            setIsDatasetLoaded(true)
          } else {
            sessionStorage.removeItem('asksql_session_id')
            localStorage.removeItem(`asksql_history_${sessionId}`)
            setSessionId('')
            setIsDatasetLoaded(false)
            setErrorMsg('Your session expired — please reload your data.')
          }
        } catch (err) {
          console.error('Failed to load schema browser:', err)
          sessionStorage.removeItem('asksql_session_id')
          localStorage.removeItem(`asksql_history_${sessionId}`)
          setSessionId('')
          setIsDatasetLoaded(false)
          setErrorMsg('Your session expired — please reload your data.')
        } finally {
          setIsSchemaLoading(false)
        }
      }
    }
    init()
  }, [sessionId])

  // Persist history to localStorage scoped by session ID
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`asksql_history_${sessionId}`, JSON.stringify(history))
    }
  }, [history, sessionId])

  const handleQuerySubmit = async (question) => {
    setIsLoading(true)
    setErrorMsg(null)
    setCurrentQuestion(question)
    setCurrentResponse(null)

    try {
      const res = await askQuestion(question, sessionId)
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
        const errMsg = res.error || 'Failed to complete query pipeline.'
        setErrorMsg(errMsg)
        
        // If session expired or not found, clear session
        if (errMsg.includes('No dataset loaded') || errMsg.includes('Database file not found')) {
          sessionStorage.removeItem('asksql_session_id')
          localStorage.removeItem(`asksql_history_${sessionId}`)
          setSessionId('')
          setIsDatasetLoaded(false)
        }

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
      
      if (typeof errorDetail === 'string' && (errorDetail.includes('No dataset loaded') || errorDetail.includes('Database file not found'))) {
        sessionStorage.removeItem('asksql_session_id')
        localStorage.removeItem(`asksql_history_${sessionId}`)
        setSessionId('')
        setIsDatasetLoaded(false)
      }

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

  const handleDatasetCleared = () => {
    setSchema([])
    setExampleQuestions([])
    setIsDatasetLoaded(false)
    setCurrentResponse(null)
    setErrorMsg(null)
    setHistory([])
    localStorage.removeItem(`asksql_history_${sessionId}`)
    sessionStorage.removeItem('asksql_session_id')
    setSessionId('')
  }

  return (
    <div className="min-h-screen bg-darkBg text-textPrimary flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-borderSubtle bg-darkCard sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">⚡</span>
            <span className="font-bold text-lg text-textPrimary tracking-tight font-serif">
              AskSQL
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Backend connection indicator */}
            <div className="flex items-center gap-2 bg-darkCard px-3 py-1.5 rounded-full border border-borderSubtle shadow-sm">
              <span className={`w-2 h-2 rounded-full ${
                backendStatus === 'connected' ? 'bg-successGreen shadow-[0_0_8px_var(--success)]' :
                backendStatus === 'checking' ? 'bg-btnGold animate-pulse' :
                'bg-errorRed shadow-[0_0_8px_var(--error)]'
              }`} />
              <span className="text-[10px] font-bold text-accentPrimary uppercase tracking-wider">
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
          <SchemaBrowser 
            schema={schema} 
            isLoading={isSchemaLoading} 
            sessionId={sessionId}
            isDatasetLoaded={isDatasetLoaded}
            onDatasetLoaded={(tables, questions) => {
              setSchema(tables)
              setExampleQuestions(questions || [])
              setIsDatasetLoaded(true)
            }}
            onDatasetCleared={handleDatasetCleared}
          />
          {isDatasetLoaded && (
            <QueryHistory
              history={history}
              onRerun={handleRerunHistory}
              onClear={handleClearHistory}
            />
          )}
        </div>

        {/* Center Panel - Input, Output, Results */}
        <div className="lg:col-span-3 space-y-8">
          <div className="glass-card p-6">
            <QueryInput 
              onSubmit={handleQuerySubmit} 
              isLoading={isLoading} 
              isDatasetLoaded={isDatasetLoaded} 
              exampleQuestions={exampleQuestions}
            />
          </div>

          {/* Render Error if any */}
          {errorMsg && (
            <div className="bg-errorRed/10 border border-errorRed/25 text-textPrimary p-5 rounded-xl text-sm leading-relaxed animate-fade-in-up">
              <strong className="block font-semibold mb-1 text-errorRed">Pipeline Execution Failure</strong>
              <span className="text-textSecondary">{errorMsg}</span>
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
      <footer className="border-t border-borderSubtle bg-darkCard py-5 mt-auto">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-xs text-textSecondary">
          <p>© 2026 AskSQL Project</p>
        </div>
      </footer>
    </div>
  )
}
