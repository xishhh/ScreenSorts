export interface SearchResultItem {
  image_id: string
  image_path: string
  text: string
  score: number
  source_dataset: string
  ocr_status: boolean
  embedding_model: string
  created_at: string
}

export interface SearchTiming {
  query_embedding_ms: number
  vector_search_ms: number
  total_ms: number
}

export interface SearchResponse {
  query: string
  top_k: number
  threshold: number
  results: SearchResultItem[]
  total_results: number
  timing: SearchTiming
}

export interface ExplainItem {
  image_id: string
  image_path: string
  text: string
  score: number
  source_dataset: string
  explanation: string
  model: string
  cache_hit: boolean
  latency_ms: number
}

export interface ExplainTiming {
  search_ms: number
  explain_ms: number
  total_ms: number
}

export interface ExplainResponse {
  query: string
  top_k: number
  threshold: number
  total_explanations: number
  explanations: ExplainItem[]
  timing: ExplainTiming
}

export interface ApiError {
  detail: string
}
