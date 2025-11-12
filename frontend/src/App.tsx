import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { SearchPage } from './pages/SearchPage'
import { BatchQueryPage } from './pages/BatchQueryPage'
import { ResultsPage } from './pages/ResultsPage'
import { LabelAnalysisPage } from './pages/LabelAnalysisPage'
import { IndicationSearchPage } from './pages/IndicationSearchPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/batch" element={<BatchQueryPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/label-analysis" element={<LabelAnalysisPage />} />
        <Route path="/indication-search" element={<IndicationSearchPage />} />
      </Routes>
    </Layout>
  )
}

export default App