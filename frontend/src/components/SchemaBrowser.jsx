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
          <Database size={15} className="text-[#C2BAA8]" />
          <h2 className="text-sm font-semibold text-[#F5F0E6] uppercase tracking-wide">Schema Browser</h2>
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
        <HelpCircle size={28} className="text-[#C2BAA8] mx-auto mb-2" />
        <p className="text-[#C2BAA8] text-xs">Schema not loaded</p>
      </div>
    )
  }

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Database size={15} className="text-[#E8B923]" />
        <h2 className="text-lg font-medium font-serif text-[#F5F0E6] tracking-tight">Schema Browser</h2>
        <span className="bg-[#E8B923] text-[#2A2620] text-[10px] font-bold rounded-full px-2 py-0.5">
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
              className="bg-[#454E5A] border border-white/[0.04] rounded-lg overflow-hidden transition-colors hover:border-[#E8B923]/20 shadow-sm"
            >
              {/* Table Title Block */}
              <button
                onClick={() => toggleTable(table.table_name)}
                className="w-full flex items-start gap-2 p-3 text-left hover:bg-white/[0.01] transition-colors"
                id={`schema-table-${table.table_name}`}
              >
                <span className="text-[#C2BAA8] mt-0.5 shrink-0">
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-[#E8B923] font-mono truncate">{table.table_name}</p>
                  <p className="text-[#C2BAA8] text-[11px] leading-relaxed mt-1 line-clamp-2">
                    {table.description}
                  </p>
                </div>
              </button>

              {/* Columns list when expanded */}
              {isExpanded && (
                <div className="bg-[#3D4550]/40 border-t border-white/[0.05] p-3 space-y-2">
                  <div className="flex items-center gap-1.5 text-[9px] text-[#C2BAA8] uppercase tracking-wider font-semibold mb-1.5">
                    <Columns size={10} className="text-[#E8B923]" />
                    <span>Columns</span>
                  </div>
                  <div className="grid gap-1.5">
                    {table.columns.map((columnName) => (
                      <div
                        key={columnName}
                        className="flex items-center justify-between text-xs bg-[#454E5A]/80 border border-white/[0.03] rounded px-2.5 py-1.5"
                      >
                        <span className="font-mono text-[#F5F0E6] text-[11px]">{columnName}</span>
                        {columnName.endsWith('_id') && (
                          <span className="text-[9px] bg-[#E8B923]/10 text-[#E8B923] border border-[#E8B923]/20 font-semibold px-1 rounded">PK/FK</span>
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
