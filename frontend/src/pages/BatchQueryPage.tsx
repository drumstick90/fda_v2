import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { Play, Download, Layers, Clock, CheckCircle, XCircle } from 'lucide-react'
import { fdaApi } from '../services/api'
import { BatchQueryRequest, BatchQueryResponse } from '../types'

interface BatchFormData {
  drugList: string
  rateLimit: number
  usePreset: string
}

export function BatchQueryPage() {
  const [results, setResults] = useState<BatchQueryResponse | null>(null)
  
  const { register, handleSubmit, setValue, watch } = useForm<BatchFormData>({
    defaultValues: {
      drugList: '',
      rateLimit: 0.3,
      usePreset: ''
    }
  })
  
  const selectedPreset = watch('usePreset')

  const batchMutation = useMutation({
    mutationFn: (data: BatchQueryRequest) => fdaApi.batchQuery(data),
    onSuccess: (data) => {
      setResults(data)
      toast.success(`Query completed! Found ${data.total_found}/${data.total_processed} drugs`)
    },
    onError: (error) => {
      toast.error('Batch query failed')
      console.error(error)
    }
  })

  const exportMutation = useMutation({
    mutationFn: () => fdaApi.exportResults(results?.results || []),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `FDA_Batch_Results_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Results exported successfully!')
    }
  })

  const onSubmit = (data: BatchFormData) => {
    const drugs = data.drugList
      .split('\n')
      .map(drug => drug.trim())
      .filter(drug => drug.length > 0)

    if (drugs.length === 0) {
      toast.error('Please enter at least one drug name')
      return
    }

    const request: BatchQueryRequest = {
      drugs,
      rate_limit_delay: data.rateLimit
    }

    batchMutation.mutate(request)
  }

  // Load preset drug list
  const loadPreset = async (category: string) => {
    try {
      const lists = await fdaApi.getDrugLists()
      const drugs = lists[category] || []
      setValue('drugList', drugs.join('\n'))
      toast.success(`Loaded ${drugs.length} ${category}`)
    } catch (error) {
      toast.error('Failed to load preset')
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Layers className="w-8 h-8 text-primary-600" />
          <span>Batch Drug Query</span>
        </h1>
        <p className="mt-2 text-gray-600">
          Query multiple drugs at once - perfect for research studies and drug class analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Configure Batch Query</h2>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Preset Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quick Start - Preset Drug Lists
              </label>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => loadPreset('antipsychotics')}
                  className="px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors"
                >
                  Antipsychotics (27)
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset('antidepressants')}
                  className="px-3 py-2 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors"
                >
                  Antidepressants (10)
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset('mood_stabilizers')}
                  className="px-3 py-2 text-sm bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100 transition-colors"
                >
                  Mood Stabilizers (5)
                </button>
              </div>
            </div>

            {/* Drug List Input */}
            <div>
              <label htmlFor="drugList" className="block text-sm font-medium text-gray-700 mb-2">
                Drug Names (one per line)
              </label>
              <textarea
                id="drugList"
                {...register('drugList', { required: 'Please enter at least one drug name' })}
                rows={12}
                className="input-field w-full resize-none font-mono text-sm"
                placeholder="Enter drug names, one per line:&#10;chlorpromazine&#10;haloperidol&#10;risperidone&#10;..."
              />
            </div>

            {/* Rate Limit */}
            <div>
              <label htmlFor="rateLimit" className="block text-sm font-medium text-gray-700 mb-2">
                Rate Limit Delay (seconds)
              </label>
              <input
                id="rateLimit"
                type="number"
                step="0.1"
                min="0.1"
                max="5"
                {...register('rateLimit', { 
                  required: 'Rate limit is required',
                  min: { value: 0.1, message: 'Minimum 0.1 seconds' },
                  max: { value: 5, message: 'Maximum 5 seconds' }
                })}
                className="input-field w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Delay between API calls to respect FDA rate limits
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={batchMutation.isPending}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              {batchMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Start Batch Query</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Results</h2>
            {results && (
              <button
                onClick={() => exportMutation.mutate()}
                disabled={exportMutation.isPending}
                className="btn-secondary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export CSV</span>
              </button>
            )}
          </div>

          {!results && (
            <div className="text-center py-12 text-gray-500">
              <Layers className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Run a batch query to see results here</p>
            </div>
          )}

          {results && (
            <div className="space-y-4">
              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{results.total_processed}</div>
                  <div className="text-sm text-blue-600">Processed</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{results.total_found}</div>
                  <div className="text-sm text-green-600">Found</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{results.errors.length}</div>
                  <div className="text-sm text-red-600">Errors</div>
                </div>
              </div>

              {/* Execution Time */}
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>Completed in {results.execution_time.toFixed(1)} seconds</span>
              </div>

              {/* Results List */}
              <div className="max-h-96 overflow-y-auto space-y-2">
                {results.results.map((result, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{result.drug}</span>
                      {result.indications_and_usage !== 'Not found' && result.indications_and_usage !== 'No data found' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {result.indications_and_usage}
                    </p>
                    {result.last_updated !== 'N/A' && (
                      <p className="text-xs text-gray-400 mt-1">
                        Updated: {result.last_updated}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}