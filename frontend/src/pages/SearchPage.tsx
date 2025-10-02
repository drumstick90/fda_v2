import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Calendar, Building, Pill, Route } from 'lucide-react'
import { fdaApi } from '../services/api'
import { DrugResult } from '../types'

export function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedDrug, setSelectedDrug] = useState<DrugResult | null>(null)

  // Search query
  const { data: drugResult, isLoading, error } = useQuery({
    queryKey: ['drug-search', searchTerm],
    queryFn: () => fdaApi.searchDrug(searchTerm),
    enabled: searchTerm.length > 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchTerm.trim() && drugResult) {
      setSelectedDrug(drugResult)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Search className="w-8 h-8 text-primary-600" />
          <span>Drug Search</span>
        </h1>
        <p className="mt-2 text-gray-600">
          Search for individual drugs to get detailed FDA information
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
                placeholder="Enter drug name (e.g., risperidone, haloperidol)"
                className="input-field flex-1"
              />
              <button
                type="submit"
                disabled={isLoading || searchTerm.length < 3}
                className="btn-primary px-6"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Search Status */}
        {searchTerm.length > 2 && (
          <div className="mt-4">
            {isLoading && (
              <div className="flex items-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Searching FDA database...</span>
              </div>
            )}
            
            {error && (
              <div className="text-red-600">
                Error searching for drug. Please try again.
              </div>
            )}
            
            {drugResult && !isLoading && (
              <div className="text-green-600">
                ✓ Found drug information for "{searchTerm}"
              </div>
            )}
          </div>
        )}
      </div>

      {/* Drug Details */}
      {drugResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 capitalize">{drugResult.drug}</h2>
              {drugResult.generic_name && (
                <p className="text-gray-600 mt-1">Generic: {drugResult.generic_name}</p>
              )}
            </div>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Last Updated: {drugResult.last_updated}
            </span>
          </div>

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
                    {drugResult.indications_and_usage}
                  </p>
                </div>
              </div>

              {/* Concise Indications List */}
              {drugResult.indications && drugResult.indications.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Indications</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-800">
                    {drugResult.indications.slice(0, 6).map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {drugResult.brand_names && drugResult.brand_names.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Brand Names</h3>
                  <div className="flex flex-wrap gap-2">
                    {drugResult.brand_names.map((brand, index) => (
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
              {drugResult.manufacturer && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                    <Building className="w-5 h-5 text-primary-600" />
                    <span>Manufacturer</span>
                  </h3>
                  <p className="text-gray-800">{drugResult.manufacturer}</p>
                </div>
              )}

              {drugResult.route && drugResult.route.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                    <Route className="w-5 h-5 text-primary-600" />
                    <span>Route of Administration</span>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {drugResult.route.map((route, index) => (
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

              {drugResult.dosage_form && drugResult.dosage_form.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Dosage Forms</h3>
                  <div className="flex flex-wrap gap-2">
                    {drugResult.dosage_form.map((form, index) => (
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

              {drugResult.strength && drugResult.strength.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Strengths</h3>
                  <div className="space-y-1">
                    {drugResult.strength.slice(0, 5).map((strength, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {strength}
                      </div>
                    ))}
                    {drugResult.strength.length > 5 && (
                      <div className="text-sm text-gray-500">
                        +{drugResult.strength.length - 5} more...
                      </div>
                    )}
                  </div>
                </div>
              )}

              {drugResult.application_number && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Application Number</h3>
                  <p className="text-gray-800 font-mono text-sm">{drugResult.application_number}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!drugResult && !isLoading && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Enter a drug name above to search FDA database</p>
          <p className="text-sm mt-2">Try: risperidone, haloperidol, fluoxetine</p>
        </div>
      )}
    </div>
  )
}