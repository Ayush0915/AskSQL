import { Clock, CheckCircle, XCircle, Trash2, RotateCcw } from 'lucide-react'

export default function QueryHistory({ history, onRerun, onClear }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={15} className="text-textSecondary" />
          <h2 className="text-lg font-medium font-serif text-textPrimary tracking-tight">History</h2>
        </div>
        <div className="text-center py-6">
          <Clock size={28} className="text-textSecondary mx-auto mb-2 opacity-35" />
          <p className="text-textSecondary text-xs">No queries yet</p>
          <p className="text-textSecondary/50 text-[11px] mt-0.5">Your session history will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={15} className="text-accentPrimary" />
          <h2 className="text-lg font-medium font-serif text-textPrimary tracking-tight">History</h2>
          <span className="bg-darkCard text-textSecondary border border-borderSubtle text-[10px] font-mono rounded-full px-2 py-0.5">
            {history.length}
          </span>
        </div>
        <button
          id="clear-history-btn"
          onClick={onClear}
          className="text-textSecondary hover:text-accentSecondary transition-colors p-1 rounded"
          title="Clear history"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* List */}
      <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {[...history].reverse().map((item, i) => (
          <div
            key={item.id}
            className="group relative bg-darkCard hover:bg-darkCardHover border border-borderSubtle hover:border-accentPrimary/35 rounded-lg p-3.5 transition-all duration-150 cursor-pointer shadow-sm"
            onClick={() => onRerun(item.question)}
            id={`history-item-${item.id}`}
          >
            {/* Status badge */}
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-1.5">
                {item.success
                  ? <CheckCircle size={12} className="text-[#4ADE80] shrink-0" />
                  : <XCircle size={12} className="text-[#C1443A] shrink-0" />
                }
                <span className={`text-[10px] font-bold uppercase tracking-wider ${item.success ? 'text-[#4ADE80]' : 'text-[#C1443A]'}`}>
                  {item.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <span className="text-[10px] text-textSecondary/70 font-mono shrink-0">{item.timestamp}</span>
            </div>

            {/* Question text */}
            <p className="text-xs text-textSecondary group-hover:text-textPrimary leading-relaxed line-clamp-2 transition-colors">
              {item.question}
            </p>

            {/* Row count if success */}
            {item.success && item.rowCount !== undefined && (
              <p className="text-[10px] text-textSecondary/80 font-medium mt-1.5 font-sans">
                {item.rowCount} row{item.rowCount !== 1 ? 's' : ''} returned
              </p>
            )}

            {/* Rerun icon on hover */}
            <div className="absolute top-3.5 right-3.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <RotateCcw size={12} className="text-accentPrimary" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
