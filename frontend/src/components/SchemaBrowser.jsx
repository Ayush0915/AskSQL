import { useState } from 'react'
import { Database, ChevronRight, ChevronDown, HelpCircle, Columns } from 'lucide-react'

export default function SchemaBrowser({ schema, isLoading }) {
  const [expandedTables, setExpandedTables] = useState({})

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }))
  }

  if (isLoading) {
    return (
      <div className="glass-card p-4">
        <div className="flex items-center gap-2 mb-4">
          <Database size={15} className="text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Schema Browser</h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton h-10 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (!schema || schema.length === 0) {
    return (
      <div className="glass-card p-4 text-center py-8">
        <HelpCircle size={28} className="text-slate-700 mx-auto mb-2" />
        <p className="text-slate-500 text-xs">Schema not loaded</p>
      </div>
    )
  }

  return (
    <div className="glass-card p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Database size={15} className="text-slate-400" />
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Schema Browser</h2>
        <span className="bg-slate-700 text-slate-400 text-xs font-mono rounded-full px-2 py-0.5">
          {schema.length}
        </span>
      </div>

      {/* Tables list */}
      <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
        {schema.map((table) => {
          const isExpanded = !!expandedTables[table.table_name]
          return (
            <div
              key={table.table_name}
              className="bg-slate-900/40 border border-slate-800/80 rounded-lg overflow-hidden transition-colors hover:border-slate-700/60"
            >
              {/* Table Title Block */}
              <button
                onClick={() => toggleTable(table.table_name)}
                className="w-full flex items-start gap-2.5 p-3 text-left hover:bg-white/[0.01] transition-colors"
                id={`schema-table-${table.table_name}`}
              >
                <span className="text-slate-500 mt-0.5">
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-indigo-300 font-mono truncate">{table.table_name}</p>
                  <p className="text-slate-500 text-[11px] leading-snug mt-1 line-clamp-2">
                    {table.description}
                  </p>
                </div>
              </button>

              {/* Columns list when expanded */}
              {isExpanded && (
                <div className="bg-slate-950/40 border-t border-slate-800/60 p-3 space-y-2">
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1">
                    <Columns size={10} />
                    <span>Columns</span>
                  </div>
                  <div className="grid gap-1.5">
                    {table.columns.map((columnName) => (
                      <div
                        key={columnName}
                        className="flex items-center justify-between text-xs bg-slate-900/60 border border-slate-800/60 rounded px-2 py-1"
                      >
                        <span className="font-mono text-slate-300">{columnName}</span>
                        {columnName.endsWith('_id') && (
                          <span className="text-[9px] bg-sky-500/10 text-sky-400 font-semibold px-1 rounded">PK/FK</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
