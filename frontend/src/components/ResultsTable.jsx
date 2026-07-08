import { useState } from 'react'
import { Table, ChevronUp, ChevronDown, ChevronsUpDown, Download } from 'lucide-react'

export default function ResultsTable({ results }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  if (!results || results.length === 0) {
    return (
      <div className="glass-card p-8 text-center animate-fade-in-up">
        <Table size={36} className="text-textSecondary mx-auto mb-3 opacity-40" />
        <p className="text-textPrimary font-medium font-serif text-lg">Query returned no rows</p>
        <p className="text-textSecondary text-xs mt-1.5 font-sans">
          Try a broader question or check the schema browser.
        </p>
      </div>
    )
  }

  const columns = Object.keys(results[0])

  const handleSort = (col) => {
    if (sortKey === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(col)
      setSortDir('asc')
    }
  }

  const sorted = [...results].sort((a, b) => {
    if (!sortKey) return 0
    const av = a[sortKey]
    const bv = b[sortKey]
    if (av === null || av === undefined) return 1
    if (bv === null || bv === undefined) return -1
    const cmp = typeof av === 'number' && typeof bv === 'number'
      ? av - bv
      : String(av).localeCompare(String(bv), undefined, { numeric: true })
    return sortDir === 'asc' ? cmp : -cmp
  })

  const handleDownloadCSV = () => {
    const header = columns.join(',')
    const rows = sorted.map(row =>
      columns.map(col => {
        const val = row[col]
        if (val === null || val === undefined) return ''
        const str = String(val)
        return str.includes(',') || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"`
          : str
      }).join(',')
    )
    const csv = [header, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'asksql_results.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="animate-fade-in-up">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2">
          <Table size={16} className="text-accentPrimary" />
          <span className="text-lg font-medium font-serif text-textPrimary tracking-tight">Results</span>
          <span className="bg-accentPrimary text-darkBg text-[10px] font-bold px-2 py-0.5 rounded-full">
            {results.length} row{results.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          id="download-csv-btn"
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 text-xs text-textSecondary hover:text-accentPrimary bg-darkCard hover:bg-darkCardHover border border-borderSubtle hover:border-accentPrimary/35 rounded-md px-3.5 py-1.5 transition-all duration-150 shadow-sm"
        >
          <Download size={13} />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
          <table className="w-full text-sm" id="results-table">
            <thead className="sticky top-0 z-10">
              <tr className="bg-darkCardHover border-b border-borderSubtle">
                {columns.map(col => (
                  <th
                    key={col}
                    className="px-4 py-3.5 text-left font-semibold text-textSecondary whitespace-nowrap cursor-pointer select-none hover:text-accentPrimary group text-xs uppercase tracking-wider border-b border-borderSubtle"
                    onClick={() => handleSort(col)}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{col}</span>
                      <span className="text-textSecondary/50 group-hover:text-accentPrimary transition-colors">
                        {sortKey === col
                          ? sortDir === 'asc'
                            ? <ChevronUp size={13} />
                            : <ChevronDown size={13} />
                          : <ChevronsUpDown size={13} />
                        }
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => (
                <tr
                  key={i}
                  className={`border-b border-borderSubtle/40 transition-colors duration-100 ${
                    i % 2 === 0 ? 'bg-transparent' : 'bg-darkBg'
                  } hover:bg-accentPrimary/5`}
                >
                  {columns.map(col => (
                    <td key={col} className="px-4 py-2.5 text-textPrimary whitespace-nowrap font-mono text-[11px]">
                      {row[col] === null || row[col] === undefined
                        ? <span className="text-textSecondary/45 italic">null</span>
                        : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
