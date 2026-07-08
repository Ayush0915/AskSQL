import { useState, useRef } from 'react'
import { Database, ChevronRight, ChevronDown, HelpCircle, Columns, Upload, FileText, Trash2, Sparkles, AlertCircle } from 'lucide-react'
import { uploadDataset, loadSampleDataset, clearDataset } from '../api'

export default function SchemaBrowser({
  schema,
  isLoading,
  sessionId,
  isDatasetLoaded,
  onDatasetLoaded,
  onDatasetCleared
}) {
  const [expandedTables, setExpandedTables] = useState({})
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }))
  }

  // Handle drag and drop events
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.csv'))
      if (files.length === 0) {
        setUploadError("Only CSV files are accepted.")
        return
      }
      setSelectedFiles(files)
      setUploadError(null)
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.csv'))
      if (files.length === 0) {
        setUploadError("Only CSV files are accepted.")
        return
      }
      setSelectedFiles(files)
      setUploadError(null)
    }
  }

  const triggerFileSelect = () => {
    fileInputRef.current.click()
  }

  // Upload handler
  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0) return
    setIsUploading(true)
    setUploadError(null)
    try {
      const data = await uploadDataset(sessionId, selectedFiles)
      if (data.status === "success") {
        // Fetch new schema to populate sidebar
        onDatasetLoaded(data.tables, data.example_questions)
      } else {
        setUploadError(data.error || "Upload failed.")
      }
    } catch (err) {
      console.error(err)
      const detail = err.response?.data?.detail || "Upload failed. Check file sizes."
      setUploadError(detail)
    } finally {
      setIsUploading(false)
    }
  }

  // Load sample dataset handler
  const handleLoadSample = async () => {
    setIsUploading(true)
    setUploadError(null)
    try {
      const data = await loadSampleDataset(sessionId)
      if (data.status === "success") {
        onDatasetLoaded(data.tables, data.example_questions)
      } else {
        setUploadError("Failed to load sample dataset.")
      }
    } catch (err) {
      console.error(err)
      setUploadError("Failed to load sample dataset from server.")
    } finally {
      setIsUploading(false)
    }
  }

  // Clear dataset handler
  const handleClear = async () => {
    setIsUploading(true)
    try {
      await clearDataset(sessionId)
      onDatasetCleared()
      setSelectedFiles([])
      setUploadError(null)
    } catch (err) {
      console.error(err)
    } finally {
      setIsUploading(false)
    }
  }

  // Loading spinner during processing
  if (isUploading || isLoading) {
    return (
      <div className="glass-card p-6 text-center py-12 space-y-4">
        <div className="relative w-12 h-12 mx-auto flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-accentPrimary/20 border-t-accentPrimary"></div>
          <Database size={18} className="absolute text-accentPrimary animate-pulse" />
        </div>
        <div>
          <p className="text-textPrimary font-semibold text-sm">Processing Schema...</p>
          <p className="text-textSecondary text-[11px] mt-1 leading-relaxed">
            Parsing CSV, running type inference, and generating descriptions with Llama 3. This can take a few seconds...
          </p>
        </div>
      </div>
    )
  }

  // 1. Initial State: Render Upload Dropzone
  if (!isDatasetLoaded) {
    return (
      <div className="glass-card p-5 space-y-5">
        <div className="flex items-center gap-2">
          <Database size={15} className="text-accentPrimary" />
          <h2 className="text-lg font-medium font-serif text-textPrimary tracking-tight">Upload Dataset</h2>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileSelect}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
            dragActive 
              ? 'border-accentPrimary bg-darkCardHover/40' 
              : 'border-borderSubtle hover:border-accentPrimary/40 hover:bg-darkCardHover/20'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
            multiple
            accept=".csv"
          />
          <Upload size={24} className="text-textSecondary mx-auto mb-3 opacity-60" />
          <p className="text-xs font-semibold text-textPrimary">Drag CSV files here</p>
          <p className="text-[10px] text-textSecondary mt-1">or click to browse from files</p>
          <p className="text-[9px] text-textSecondary/65 mt-2">Max 50MB per file · CSV format only</p>
        </div>

        {/* Selected files list */}
        {selectedFiles.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] text-textSecondary uppercase tracking-wider font-bold">Selected Files ({selectedFiles.length})</p>
            <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
              {selectedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between bg-darkCardHover border border-borderSubtle rounded px-2.5 py-1.5 text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText size={12} className="text-accentPrimary shrink-0" />
                    <span className="font-mono text-[11px] text-textPrimary truncate">{file.name}</span>
                  </div>
                  <span className="text-[10px] text-textSecondary shrink-0 ml-1">
                    {(file.size / 1024).toFixed(0)} KB
                  </span>
                </div>
              ))}
            </div>
            
            <button
              onClick={handleUploadSubmit}
              className="w-full btn-neon py-2 text-xs flex items-center justify-center gap-1.5 shadow-sm"
            >
              <Database size={13} />
              <span>Import Dataset</span>
            </button>
          </div>
        )}

        {/* Error message */}
        {uploadError && (
          <div className="bg-errorRed/10 border border-errorRed/20 text-errorRed p-3 rounded-lg flex items-start gap-2 text-xs leading-relaxed">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Quick Demo Option */}
        <div className="border-t border-borderSubtle/60 pt-4 text-center">
          <p className="text-[10px] text-textSecondary mb-2.5">No dataset of your own?</p>
          <button
            onClick={handleLoadSample}
            className="inline-flex items-center gap-1.5 text-xs text-accentPrimary hover:text-accentPrimaryHover border border-accentPrimary/25 hover:border-accentPrimary/40 rounded-full px-4 py-1.5 bg-darkCard hover:bg-darkCardHover transition-all duration-150 shadow-sm"
          >
            <Sparkles size={12} />
            <span>Try sample dataset</span>
          </button>
        </div>
      </div>
    )
  }

  // 2. Active Schema State: Render Schema Browser Tree
  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database size={15} className="text-accentPrimary" />
          <h2 className="text-lg font-medium font-serif text-textPrimary tracking-tight">Schema Browser</h2>
          <span className="bg-accentPrimary text-darkBg text-[10px] font-bold rounded-full px-2 py-0.5">
            {schema.length}
          </span>
        </div>
        <button
          onClick={handleClear}
          className="text-textSecondary hover:text-errorRed transition-colors p-1 rounded hover:bg-black/[0.03]"
          title="Clear Dataset / Start Over"
          id="clear-dataset-btn"
        >
          <Trash2 size={14} />
        </button>
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
                          <span className="text-[9px] bg-accentPrimary/10 text-accentPrimary border border-accentPrimary/30 font-bold px-1.5 py-0.5 rounded font-sans">PK/FK</span>
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
