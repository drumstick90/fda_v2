import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Search, Building, Pill, Route, Sparkles } from 'lucide-react'
import { fdaApi } from '../services/api'
import { DrugResult } from '../types'
import { DrugAutocompleteInput } from '../components/DrugAutocompleteInput'

export function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [submittedTerm, setSubmittedTerm] = useState('')
  const [aiResult, setAiResult] = useState<DrugResult | null>(null)

  // Search query
  const { data: drugResult, isLoading, error } = useQuery({
    queryKey: ['drug-search', submittedTerm],
    queryFn: () => fdaApi.searchDrug(submittedTerm),
    enabled: submittedTerm.length > 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const aiSummaryMutation = useMutation({
    mutationFn: (drugName: string) => fdaApi.searchDrug(drugName, true),
    onSuccess: (data) => {
      setAiResult(data)
    },
  })

  useEffect(() => {
    setAiResult(null)
    aiSummaryMutation.reset()
  }, [submittedTerm])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = searchTerm.trim()
    if (trimmed.length > 1) {
      setSubmittedTerm(trimmed)
    }
  }

  const displayedResult = aiResult ?? drugResult
  const hasFoundLabel = displayedResult
    && !['Not found', 'No data found'].includes(displayedResult.indications_and_usage)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 flex items-center space-x-2">
          <Search className="w-6 h-6 text-primary-600" />
          <span>Drug Search</span>
        </h1>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <form onSubmit={handleSearch} className="space-y-3">
          <div className="space-y-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700">
              Generic or brand name
            </label>
            <div className="flex flex-col gap-2 sm:flex-row">
              <DrugAutocompleteInput
                id="search"
                value={searchTerm}
                onChange={setSearchTerm}
                onSelect={(term) => setSubmittedTerm(term)}
                placeholder="e.g., risperidone, Abilify"
                className="flex-1"
              />
              <button
                type="submit"
                disabled={isLoading || searchTerm.trim().length < 2}
                className="btn-primary flex items-center justify-center gap-2 px-5"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Search className="w-4 h-4" />
                )}
                <span>Search</span>
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {['risperidone', 'Abilify', 'fluoxetine', 'cariprazine'].map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => {
                  setSearchTerm(term)
                  setSubmittedTerm(term)
                }}
                className="rounded-md bg-gray-100 px-2.5 py-1 text-sm text-gray-700 hover:bg-gray-200"
              >
                {term}
              </button>
            ))}
          </div>
        </form>

        {/* Search Status */}
        {submittedTerm && (
          <div className="mt-3">
            {isLoading && (
              <div className="flex items-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Searching OpenFDA...</span>
              </div>
            )}
            
            {error && (
              <div className="text-red-600">
                Error searching for drug. Please try again.
              </div>
            )}
            
            {displayedResult && !isLoading && (
              <div className="text-sm text-green-700">
                Found label data for "{submittedTerm}"
              </div>
            )}
          </div>
        )}
      </div>

      {/* Drug Details */}
      {displayedResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 capitalize">{displayedResult.drug}</h2>
              {displayedResult.generic_name && (
                <p className="text-gray-600 mt-1">Generic: {displayedResult.generic_name}</p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {hasFoundLabel && !displayedResult.ai_summary && (
                <button
                  type="button"
                  onClick={() => aiSummaryMutation.mutate(submittedTerm)}
                  disabled={aiSummaryMutation.isPending}
                  className="btn-secondary flex items-center space-x-2"
                >
                  {aiSummaryMutation.isPending ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  <span>{aiSummaryMutation.isPending ? 'Generating...' : 'Generate AI Summary'}</span>
                </button>
              )}
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                Last Updated: {displayedResult.last_updated}
              </span>
            </div>
          </div>

          {/* AI Summary */}
          {displayedResult.ai_summary && (
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200 mb-6">
              <h3 className="text-sm font-semibold text-purple-700 mb-2 uppercase tracking-wide">AI Summary</h3>
              <pre className="text-gray-800 leading-relaxed whitespace-pre-wrap font-mono text-sm overflow-x-auto">{displayedResult.ai_summary}</pre>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Main Information */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                  <Pill className="w-5 h-5 text-primary-600" />
                  <span>Indications and Usage</span>
                </h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-800 leading-relaxed">
                    {displayedResult.indications_and_usage}
                  </p>
                </div>
              </div>

              {/* Concise Indications List */}
              {displayedResult.indications && displayedResult.indications.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Indications</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-800">
                    {displayedResult.indications.slice(0, 6).map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {displayedResult.brand_names && displayedResult.brand_names.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Brand Names</h3>
                  <div className="flex flex-wrap gap-2">
                    {displayedResult.brand_names.map((brand, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                      >
                        {brand}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Additional Details */}
            <div className="space-y-6">
              {displayedResult.manufacturer && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                    <Building className="w-5 h-5 text-primary-600" />
                    <span>Manufacturer</span>
                  </h3>
                  <p className="text-gray-800">{displayedResult.manufacturer}</p>
                </div>
              )}

              {displayedResult.route && displayedResult.route.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                    <Route className="w-5 h-5 text-primary-600" />
                    <span>Route of Administration</span>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {displayedResult.route.map((route, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                      >
                        {route}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {displayedResult.dosage_form && displayedResult.dosage_form.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Dosage Forms</h3>
                  <div className="flex flex-wrap gap-2">
                    {displayedResult.dosage_form.map((form, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm"
                      >
                        {form}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {displayedResult.strength && displayedResult.strength.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Strengths</h3>
                  <div className="space-y-1">
                    {displayedResult.strength.slice(0, 5).map((strength, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {strength}
                      </div>
                    ))}
                    {displayedResult.strength.length > 5 && (
                      <div className="text-sm text-gray-500">
                        +{displayedResult.strength.length - 5} more...
                      </div>
                    )}
                  </div>
                </div>
              )}

              {displayedResult.application_number && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Application Number</h3>
                  <p className="text-gray-800 font-mono text-sm">{displayedResult.application_number}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!displayedResult && !isLoading && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Search for a drug to see its current FDA label information.</p>
        </div>
      )}
    </div>
  )
}
