import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Calendar, FileText, TrendingUp } from 'lucide-react'
import { fdaApi } from '../services/api'

type LabelStatus = 'active' | 'likely_active' | 'outdated' | 'unknown'

type Label = {
  effective_time: string
  version: number
  set_id: string
  brand_name: string
  manufacturer: string
  status: LabelStatus
  indications_text: string
}

type UniqueIndication = {
  text: string
  latest_date: string
}

type AnalysisResult = {
  drug_name: string
  total_labels: number
  active_count: number
  likely_active_count: number
  outdated_count: number
  unknown_count: number
  unique_indications: UniqueIndication[]
  labels: Label[]
}

export function LabelAnalysisPage() {
  const [searchParams] = useSearchParams()
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Auto-search if drug param is in URL
  useEffect(() => {
    const drugParam = searchParams.get('drug')
    if (drugParam) {
      setSearchTerm(drugParam)
      performSearch(drugParam)
    }
  }, [searchParams])

  const performSearch = async (drug: string) => {
    if (!drug.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const data = await fdaApi.analyzeLabels(drug.trim())
      setAnalysisResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze labels')
      setAnalysisResult(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    await performSearch(searchTerm)
  }

  const getStatusColor = (status: LabelStatus) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'likely_active': return 'bg-blue-500'
      case 'outdated': return 'bg-gray-400'
      default: return 'bg-gray-300'
    }
  }

  const parseEffectiveDate = (dateStr: string): Date | null => {
    if (!dateStr || dateStr.length !== 8) return null
    const year = parseInt(dateStr.substring(0, 4))
    const month = parseInt(dateStr.substring(4, 6)) - 1
    const day = parseInt(dateStr.substring(6, 8))
    return new Date(year, month, day)
  }

  const formatDate = (dateStr: string): string => {
    const date = parseEffectiveDate(dateStr)
    if (!date) return dateStr
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <TrendingUp className="w-8 h-8 text-primary-600" />
          <span>Label Analysis Dashboard</span>
        </h1>
        <p className="mt-2 text-gray-600">
          Analyze all FDA labels for a medication - view timeline, status distribution, and unique indications
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Drug Name
            </label>
            <div className="flex space-x-2">
              <input
                id="search"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="e.g., risperidone, aripiprazole"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Search className="w-4 h-4" />
                )}
                <span>{isLoading ? 'Analyzing...' : 'Analyze'}</span>
              </button>
            </div>
          </div>
        </form>

        {error && (
          <div className="mt-4 text-red-600">
            Error: {error}
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Total Labels</div>
              <div className="text-3xl font-bold text-gray-900">{analysisResult.total_labels}</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border border-green-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Active</div>
              <div className="text-3xl font-bold text-green-600">{analysisResult.active_count}</div>
              <div className="text-xs text-gray-500 mt-1">
                {Math.round((analysisResult.active_count / analysisResult.total_labels) * 100)}%
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border border-blue-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Likely Active</div>
              <div className="text-3xl font-bold text-blue-600">{analysisResult.likely_active_count}</div>
              <div className="text-xs text-gray-500 mt-1">
                {Math.round((analysisResult.likely_active_count / analysisResult.total_labels) * 100)}%
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Outdated</div>
              <div className="text-3xl font-bold text-gray-600">{analysisResult.outdated_count}</div>
              <div className="text-xs text-gray-500 mt-1">
                {Math.round((analysisResult.outdated_count / analysisResult.total_labels) * 100)}%
              </div>
            </div>
          </div>

          {/* Timeline Chart */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-primary-600" />
              <span>Label Timeline (by Effective Date)</span>
            </h2>
            
            <div className="relative h-32 border-l-2 border-b-2 border-gray-300">
              {/* Timeline visualization */}
              {(() => {
                const sortedLabels = [...analysisResult.labels].sort((a, b) => 
                  a.effective_time.localeCompare(b.effective_time)
                )
                
                const minDate = parseEffectiveDate(sortedLabels[0]?.effective_time)
                const maxDate = parseEffectiveDate(sortedLabels[sortedLabels.length - 1]?.effective_time)
                
                if (!minDate || !maxDate) return null
                
                const timeRange = maxDate.getTime() - minDate.getTime()
                
                return (
                  <>
                    {sortedLabels.map((label, idx) => {
                      const labelDate = parseEffectiveDate(label.effective_time)
                      if (!labelDate) return null
                      
                      const position = ((labelDate.getTime() - minDate.getTime()) / timeRange) * 100
                      
                      return (
                        <div
                          key={idx}
                          className="absolute bottom-0 transform -translate-x-1/2 group"
                          style={{ left: `${position}%` }}
                          title={`${label.brand_name} - ${formatDate(label.effective_time)} (v${label.version})`}
                        >
                          <div className={`w-3 h-3 rounded-full ${getStatusColor(label.status)} cursor-pointer hover:scale-150 transition-transform`}></div>
                          <div className="hidden group-hover:block absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                            {label.brand_name}<br/>
                            {formatDate(label.effective_time)}<br/>
                            v{label.version} - {label.status}
                          </div>
                        </div>
                      )
                    })}
                    
                    {/* X-axis labels */}
                    <div className="absolute -bottom-6 left-0 text-xs text-gray-600">
                      {formatDate(sortedLabels[0].effective_time)}
                    </div>
                    <div className="absolute -bottom-6 right-0 text-xs text-gray-600">
                      {formatDate(sortedLabels[sortedLabels.length - 1].effective_time)}
                    </div>
                  </>
                )
              })()}
            </div>
            
            {/* Legend */}
            <div className="mt-8 flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-gray-700">Active</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-gray-700">Likely Active</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                <span className="text-gray-700">Outdated</span>
              </div>
            </div>
          </div>

          {/* Unique Indications */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary-600" />
              <span>Unique Indications ({analysisResult.unique_indications.length})</span>
            </h2>
            
            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <div className="max-h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {analysisResult.unique_indications.map((indication, idx) => (
                  <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-500 mb-2 flex items-center space-x-3">
                      <span>Indication #{idx + 1}</span>
                      <span>•</span>
                      <span>{indication.text.length} chars</span>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(indication.latest_date)}</span>
                      </span>
                    </div>
                    <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
                      {indication.text}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysisResult && !isLoading && !error && (
        <div className="text-center py-12 text-gray-500">
          <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Enter a drug name above to analyze all FDA labels</p>
          <p className="text-sm mt-2">Try: risperidone, aripiprazole, haloperidol</p>
        </div>
      )}
    </div>
  )
}
