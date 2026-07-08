import { useState } from 'react'
import { Search, Sparkles, ChevronRight } from 'lucide-react'

const EXAMPLE_QUESTIONS = [
  'How many orders were placed in total?',
  'What are the top 5 best-selling products by quantity?',
  'Which customers have spent more than $500 total?',
  'What is the average order value by month?',
  'How many orders were delivered late?',
  'Which product category has the most orders?',
]

export default function QueryInput({ onSubmit, isLoading }) {
  const [question, setQuestion] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!question.trim() || isLoading) return
    onSubmit(question.trim())
  }

  const handleExample = (q) => {
    setQuestion(q)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit(e)
    }
  }

  return (
    <div className="w-full">
      {/* Heading */}
      <div className="mb-6 text-center">
        <div className="inline-flex items-center gap-2 bg-sky-500/10 border border-sky-500/20 rounded-full px-4 py-1.5 mb-4">
          <Sparkles size={14} className="text-sky-400" />
          <span className="text-sky-400 text-xs font-medium tracking-wide uppercase">Powered by Llama 3 + ChromaDB RAG</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-sky-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2">
          Ask your database anything
        </h1>
        <p className="text-slate-400 text-sm md:text-base max-w-xl mx-auto">
          Type a question in plain English — AskSQL generates the SQL, validates it, executes it, and explains what it found.
        </p>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative glass-card p-1 group focus-within:border-sky-500/40 transition-colors duration-200">
          <div className="flex items-start gap-3 p-3">
            <Search size={20} className="text-slate-500 mt-1 shrink-0" />
            <textarea
              id="query-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. What were the top 5 best-selling product categories last month?"
              rows={3}
              className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 resize-none outline-none text-sm md:text-base leading-relaxed"
              disabled={isLoading}
              aria-label="Natural language query input"
            />
          </div>
          <div className="flex items-center justify-between px-4 pb-3">
            <span className="text-xs text-slate-600">
              Press <kbd className="bg-slate-700 px-1.5 py-0.5 rounded text-slate-400 font-mono text-xs">Ctrl+Enter</kbd> to submit
            </span>
            <button
              id="submit-query-btn"
              type="submit"
              disabled={!question.trim() || isLoading}
              className="btn-neon flex items-center gap-2 px-5 py-2.5 text-sm font-semibold"
            >
              {isLoading ? (
                <>
                  <LoadingDots />
                  <span>Thinking…</span>
                </>
              ) : (
                <>
                  <span>Run Query</span>
                  <ChevronRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Example questions */}
      <div className="mt-5">
        <p className="text-xs text-slate-600 uppercase tracking-wide mb-3 font-medium">Try an example</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button
              key={i}
              id={`example-question-${i}`}
              onClick={() => handleExample(q)}
              disabled={isLoading}
              className="text-xs bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/60 hover:border-sky-500/30 text-slate-400 hover:text-sky-300 rounded-full px-3 py-1.5 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function LoadingDots() {
  return (
    <span className="flex gap-1 items-center">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="pulse-dot w-1.5 h-1.5 bg-white rounded-full inline-block"
        />
      ))}
    </span>
  )
}
