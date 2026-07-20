import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Calendar, FileText, TrendingUp, Sparkles } from 'lucide-react'
import { fdaApi } from '../services/api'
import { DrugAutocompleteInput } from '../components/DrugAutocompleteInput'

type Label = {
  effective_time: string
  year: string
  version: number | string
  set_id: string
  brand_name: string
  manufacturer: string
  generic_name?: string
  application_number?: string
  route: string[]
  dosage_form: string[]
  product_type?: string
  product_ndc: string[]
  formulation: string
  indications_text: string
}

type UniqueIndication = {
  text: string
  first_date: string
  latest_date: string
  label_count: number
}

type AnalysisResult = {
  drug_name: string
  total_labels: number
  labels_with_indications: number
  formulation_count: number
  version_count: number
  unique_indications: UniqueIndication[]
  labels: Label[]
}

type ExtractedIndication = {
  indication: string
  condition?: string
  episode_or_phase?: string | null
  treatment_mode?: string
  population?: string | null
  first_appearance_year?: string | null
  first_appearance_effective_time?: string | null
  still_present_in_latest?: boolean
  latest_presence_effective_time?: string | null
  guardrail_check?: string
  formulations?: Array<{
    formulation?: string
    route?: string[]
    dosage_form?: string[]
    brand_names?: string[]
    application_numbers?: string[]
    versions_seen?: string[]
  }>
}

type ExtractionResult = {
  drug_name: string
  latest_effective_time: string
  indications: ExtractedIndication[]
  latest_label_coverage?: {
    latest_effective_time: string
    latest_label_count: number
    latest_formulations: string[]
  }
  warnings?: string[]
  payload_label_count?: number
}

type ExtractedFormulation = NonNullable<ExtractedIndication['formulations']>[number]

const timelineColors = [
  'bg-sky-500',
  'bg-emerald-500',
  'bg-violet-500',
  'bg-amber-500',
  'bg-rose-500',
  'bg-cyan-600',
  'bg-lime-600',
  'bg-fuchsia-500',
]

