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

export default function QueryInput({ onSubmit, isLoading, isDatasetLoaded }) {
  const [question, setQuestion] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!question.trim() || isLoading || !isDatasetLoaded) return
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
        <div className="inline-flex items-center gap-2 bg-darkCard border border-borderSubtle rounded-full px-4 py-1.5 mb-4 shadow-sm">
          <Sparkles size={13} className="text-accentPrimary" />
          <span className="text-accentPrimary text-[10px] font-bold tracking-wider uppercase">
            Powered by Llama 3 + ChromaDB RAG
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-normal font-serif text-textPrimary mb-3 leading-tight">
          Ask your database anything
        </h1>
        {/* Dark Gold Underline Divider */}
        <div className="w-12 h-[2.5px] bg-accentPrimary mx-auto mb-4 rounded-full" />
        <p className="text-textSecondary text-sm md:text-base max-w-xl mx-auto font-sans leading-relaxed">
          Type a question in plain English — AskSQL generates the SQL, validates it, executes it, and explains what it found.
        </p>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className={`relative glass-card p-1 group transition-colors duration-200 ${
          isDatasetLoaded ? 'focus-within:border-accentPrimary/50' : 'opacity-70 bg-darkCardHover/20'
        }`}>
          <div className="flex items-start gap-3 p-3">
            <Search size={20} className="text-textSecondary mt-1 shrink-0" />
            <textarea
              id="query-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isDatasetLoaded 
                ? "e.g. What were the top 5 best-selling product categories last month?" 
                : "Please upload a CSV dataset or click 'Try sample dataset' in the sidebar to start asking questions..."
              }
              rows={3}
              className="flex-1 bg-transparent text-textPrimary placeholder-textSecondary/50 resize-none outline-none text-sm md:text-base leading-relaxed font-sans"
              disabled={isLoading || !isDatasetLoaded}
              aria-label="Natural language query input"
            />
          </div>
          <div className="flex items-center justify-between px-4 pb-3">
            <span className="text-[11px] text-textSecondary/70 font-sans">
              Press <kbd className="bg-darkBg px-1.5 py-0.5 rounded text-textSecondary font-mono text-[10px] border border-borderSubtle">Ctrl+Enter</kbd> to submit
            </span>
            <button
              id="submit-query-btn"
              type="submit"
              disabled={!question.trim() || isLoading || !isDatasetLoaded}
              className="btn-neon flex items-center gap-2 px-5 py-2.5 text-sm font-semibold tracking-wide"
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
      <div className="mt-6">
        <p className="text-[10px] text-textSecondary uppercase tracking-wider mb-3 font-semibold font-sans">Try an example</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button
              key={i}
              id={`example-question-${i}`}
              onClick={() => handleExample(q)}
              disabled={isLoading || !isDatasetLoaded}
              className="text-xs bg-darkCard hover:bg-darkCardHover border border-borderSubtle hover:border-accentPrimary/40 text-textSecondary hover:text-accentPrimary rounded-full px-3.5 py-1.5 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed font-sans"
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
          className="pulse-dot w-1.5 h-1.5 bg-textPrimary rounded-full inline-block"
        />
      ))}
    </span>
  )
}
