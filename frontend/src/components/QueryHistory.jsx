import { Clock, CheckCircle, XCircle, Trash2, RotateCcw } from 'lucide-react'

export default function QueryHistory({ history, onRerun, onClear }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={15} className="text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">History</h2>
        </div>
        <div className="text-center py-6">
          <Clock size={28} className="text-slate-700 mx-auto mb-2" />
          <p className="text-slate-600 text-xs">No queries yet</p>
          <p className="text-slate-700 text-xs mt-0.5">Your session history will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={15} className="text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">History</h2>
          <span className="bg-slate-700 text-slate-400 text-xs font-mono rounded-full px-2 py-0.5">
            {history.length}
          </span>
        </div>
        <button
          id="clear-history-btn"
          onClick={onClear}
          className="text-slate-600 hover:text-red-400 transition-colors p-1 rounded"
          title="Clear history"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* List */}
      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {[...history].reverse().map((item, i) => (
          <div
            key={item.id}
            className="group relative bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-lg p-3 transition-all duration-150 cursor-pointer"
            onClick={() => onRerun(item.question)}
            id={`history-item-${item.id}`}
          >
            {/* Status badge */}
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-1.5">
                {item.success
                  ? <CheckCircle size={12} className="text-emerald-400 shrink-0" />
                  : <XCircle size={12} className="text-red-400 shrink-0" />
                }
                <span className={`text-xs font-medium ${item.success ? 'text-emerald-400' : 'text-red-400'}`}>
                  {item.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <span className="text-xs text-slate-600 font-mono shrink-0">{item.timestamp}</span>
            </div>

            {/* Question text */}
            <p className="text-xs text-slate-400 group-hover:text-slate-300 leading-relaxed line-clamp-2 transition-colors">
              {item.question}
            </p>

            {/* Row count if success */}
            {item.success && item.rowCount !== undefined && (
              <p className="text-xs text-slate-600 mt-1">
                {item.rowCount} row{item.rowCount !== 1 ? 's' : ''}
              </p>
            )}

            {/* Rerun icon on hover */}
            <div className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <RotateCcw size={12} className="text-sky-400" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
