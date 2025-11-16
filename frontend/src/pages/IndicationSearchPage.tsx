import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ArrowRight, Calendar, Pill } from 'lucide-react'

type DrugSummary = {
  drug_name: string
  total_labels: number
  active_count: number
  likely_active_count: number
  outdated_count: number
  latest_date: string
  brand_names: string[]
  has_monotherapy: boolean
  has_adjunctive: boolean
}

type SearchResult = {
  indication: string
  total_labels: number
  total_drugs: number
  drugs: DrugSummary[]
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  try {
    const year = parseInt(dateString.substring(0, 4))
    const month = parseInt(dateString.substring(4, 6)) - 1
    const day = parseInt(dateString.substring(6, 8))
    const date = new Date(year, month, day)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch (e) {
    return dateString
  }
}

function DrugCard({ drug, onClick }: { drug: DrugSummary; onClick: () => void }) {
  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <h3 className="text-lg font-semibold text-gray-900 capitalize mb-1">
        {drug.drug_name}
      </h3>

      {drug.brand_names.length > 0 && (
        <p className="text-sm text-gray-600 mb-3">
          {drug.brand_names.slice(0, 2).join(', ')}
          {drug.brand_names.length > 2 && ` +${drug.brand_names.length - 2} more`}
        </p>
      )}

      <div className="space-y-2 text-sm mb-4">
        <div className="flex justify-between">
          <span className="text-gray-600">Total labels:</span>
          <span className="font-medium">{drug.total_labels}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-green-600">Active:</span>
          <span className="font-medium text-green-700">{drug.active_count}</span>
        </div>
        {drug.likely_active_count > 0 && (
          <div className="flex justify-between">
            <span className="text-blue-600">Likely active:</span>
            <span className="font-medium text-blue-700">{drug.likely_active_count}</span>
          </div>
        )}
        <div className="flex justify-between items-center">
          <span className="text-gray-600 flex items-center space-x-1">
            <Calendar className="w-3 h-3" />
            <span>Latest:</span>
          </span>
          <span className="font-medium">{formatDate(drug.latest_date)}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {drug.has_monotherapy && (
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
            Monotherapy
          </span>
        )}
        {drug.has_adjunctive && (
          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
            Adjunctive
          </span>
        )}
      </div>

      <div className="text-primary-600 text-sm font-medium flex items-center">
        View Timeline
        <ArrowRight className="w-4 h-4 ml-1" />
      </div>
    </div>
  )
}

export function IndicationSearchPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<SearchResult | null>(null)
  const [activeOnly, setActiveOnly] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [showLogs, setShowLogs] = useState(false)
  const [sortBy, setSortBy] = useState<'date' | 'alphabetical' | 'labels'>('date')
  const logContainerRef = useRef<HTMLDivElement>(null)

  const navigate = useNavigate()

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchTerm.trim()) return

    setIsLoading(true)
    setResults(null)
    setError(null)
    setLogs([])
    setShowLogs(true)

    try {
      const params = new URLSearchParams()
      if (activeOnly) {
        params.append('active_only', 'true')
      }

      const url = `http://localhost:8000/api/indications/search/${encodeURIComponent(
        searchTerm.trim()
      )}/stream?${params.toString()}`

      const eventSource = new EventSource(url)

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'log') {
          setLogs((prev) => [...prev, data.message])
        } else if (data.type === 'result') {
          setResults(data.data)
          setIsLoading(false)
          eventSource.close()
          // Hide logs after 2 seconds
          setTimeout(() => {
            setShowLogs(false)
          }, 2000)
        } else if (data.type === 'error') {
          setError(data.message)
          setIsLoading(false)
          eventSource.close()
          setTimeout(() => {
            setShowLogs(false)
          }, 3000)
        }
      }

      eventSource.onerror = () => {
        setError('Connection error. Please try again.')
        setIsLoading(false)
        eventSource.close()
        setTimeout(() => {
          setShowLogs(false)
        }, 3000)
      }
    } catch (err) {
      console.error('Error fetching indication search:', err)
      setError('Failed to search. Please try again.')
      setIsLoading(false)
      setTimeout(() => {
        setShowLogs(false)
      }, 3000)
    }
  }

  const handleDrugClick = (drugName: string) => {
    navigate(`/label-analysis?drug=${encodeURIComponent(drugName)}`)
  }

  // Sort drugs based on selected criteria
  const sortedDrugs = results?.drugs ? [...results.drugs].sort((a, b) => {
    switch (sortBy) {
      case 'alphabetical':
        return a.drug_name.localeCompare(b.drug_name)
      case 'labels':
        return b.total_labels - a.total_labels // Descending
      case 'date':
      default:
        return b.latest_date.localeCompare(a.latest_date) // Descending (newest first)
    }
  }) : []

  const commonSearches = ['schizophrenia', 'depression', 'bipolar', 'anxiety', 'ADHD']

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Pill className="w-8 h-8 text-primary-600" />
          <span>Search by Indication</span>
        </h1>
        <p className="mt-2 text-gray-600">
          Find all drugs approved for a specific condition or indication
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Indication or Condition
            </label>
            <div className="flex space-x-2">
              <input
                id="search"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="e.g., schizophrenia, depression, bipolar disorder"
                className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Common Searches */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Common searches:</p>
            <div className="flex flex-wrap gap-2">
              {commonSearches.map((term) => (
                <button
                  key={term}
                  type="button"
                  onClick={() => setSearchTerm(term)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="active-only"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="active-only" className="text-sm text-gray-700">
              Show only drugs with active labels (last 2 years)
            </label>
          </div>
        </form>

        {/* Loading State */}
        {isLoading && (
          <div className="mt-4 flex items-center space-x-2 text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Searching FDA database...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mt-4 text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </div>
        )}
      </div>

      {/* Live Log Viewer */}
      {showLogs && logs.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden shadow-lg">
          <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
            <span className="text-sm font-mono text-gray-300">Live Search Log</span>
            {isLoading && (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-green-400"></div>
                <span className="text-xs text-green-400">Processing...</span>
              </div>
            )}
          </div>
          <div
            ref={logContainerRef}
            className="p-4 font-mono text-sm text-green-400 bg-gray-900 h-64 overflow-y-auto"
            style={{ scrollBehavior: 'smooth' }}
          >
            {logs.map((log, index) => (
              <div key={index} className="mb-1">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results Summary */}
      {results && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg p-4 border border-primary-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-gray-900">
                Found {results.total_drugs} drug{results.total_drugs !== 1 ? 's' : ''} for "
                {results.indication}"
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Across {results.total_labels} FDA label{results.total_labels !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results Grid */}
      {results && results.drugs.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Drugs</h2>
            
            {/* Sort Controls */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Sort by:</span>
              <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setSortBy('date')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    sortBy === 'date'
                      ? 'bg-white text-primary-700 font-medium shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Latest Date
                </button>
                <button
                  onClick={() => setSortBy('alphabetical')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    sortBy === 'alphabetical'
                      ? 'bg-white text-primary-700 font-medium shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  A-Z
                </button>
                <button
                  onClick={() => setSortBy('labels')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    sortBy === 'labels'
                      ? 'bg-white text-primary-700 font-medium shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  # Labels
                </button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedDrugs.map((drug) => (
              <DrugCard
                key={drug.drug_name}
                drug={drug}
                onClick={() => handleDrugClick(drug.drug_name)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!results && !isLoading && !error && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Enter an indication or condition above to search</p>
          <p className="text-sm mt-2">Try: schizophrenia, bipolar disorder, depression</p>
        </div>
      )}
    </div>
  )
}

