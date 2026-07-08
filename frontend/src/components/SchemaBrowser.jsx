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
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Database size={15} className="text-textSecondary" />
          <h2 className="text-sm font-semibold text-textPrimary uppercase tracking-wide">Schema Browser</h2>
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
      <div className="glass-card p-5 text-center py-8">
        <HelpCircle size={28} className="text-textSecondary mx-auto mb-2 opacity-50" />
        <p className="text-textSecondary text-xs">Schema not loaded</p>
      </div>
    )
  }

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Database size={15} className="text-accentPrimary" />
        <h2 className="text-lg font-medium font-serif text-textPrimary tracking-tight">Schema Browser</h2>
        <span className="bg-accentPrimary text-darkBg text-[10px] font-bold rounded-full px-2 py-0.5">
          {schema.length}
        </span>
      </div>

      {/* Tables list */}
      <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
        {schema.map((table) => {
          const isExpanded = !!expandedTables[table.table_name]
          return (
            <div
              key={table.table_name}
              className="bg-darkCard border border-borderSubtle rounded-lg overflow-hidden transition-colors hover:border-accentPrimary/35 shadow-sm"
            >
              {/* Table Title Block */}
              <button
                onClick={() => toggleTable(table.table_name)}
                className="w-full flex items-start gap-2 p-3 text-left hover:bg-black/[0.02] transition-colors"
                id={`schema-table-${table.table_name}`}
              >
                <span className="text-textSecondary mt-0.5 shrink-0">
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-accentPrimary font-mono truncate">{table.table_name}</p>
                  <p className="text-textSecondary text-[11px] leading-relaxed mt-1 line-clamp-2">
                    {table.description}
                  </p>
                </div>
              </button>

              {/* Columns list when expanded */}
              {isExpanded && (
                <div className="bg-darkBg border-t border-borderSubtle p-3 space-y-2">
                  <div className="flex items-center gap-1.5 text-[9px] text-textSecondary uppercase tracking-wider font-semibold mb-1.5">
                    <Columns size={10} className="text-accentPrimary" />
                    <span>Columns</span>
                  </div>
                  <div className="grid gap-1.5">
                    {table.columns.map((columnName) => (
                      <div
                        key={columnName}
                        className="flex items-center justify-between text-xs bg-darkCard border border-borderSubtle rounded px-2.5 py-1.5"
                      >
                        <span className="font-mono text-textPrimary text-[11px]">{columnName}</span>
                        {columnName.endsWith('_id') && (
                          <span className="text-[9px] bg-accentPrimary/10 text-accentPrimary border border-accentPrimary/30 font-bold px-1.5 py-0.5 rounded">PK/FK</span>
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
