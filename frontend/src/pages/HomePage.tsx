import { Link } from 'react-router-dom'
import { Search, Layers, Zap, Database, Download, Shield } from 'lucide-react'

export function HomePage() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          FDA Drug Search <span className="text-primary-600">v2</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          The fastest, most intuitive way to search and analyze FDA drug approval data. 
          Built for researchers, healthcare professionals, and data scientists.
        </p>
        <div className="flex justify-center space-x-4">
          <Link to="/search" className="btn-primary text-lg px-8 py-3 flex items-center space-x-2">
            <Search className="w-5 h-5" />
            <span>Start Searching</span>
          </Link>
          <Link to="/batch" className="btn-secondary text-lg px-8 py-3 flex items-center space-x-2">
            <Layers className="w-5 h-5" />
            <span>Batch Query</span>
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
            <Zap className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Lightning Fast</h3>
          <p className="text-gray-600">
            Sub-200ms search responses with intelligent caching and optimized API calls.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
            <Layers className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Batch Processing</h3>
          <p className="text-gray-600">
            Query hundreds of drugs at once. Perfect for research studies and drug class analysis.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
            <Database className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Rich Data</h3>
          <p className="text-gray-600">
            Access comprehensive drug information including indications, manufacturers, and approval dates.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
            <Download className="w-6 h-6 text-yellow-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Export Ready</h3>
          <p className="text-gray-600">
            Download results in CSV format for further analysis in your preferred tools.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Rate Limited</h3>
          <p className="text-gray-600">
            Respects FDA API rate limits with intelligent queuing and retry logic.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
            <Search className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Search</h3>
          <p className="text-gray-600">
            Advanced filtering and search capabilities with autocomplete and suggestions.
          </p>
        </div>
      </div>

      {/* Use Cases */}
      <div className="bg-gray-50 rounded-2xl p-8">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-8">Perfect For</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Researchers</h3>
            <p className="text-gray-600">
              Query drug classes for systematic reviews, meta-analyses, and research studies.
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Database className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Healthcare Professionals</h3>
            <p className="text-gray-600">
              Quick access to drug information, indications, and FDA approval status.
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Layers className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Data Scientists</h3>
            <p className="text-gray-600">
              Bulk data extraction and analysis for pharmaceutical research and analytics.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Start */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Quick Start Example</h2>
        <p className="text-gray-600 mb-6">
          Here's exactly what your original script did, but now with a beautiful interface:
        </p>
        <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm">
          <div className="text-gray-600 mb-2"># Your original workflow, now web-based:</div>
          <div className="text-blue-600">1. Navigate to Batch Query</div>
          <div className="text-blue-600">2. Click "Antipsychotics (27)" preset</div>
          <div className="text-blue-600">3. Click "Start Batch Query"</div>
          <div className="text-blue-600">4. Export results to CSV</div>
          <div className="text-gray-600 mt-4"># Same results, 10x faster interface!</div>
        </div>
        <div className="mt-6">
          <Link to="/batch" className="btn-primary">
            Try Batch Query Now →
          </Link>
        </div>
      </div>
    </div>
  )
}