export function LabelAnalysisPage() {
  const [searchParams] = useSearchParams()
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const [showApiKeyInput, setShowApiKeyInput] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [extractionGroupMode, setExtractionGroupMode] = useState<'formulation' | 'indication'>('formulation')
  const [error, setError] = useState<string | null>(null)
  const [extractionError, setExtractionError] = useState<string | null>(null)

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
    setExtractionError(null)
    setExtractionResult(null)

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

  const getFormulationIndex = (formulation: string, formulations: string[]) => {
    const index = formulations.indexOf(formulation)
    return index >= 0 ? index : 0
  }

  const getFormulationColor = (formulation: string, formulations: string[]) => {
    return timelineColors[getFormulationIndex(formulation, formulations) % timelineColors.length]
  }

  const handleExtractIndications = async () => {
    if (!analysisResult) return

    setIsExtracting(true)
    setExtractionError(null)

    try {
      const data = await fdaApi.extractIndicationHistory(
        analysisResult.drug_name,
        analysisResult.labels,
        apiKey
      )
      setExtractionResult(data)
    } catch (err) {
      const detail = typeof err === 'object' && err !== null && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
      setExtractionError(detail || (err instanceof Error ? err.message : 'Failed to extract indication history'))
      setExtractionResult(null)
    } finally {
      setIsExtracting(false)
    }
  }

  const getTimelineData = (labels: Label[]) => {
    const datedLabels = [...labels]
      .filter((label) => parseEffectiveDate(label.effective_time))
      .sort((a, b) => a.effective_time.localeCompare(b.effective_time))
    const minDate = parseEffectiveDate(datedLabels[0]?.effective_time)
    const maxDate = parseEffectiveDate(datedLabels[datedLabels.length - 1]?.effective_time)
    const timeRange = minDate && maxDate
      ? Math.max(maxDate.getTime() - minDate.getTime(), 1)
      : 1
    const formulations = Array.from(new Set(labels.map((label) => label.formulation))).sort()

    return { datedLabels, minDate, maxDate, timeRange, formulations }
  }

  const getPosition = (effectiveTime: string, minDate: Date | null, timeRange: number) => {
    const labelDate = parseEffectiveDate(effectiveTime)
    if (!labelDate || !minDate) return 0
    return ((labelDate.getTime() - minDate.getTime()) / timeRange) * 100
  }

  const getFormulationGroups = (labels: Label[]) => {
    const groups = new Map<string, Label[]>()
    labels.forEach((label) => {
      const key = label.formulation || 'Unspecified formulation'
      groups.set(key, [...(groups.get(key) || []), label])
    })

    return Array.from(groups.entries())
      .map(([formulation, groupLabels]) => ({
        formulation,
        labels: groupLabels.sort((a, b) => a.effective_time.localeCompare(b.effective_time)),
        brands: Array.from(new Set(groupLabels.map((label) => label.brand_name))).sort(),
        latestDate: groupLabels.reduce((latest, label) => (
          label.effective_time > latest ? label.effective_time : latest
        ), ''),
      }))
      .sort((a, b) => b.latestDate.localeCompare(a.latestDate) || a.formulation.localeCompare(b.formulation))
  }

  const getVersionsText = (versions?: string[]) => {
    const uniqueVersions = Array.from(new Set((versions || []).filter(Boolean)))
    return uniqueVersions.length ? uniqueVersions.join(', ') : 'N/A'
  }

  const getFormulationText = (formulation?: ExtractedFormulation) => {
    return formulation?.formulation || 'Unspecified formulation'
  }

  const getClinicalText = (item: ExtractedIndication) => {
    const condition = item.condition || item.indication
    const details = [item.episode_or_phase, item.treatment_mode, item.population].filter(Boolean).join(' / ')

    return (
      <>
        <strong>{condition}</strong>
        {details ? <span> - {details}</span> : null}
      </>
    )
  }

  const getFormulationFirstGroups = (indications: ExtractedIndication[]) => {
    type FormulationFirstRow = { item: ExtractedIndication; formulation?: ExtractedFormulation }
    const groups = new Map<string, {
      formulation: string
      versions: string
      rows: FormulationFirstRow[]
    }>()

    indications.forEach((item) => {
      const formulations = item.formulations?.length ? item.formulations : [undefined]

      formulations.forEach((formulation) => {
        const formulationName = getFormulationText(formulation)
        const versions = getVersionsText(formulation?.versions_seen)
        const key = `${formulationName}__${versions}`
        const group = groups.get(key) || {
          formulation: formulationName,
          versions,
          rows: [] as FormulationFirstRow[],
        }

        group.rows.push({ item, formulation })
        groups.set(key, group)
      })
    })

    return Array.from(groups.values()).sort((a, b) => a.formulation.localeCompare(b.formulation))
  }

  const getIndicationFirstGroups = (indications: ExtractedIndication[]) => {
    return indications.map((item) => ({
      item,
      condition: item.condition || item.indication,
      rows: item.formulations?.length ? item.formulations : [undefined],
    }))
  }

  const getMatrixFormulations = (indications: ExtractedIndication[], sourceLabels: Label[]) => {
    const names = new Set<string>()
    sourceLabels.forEach((label) => {
      names.add(label.formulation || 'Unspecified formulation')
    })
    indications.forEach((item) => {
      const formulations = item.formulations?.length ? item.formulations : [undefined]
      formulations.forEach((formulation) => {
        names.add(getFormulationText(formulation))
      })
    })

    return Array.from(names).sort()
  }

  const getMatrixCell = (item: ExtractedIndication, formulationName: string) => {
    return item.formulations?.find((formulation) => getFormulationText(formulation) === formulationName)
  }

  const getMatrixCellTitle = (formulation: ExtractedFormulation) => {
    const brands = (formulation.brand_names || []).slice(0, 5).join(', ') || 'N/A'
    const applications = (formulation.application_numbers || []).slice(0, 5).join(', ') || 'N/A'
    const routes = (formulation.route || []).join(', ') || 'N/A'
    const dosageForms = (formulation.dosage_form || []).join(', ') || 'N/A'

    return [
      getFormulationText(formulation),
      `Versions: ${getVersionsText(formulation.versions_seen)}`,
      `Brands: ${brands}`,
      `Applications: ${applications}`,
      `Route: ${routes}`,
      `Dosage form: ${dosageForms}`,
    ].join('\n')
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <TrendingUp className="w-8 h-8 text-primary-600" />
          <span>Label Analysis Dashboard</span>
        </h1>
        <p className="mt-2 text-gray-600">
          Analyze all FDA labels for a medication - view timeline, formulations, versions, and indication-section changes
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Drug Name
            </label>
            <div className="flex space-x-2">
              <DrugAutocompleteInput
                id="search"
                value={searchTerm}
                onChange={setSearchTerm}
                onSelect={(term) => performSearch(term)}
                placeholder="e.g., risperidone, aripiprazole"
                className="flex-1"
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

      {analysisResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Total Labels</div>
              <div className="text-3xl font-bold text-gray-900">{analysisResult.total_labels}</div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-blue-200 p-4">
              <div className="text-sm text-gray-600 mb-1">With Indications</div>
              <div className="text-3xl font-bold text-blue-600">{analysisResult.labels_with_indications}</div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-purple-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Formulations</div>
              <div className="text-3xl font-bold text-purple-600">{analysisResult.formulation_count}</div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Set Versions</div>
              <div className="text-3xl font-bold text-gray-700">{analysisResult.version_count}</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-primary-600" />
                  <span>OpenAI Indication Extraction</span>
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  Sends the loaded indication sections with formulation and version metadata.
                </p>
              </div>
              <div className="flex flex-col gap-2 sm:items-end">
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setShowApiKeyInput((value) => !value)}
                    className="btn-secondary"
                  >
                    API Key
                  </button>
                  <button
                    type="button"
                    onClick={handleExtractIndications}
                    disabled={isExtracting}
                    className="btn-primary flex items-center justify-center space-x-2"
                  >
                    {isExtracting ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    <span>{isExtracting ? 'Extracting...' : 'Extract Indications'}</span>
                  </button>
                </div>
                {showApiKeyInput && (
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="OpenAI API key"
                    autoComplete="off"
                    className="input-field w-full min-w-0 sm:w-80"
                  />
                )}
              </div>
            </div>

            {extractionError && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {extractionError}
              </div>
            )}

            {extractionResult && (
              <div className="mt-5 space-y-4">
                <div className="grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
                  <div className="rounded-lg bg-gray-50 p-3">
                    <div className="text-gray-500">Extracted Indications</div>
                    <div className="text-2xl font-semibold text-gray-900">{extractionResult.indications?.length ?? 0}</div>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <div className="text-gray-500">Latest Label Date</div>
                    <div className="text-lg font-semibold text-gray-900">{formatDate(extractionResult.latest_effective_time)}</div>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <div className="text-gray-500">Payload Labels</div>
                    <div className="text-2xl font-semibold text-gray-900">{extractionResult.payload_label_count ?? analysisResult.labels.length}</div>
                  </div>
                </div>

                {extractionResult.warnings && extractionResult.warnings.length > 0 && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    {extractionResult.warnings.join(' ')}
                  </div>
                )}

                <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
                  Years shown are the first year observed in the fetched OpenFDA drug-label records, not first FDA approval or first-ever labeling.
                </div>

                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  {(() => {
                    const indications = extractionResult.indications || []
                    const formulations = getMatrixFormulations(indications, analysisResult.labels)

                    return (
                      <table className="min-w-[900px] divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                          <tr>
                            <th className="sticky left-0 z-10 bg-gray-50 px-4 py-3">Indication</th>
                            {formulations.map((formulation) => (
                              <th key={formulation} className="min-w-48 px-4 py-3">
                                {formulation}
                              </th>
                            ))}
                            <th className="px-4 py-3">Latest</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {indications.map((item, idx) => (
                            <tr key={`${item.indication}-${idx}`}>
                              <td className="sticky left-0 z-10 bg-white px-4 py-3 align-top text-gray-900">
                                <div>{getClinicalText(item)}</div>
                                <div className="mt-1 text-xs text-gray-500">
                                  First OpenFDA year: {item.first_appearance_year || 'N/A'}
                                </div>
                              </td>
                              {formulations.map((formulationName) => {
                                const formulation = getMatrixCell(item, formulationName)

                                return (
                                  <td key={formulationName} className="px-4 py-3 text-center align-middle text-gray-700">
                                    {formulation ? (
                                      <span
                                        title={getMatrixCellTitle(formulation)}
                                        className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-sm font-medium text-green-700"
                                      >
                                        ✓
                                      </span>
                                    ) : (
                                      <span className="text-gray-300">-</span>
                                    )}
                                  </td>
                                )
                              })}
                              <td className="px-4 py-3 align-top">
                                <span className={`rounded-full px-2 py-1 text-xs ${
                                  item.still_present_in_latest
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-gray-100 text-gray-700'
                                }`}>
                                  {item.still_present_in_latest ? 'Present' : 'Not present'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )
                  })()}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm text-gray-600">Group results by</div>
                  <div className="flex rounded-lg bg-gray-100 p-1 text-sm">
                    <button
                      type="button"
                      onClick={() => setExtractionGroupMode('formulation')}
                      className={`rounded-md px-3 py-1 ${
                        extractionGroupMode === 'formulation'
                          ? 'bg-white text-primary-700 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      Formulation / Version
                    </button>
                    <button
                      type="button"
                      onClick={() => setExtractionGroupMode('indication')}
                      className={`rounded-md px-3 py-1 ${
                        extractionGroupMode === 'indication'
                          ? 'bg-white text-primary-700 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      Indication
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {extractionGroupMode === 'formulation' ? (
                    getFormulationFirstGroups(extractionResult.indications || []).map((group) => (
                      <div key={`${group.formulation}-${group.versions}`} className="overflow-hidden rounded-lg border border-gray-200">
                        <div className="bg-gray-50 px-4 py-3 text-sm text-gray-800">
                          <div>{group.formulation}</div>
                          <div className="mt-1 text-xs text-gray-500">Versions: {group.versions}</div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-white text-left text-xs uppercase text-gray-500">
                              <tr>
                                <th className="px-4 py-3">Indication</th>
                                <th className="px-4 py-3">First OpenFDA Year</th>
                                <th className="px-4 py-3">Latest</th>
                                <th className="px-4 py-3">Guardrail</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 bg-white">
                              {group.rows.map(({ item, formulation }, idx) => (
                                <tr key={`${item.indication}-${getFormulationText(formulation)}-${idx}`}>
                                  <td className="px-4 py-3 align-top text-gray-900">
                                    <div>{getClinicalText(item)}</div>
                                    <div className="mt-1 text-xs text-gray-500">
                                      {(formulation?.brand_names || []).slice(0, 3).join(', ')}
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 align-top text-gray-700">
                                    {item.first_appearance_year || 'N/A'}
                                  </td>
                                  <td className="px-4 py-3 align-top">
                                    <span className={`rounded-full px-2 py-1 text-xs ${
                                      item.still_present_in_latest
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-gray-100 text-gray-700'
                                    }`}>
                                      {item.still_present_in_latest ? 'Present' : 'Not present'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 align-top text-xs text-gray-600">
                                    {item.guardrail_check || ''}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ))
                  ) : (
                    getIndicationFirstGroups(extractionResult.indications || []).map((group, groupIdx) => (
                      <div key={`${group.condition}-${groupIdx}`} className="overflow-hidden rounded-lg border border-gray-200">
                        <div className="bg-gray-50 px-4 py-3 text-sm text-gray-800">
                          <div>{getClinicalText(group.item)}</div>
                          <div className="mt-1 text-xs text-gray-500">
                            First OpenFDA year: {group.item.first_appearance_year || 'N/A'}
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-white text-left text-xs uppercase text-gray-500">
                              <tr>
                                <th className="px-4 py-3">Formulation / Version</th>
                                <th className="px-4 py-3">Latest</th>
                                <th className="px-4 py-3">Guardrail</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 bg-white">
                              {group.rows.map((formulation, idx) => (
                                <tr key={`${getFormulationText(formulation)}-${idx}`}>
                                  <td className="px-4 py-3 align-top text-gray-800">
                                    <div>{getFormulationText(formulation)}</div>
                                    <div className="mt-1 text-xs text-gray-500">
                                      Versions: {getVersionsText(formulation?.versions_seen)}
                                    </div>
                                    <div className="mt-1 text-xs text-gray-500">
                                      {(formulation?.brand_names || []).slice(0, 3).join(', ')}
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 align-top">
                                    <span className={`rounded-full px-2 py-1 text-xs ${
                                      group.item.still_present_in_latest
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-gray-100 text-gray-700'
                                    }`}>
                                      {group.item.still_present_in_latest ? 'Present' : 'Not present'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 align-top text-xs text-gray-600">
                                    {group.item.guardrail_check || ''}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-primary-600" />
              <span>Label Timeline (by Effective Date)</span>
            </h2>

            <div className="relative h-32 border-l-2 border-b-2 border-gray-300">
              {(() => {
                const { datedLabels, minDate, maxDate, timeRange, formulations } = getTimelineData(analysisResult.labels)

                if (!minDate || !maxDate) return null

                return (
                  <>
                    {datedLabels.map((label, idx) => {
                      const position = getPosition(label.effective_time, minDate, timeRange)

                      return (
                        <div
                          key={idx}
                          className="absolute bottom-0 transform -translate-x-1/2 group"
                          style={{ left: `${position}%` }}
                          title={`${label.brand_name} - ${formatDate(label.effective_time)} (v${label.version}) - ${label.formulation}`}
                        >
                          <div className={`w-3 h-3 rounded-full ${getFormulationColor(label.formulation, formulations)} cursor-pointer hover:scale-150 transition-transform`}></div>
                          <div className="hidden group-hover:block absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                            {label.brand_name}<br/>
                            {formatDate(label.effective_time)}<br/>
                            v{label.version}<br/>
                            {label.formulation}
                          </div>
                        </div>
                      )
                    })}

                    <div className="absolute -bottom-6 left-0 text-xs text-gray-600">
                      {formatDate(datedLabels[0].effective_time)}
                    </div>
                    <div className="absolute -bottom-6 right-0 text-xs text-gray-600">
                      {formatDate(datedLabels[datedLabels.length - 1].effective_time)}
                    </div>
                  </>
                )
              })()}
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-4 text-sm">
              {Array.from(new Set(analysisResult.labels.map((label) => label.formulation))).sort().slice(0, 8).map((formulation) => (
                <div key={formulation} className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${getFormulationColor(formulation, Array.from(new Set(analysisResult.labels.map((label) => label.formulation))).sort())}`}></div>
                  <span className="text-gray-700">{formulation}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary-600" />
              <span>Formulation Grid</span>
            </h2>

            {(() => {
              const { datedLabels, minDate, maxDate, timeRange, formulations } = getTimelineData(analysisResult.labels)
              const groups = getFormulationGroups(analysisResult.labels)

              if (!minDate || !maxDate) {
                return <div className="text-sm text-gray-500">No dated labels available for grid view.</div>
              }

              return (
                <div className="overflow-x-auto">
                  <div className="min-w-[900px]">
                    <div className="grid grid-cols-[260px_1fr_130px] gap-4 border-b border-gray-200 pb-2 text-xs font-semibold uppercase text-gray-500">
                      <div>Formulation</div>
                      <div className="flex justify-between">
                        <span>{formatDate(datedLabels[0]?.effective_time || '')}</span>
                        <span>{formatDate(datedLabels[datedLabels.length - 1]?.effective_time || '')}</span>
                      </div>
                      <div className="text-right">Labels</div>
                    </div>

                    <div className="divide-y divide-gray-100">
                      {groups.map((group) => (
                        <div key={group.formulation} className="grid grid-cols-[260px_1fr_130px] gap-4 py-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm font-medium text-gray-900">{group.formulation}</div>
                            <div className="mt-1 truncate text-xs text-gray-500">
                              {group.brands.slice(0, 3).join(', ')}
                              {group.brands.length > 3 ? ` +${group.brands.length - 3}` : ''}
                            </div>
                          </div>

                          <div className="relative h-10 rounded-md bg-gray-50 ring-1 ring-inset ring-gray-200">
                            {group.labels.map((label, idx) => {
                              const position = getPosition(label.effective_time, minDate, timeRange)
                              return (
                                <div
                                  key={`${label.set_id}-${label.version}-${idx}`}
                                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 group"
                                  style={{ left: `${position}%` }}
                                  title={`${label.brand_name} - ${formatDate(label.effective_time)} - v${label.version}`}
                                >
                                  <div className={`h-3 w-3 rounded-sm ${getFormulationColor(group.formulation, formulations)} ring-2 ring-white`}></div>
                                  <div className="hidden group-hover:block absolute bottom-5 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-2 py-1 text-xs text-white">
                                    {label.brand_name}<br/>
                                    {formatDate(label.effective_time)}<br/>
                                    v{label.version}
                                  </div>
                                </div>
                              )
                            })}
                          </div>

                          <div className="text-right text-sm text-gray-700">
                            <div className="font-medium">{group.labels.length}</div>
                            <div className="text-xs text-gray-500">{formatDate(group.latestDate)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })()}
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary-600" />
              <span>Raw Indication Sections ({analysisResult.unique_indications.length})</span>
            </h2>

            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <div className="max-h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {analysisResult.unique_indications.map((indication, idx) => (
                  <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-500 mb-2 flex flex-wrap items-center gap-3">
                      <span>Indication #{idx + 1}</span>
                      <span>{indication.text.length} chars</span>
                      <span>{indication.label_count} label{indication.label_count === 1 ? '' : 's'}</span>
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(indication.first_date)} - {formatDate(indication.latest_date)}</span>
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
