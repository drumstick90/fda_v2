export interface DrugResult {
  drug: string
  last_updated: string
  indications_and_usage: string
  indications?: string[]
  generic_name?: string
  brand_names?: string[]
  manufacturer?: string
  approval_date?: string
  route?: string[]
  dosage_form?: string[]
  strength?: string[]
  ndc?: string[]
  application_number?: string
  product_type?: string
}

export interface BatchQueryRequest {
  drugs: string[]
  include_fields?: string[]
  rate_limit_delay?: number
}

export interface BatchQueryResponse {
  results: DrugResult[]
  total_processed: number
  total_found: number
  errors: { drug: string; error: string }[]
  execution_time: number
}

export interface SearchFilters {
  drug_name?: string
  manufacturer?: string
  approval_year_start?: number
  approval_year_end?: number
  product_type?: string
  route?: string
  dosage_form?: string
}

export interface ApiResponse<T> {
  data: T
  meta: {
    total: number
    page: number
    per_page: number
    last_updated: string
  }
}