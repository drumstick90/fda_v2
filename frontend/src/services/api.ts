import axios from 'axios'
import { DrugResult, BatchQueryRequest, BatchQueryResponse, SearchFilters, ApiResponse } from '../types'

// Use same-origin by default so Vite dev proxy can forward '/api' to backend
const API_BASE_URL = typeof import.meta.env.VITE_API_URL !== 'undefined' ? import.meta.env.VITE_API_URL : ''

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
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
  searchDrug: async (drugName: string): Promise<DrugResult> => {
    const response = await api.get(`/api/drugs/search/${encodeURIComponent(drugName)}`)
    return response.data
  },

  // Advanced search with filters
  searchDrugs: async (filters: SearchFilters, page = 1, limit = 20): Promise<ApiResponse<DrugResult[]>> => {
    const response = await api.post(`/api/drugs/search?page=${page}&limit=${limit}`, filters)
    return response.data
  },

  // Batch query multiple drugs (like your antipsychotic example)
  batchQuery: async (request: BatchQueryRequest): Promise<BatchQueryResponse> => {
    const response = await api.post('/api/drugs/batch', request)
    return response.data
  },

  // Get drug suggestions for autocomplete
  getSuggestions: async (query: string): Promise<string[]> => {
    const response = await api.get(`/api/drugs/suggest?q=${encodeURIComponent(query)}`)
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
  }
}

export default api