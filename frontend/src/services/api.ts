import axios from 'axios'
import { DrugResult, BatchQueryRequest, BatchQueryResponse } from '../types'

// Use same-origin by default so Vite dev proxy can forward '/api' to backend
const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const buildApiUrl = (path: string): string => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return API_BASE_URL ? `${API_BASE_URL}${normalizedPath}` : normalizedPath
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const fdaApi = {
  // Single drug search
  searchDrug: async (drugName: string, includeAi = false): Promise<DrugResult> => {
    const response = await api.get(`/api/drugs/search/${encodeURIComponent(drugName)}`, {
      params: includeAi ? { include_ai: true } : undefined,
    })
    return response.data
  },

  analyzeLabels: async (drugName: string) => {
    const response = await api.get(`/api/drugs/analyze-labels/${encodeURIComponent(drugName)}`)
    return response.data
  },

  // Batch query multiple drugs (like your antipsychotic example)
  batchQuery: async (request: BatchQueryRequest): Promise<BatchQueryResponse> => {
    const response = await api.post('/api/drugs/batch', request)
    return response.data
  },

  // Export results to CSV
  exportResults: async (results: DrugResult[], filename?: string): Promise<Blob> => {
    const response = await api.post('/api/export/csv', 
      { results, filename }, 
      { responseType: 'blob' }
    )
    return response.data
  },

  // Get predefined drug lists (antipsychotics, antidepressants, etc.)
  getDrugLists: async (): Promise<{ [category: string]: string[] }> => {
    const response = await api.get('/api/drugs/lists')
    return response.data
  },

  getIndicationSearchStreamUrl: (indication: string, activeOnly: boolean): string => {
    const params = new URLSearchParams()
    if (activeOnly) {
      params.append('active_only', 'true')
    }

    const query = params.toString()
    const path = `/api/indications/search/${encodeURIComponent(indication)}/stream${query ? `?${query}` : ''}`
    return buildApiUrl(path)
  },
}

export default api
