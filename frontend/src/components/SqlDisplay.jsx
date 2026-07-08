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
    <div className="space-y-4 animate-fade-in-up">
      {/* Explanation card */}
      {explanation && (
        <div className="glass-card p-5 border-l-4 border-l-accentPrimary bg-darkCard/50">
          <div className="flex items-start gap-3">
            <div className="w-6.5 h-6.5 rounded-full bg-accentPrimary/10 border border-accentPrimary/25 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
              <span className="text-accentPrimary text-xs font-bold font-serif">?</span>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-accentPrimary uppercase tracking-wider mb-1.5 font-sans">
                Plain-English Explanation
              </p>
              <p className="text-textPrimary text-sm leading-relaxed font-sans font-normal">
                {explanation}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* SQL toggle header */}
      <div className="glass-card overflow-hidden">
        <button
          id="toggle-sql-btn"
          onClick={() => setExpanded(e => !e)}
          className="w-full flex items-center justify-between px-5 py-4 hover:bg-black/[0.015] transition-colors duration-150"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2.5">
            <Code2 size={16} className="text-accentPrimary" />
            <span className="text-sm font-semibold text-textPrimary font-sans">Generated SQL Query</span>
            {retriesUsed > 0 && (
              <span className="text-[10px] font-semibold bg-[#C1443A]/10 text-[#C1443A] border border-[#C1443A]/20 rounded-full px-2 py-0.5 uppercase tracking-wider">
                {retriesUsed} retry{retriesUsed !== 1 ? 'ies' : ''}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-textSecondary font-sans">{expanded ? 'Hide Query' : 'Show Query'}</span>
            {expanded
              ? <ChevronUp size={15} className="text-textSecondary" />
              : <ChevronDown size={15} className="text-textSecondary" />
            }
          </div>
        </button>

        {expanded && (
          <div className="border-t border-borderSubtle">
            {/* Copy button */}
            <div className="flex justify-end px-5 pt-3.5">
              <button
                id="copy-sql-btn"
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-textSecondary hover:text-accentPrimary bg-darkCard border border-borderSubtle hover:border-accentPrimary/30 rounded-md px-3 py-1.5 transition-all duration-150 shadow-sm"
              >
                {copied ? <Check size={13} className="text-[#4ADE80]" /> : <Copy size={13} />}
                {copied ? 'Copied' : 'Copy SQL'}
              </button>
            </div>
            {/* Code block - ALWAYS remains dark #1E1E2E */}
            <div className="p-5">
              <pre className="code-block font-mono text-xs rounded-lg" id="sql-code-block" style={{ background: '#1E1E2E' }}>
                <SQLHighlight sql={sql} />
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* Very lightweight keyword & string literal highlighter (optimized for dark pre container) */
const TOKEN_REGEX = /('[^']*')|\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|AND|OR|NOT|IN|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|NULL|IS|BETWEEN|LIKE|ASC|DESC|BY)\b/gi
const KEYWORDS_ONLY = /^(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|AND|OR|NOT|IN|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|NULL|IS|BETWEEN|LIKE|ASC|DESC|BY)$/i

function SQLHighlight({ sql }) {
  if (!sql) return null

  const parts = sql.split(TOKEN_REGEX)

  return (
    <>
      {parts.map((part, i) => {
        if (part === undefined || part === null || part === '') return null

        // Safe dark contrast string color (coral/red)
        if (part.startsWith("'") && part.endsWith("'")) {
          return (
            <span key={i} className="text-[#ef4444] font-medium">
              {part}
            </span>
          )
        }

        // Safe dark contrast SQL keyword color (bright gold)
        if (KEYWORDS_ONLY.test(part)) {
          return (
            <span key={i} className="text-[#E8B923] font-semibold">
              {part}
            </span>
          )
        }

        // Base code color (off-white for dark background pre container)
        return <span key={i} className="text-[#F5F0E6]">{part}</span>
      })}
    </>
  )
}
