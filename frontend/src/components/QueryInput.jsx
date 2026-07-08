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
        <div className="inline-flex items-center gap-2 bg-white/[0.02] border border-white/[0.06] rounded-full px-4 py-1.5 mb-4">
          <Sparkles size={13} className="text-[#E8B923]" />
          <span className="text-[#E8B923] text-[10px] font-semibold tracking-wider uppercase">
            Powered by Llama 3 + ChromaDB RAG
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-normal font-serif text-[#F5F0E6] mb-3 leading-tight">
          Ask your database anything
        </h1>
        {/* Short Gold Underline Divider */}
        <div className="w-12 h-[2.5px] bg-[#E8B923] mx-auto mb-4 rounded-full" />
        <p className="text-[#C2BAA8] text-sm md:text-base max-w-xl mx-auto font-sans leading-relaxed">
          Type a question in plain English — AskSQL generates the SQL, validates it, executes it, and explains what it found.
        </p>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative glass-card p-1 group focus-within:border-[#E8B923]/40 transition-colors duration-200 bg-[#454E5A]/60">
          <div className="flex items-start gap-3 p-3">
            <Search size={20} className="text-[#C2BAA8] mt-1 shrink-0" />
            <textarea
              id="query-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. What were the top 5 best-selling product categories last month?"
              rows={3}
              className="flex-1 bg-transparent text-[#F5F0E6] placeholder-[#C2BAA8]/50 resize-none outline-none text-sm md:text-base leading-relaxed font-sans"
              disabled={isLoading}
              aria-label="Natural language query input"
            />
          </div>
          <div className="flex items-center justify-between px-4 pb-3">
            <span className="text-[11px] text-[#C2BAA8]/70 font-sans">
              Press <kbd className="bg-[#3D4550] px-1.5 py-0.5 rounded text-[#C2BAA8] font-mono text-[10px]">Ctrl+Enter</kbd> to submit
            </span>
            <button
              id="submit-query-btn"
              type="submit"
              disabled={!question.trim() || isLoading}
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
        <p className="text-[10px] text-[#C2BAA8] uppercase tracking-wider mb-3 font-semibold font-sans">Try an example</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button
              key={i}
              id={`example-question-${i}`}
              onClick={() => handleExample(q)}
              disabled={isLoading}
              className="text-xs bg-[#454E5A]/40 hover:bg-[#454E5A]/80 border border-white/[0.04] hover:border-[#E8B923]/25 text-[#C2BAA8] hover:text-[#E8B923] rounded-full px-3.5 py-1.5 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed font-sans"
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
          className="pulse-dot w-1.5 h-1.5 bg-[#2A2620] rounded-full inline-block"
        />
      ))}
    </span>
  )
}
