import { useState } from 'react'
import { Code2, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

export default function SqlDisplay({ sql, explanation, retriesUsed }) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!sql) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback
    }
  }

  return (
    <div className="space-y-3 animate-fade-in-up">
      {/* Explanation card */}
      {explanation && (
        <div className="glass-card p-4 border-l-4 border-l-sky-500/60">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-sky-500/20 flex items-center justify-center shrink-0 mt-0.5">
              <span className="text-sky-400 text-xs font-bold">?</span>
            </div>
            <div>
              <p className="text-xs font-semibold text-sky-400 uppercase tracking-wide mb-1">Plain-English Explanation</p>
              <p className="text-slate-300 text-sm leading-relaxed">{explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* SQL toggle header */}
      <div className="glass-card overflow-hidden">
        <button
          id="toggle-sql-btn"
          onClick={() => setExpanded(e => !e)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.03] transition-colors duration-150"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2">
            <Code2 size={15} className="text-indigo-400" />
            <span className="text-sm font-semibold text-slate-200">Generated SQL</span>
            {retriesUsed > 0 && (
              <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/20 rounded-full px-2 py-0.5">
                {retriesUsed} retry
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">{expanded ? 'Hide' : 'Show'}</span>
            {expanded
              ? <ChevronUp size={15} className="text-slate-500" />
              : <ChevronDown size={15} className="text-slate-500" />
            }
          </div>
        </button>

        {expanded && (
          <div className="border-t border-slate-700/50">
            {/* Copy button */}
            <div className="flex justify-end px-4 pt-3">
              <button
                id="copy-sql-btn"
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-sky-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md px-3 py-1.5 transition-all duration-150"
              >
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                {copied ? 'Copied!' : 'Copy SQL'}
              </button>
            </div>
            {/* Code block */}
            <div className="p-4">
              <pre className="code-block" id="sql-code-block">
                <SQLHighlight sql={sql} />
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* Very lightweight keyword highlighter — no external dep needed */
const KEYWORDS = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|AND|OR|NOT|IN|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|NULL|IS|BETWEEN|LIKE|ASC|DESC|BY)\b/gi

function SQLHighlight({ sql }) {
  if (!sql) return null

  const parts = sql.split(KEYWORDS)
  const matches = sql.match(KEYWORDS) || []

  const result = []
  parts.forEach((part, i) => {
    result.push(<span key={`p${i}`} className="text-slate-300">{part}</span>)
    if (matches[i]) {
      result.push(
        <span key={`k${i}`} className="text-sky-300 font-semibold">
          {matches[i]}
        </span>
      )
    }
  })

  return <>{result}</>
}
