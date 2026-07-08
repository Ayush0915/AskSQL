import { useState } from 'react'
import { Table, ChevronUp, ChevronDown, ChevronsUpDown, Download } from 'lucide-react'

export default function ResultsTable({ results }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  if (!results || results.length === 0) {
    return (
      <div className="glass-card p-8 text-center animate-fade-in-up">
        <Table size={36} className="text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400 font-medium">Query returned no rows</p>
        <p className="text-slate-600 text-sm mt-1">Try a broader question or check the schema browser.</p>
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
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Table size={16} className="text-sky-400" />
          <span className="text-sm font-semibold text-slate-200">Results</span>
          <span className="bg-sky-500/20 text-sky-300 text-xs font-mono px-2 py-0.5 rounded-full">
            {results.length} row{results.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          id="download-csv-btn"
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-sky-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-sky-500/30 rounded-md px-3 py-1.5 transition-all duration-150"
        >
          <Download size={13} />
          CSV
        </button>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
          <table className="w-full text-sm" id="results-table">
            <thead className="sticky top-0 z-10">
              <tr className="bg-slate-900/90 backdrop-blur border-b border-slate-700/60">
                {columns.map(col => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left font-semibold text-slate-300 whitespace-nowrap cursor-pointer select-none hover:text-sky-300 group"
                    onClick={() => handleSort(col)}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{col}</span>
                      <span className="text-slate-600 group-hover:text-sky-400 transition-colors">
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
                  className={`border-b border-slate-800/50 transition-colors duration-100 ${
                    i % 2 === 0 ? 'bg-slate-900/20' : 'bg-slate-800/10'
                  } hover:bg-sky-500/5`}
                >
                  {columns.map(col => (
                    <td key={col} className="px-4 py-2.5 text-slate-300 whitespace-nowrap font-mono text-xs">
                      {row[col] === null || row[col] === undefined
                        ? <span className="text-slate-600 italic">null</span>
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
