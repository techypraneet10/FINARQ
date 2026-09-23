/**
 * Comprehensive TypeScript API Types mirroring Phase 1-6 Backend OpenAPI Contracts.
 */

export type UserRole = 'owner' | 'admin' | 'member' | 'viewer';
export type UserStatus = 'active' | 'suspended' | 'pending';
export type DocumentType = '10-K' | '10-Q' | '8-K' | 'EARNINGS_RELEASE' | 'BALANCE_SHEET' | 'INCOME_STATEMENT' | 'CASH_FLOW' | 'OTHER';
export type IngestionStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type IngestionStage =
  | 'queued'
  | 'uploaded'
  | 'classifying'
  | 'parsing'
  | 'ocr'
  | 'normalizing'
  | 'table_extraction'
  | 'chunking'
  | 'embedding'
  | 'indexing'
  | 'completed'
  | 'failed';

export type AnswerabilityState =
  | 'answerable'
  | 'partially_answerable'
  | 'insufficient_evidence'
  | 'conflicting_evidence'
  | 'ambiguous_query'
  | 'calculation_failed'
  | 'grounding_failed'
  | 'completed'
  | 'invalid_query';

export type GroundingStatus = 'grounded' | 'partially_grounded' | 'ungrounded' | 'conflicting';

export type ResponseStyle = 'concise' | 'standard' | 'detailed' | 'analytical';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
  user_id: string;
  tenant_id: string;
  role: UserRole;
  permissions: string[];
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface CreateUserRequest {
  email: string;
  password?: string;
  role: UserRole;
}

export interface AuditEventResponse {
  event_id: string;
  timestamp: string;
  tenant_id: string | null;
  actor_user_id: string | null;
  event_type: string;
  resource_type: string;
  resource_id: string | null;
  action: string;
  outcome: string;
  request_id: string | null;
  trace_id: string | null;
  source_ip: string | null;
  user_agent: string | null;
  metadata: Record<string, any>;
}

export interface DocumentResponse {
  id: string;
  title: string;
  document_type: DocumentType;
  ticker_symbol: string | null;
  fiscal_year: number | null;
  fiscal_period: string | null;
  storage_uri: string;
  file_hash_sha256: string;
  pages_count: number;
  current_version_id: string | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersionResponse {
  id: string;
  document_id: string;
  version_number: number;
  storage_uri: string;
  file_hash_sha256: string;
  filename: string;
  file_size_bytes: number;
  mime_type: string;
  pages_count: number;
  created_at: string;
}

export interface LayoutBlockResponse {
  id: string;
  page_number: number;
  block_type: string;
  content: string;
  reading_order: number;
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
  confidence: number;
  section_path: string;
  font_size: number | null;
  is_bold: boolean;
  source_method: string;
  metadata: Record<string, any>;
}

export interface RetrievalSearchRequest {
  query: string;
  filters?: RetrievalFilterRequest;
  top_k?: number;
  use_reranker?: boolean;
  min_score?: number;
}

export interface FinancialTableCellResponse {
  row_idx: number;
  col_idx: number;
  value: string;
  raw_text: string;
  is_header: boolean;
  currency: string | null;
  scale: number;
  is_negative: boolean;
  is_percentage: boolean;
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
}

export interface FinancialTableResponse {
  id: string;
  page_number: number;
  title: string;
  headers: string[];
  rows: string[][];
  cells: FinancialTableCellResponse[];
  units: string;
  currency: string;
  scale: number;
  footnotes: string[];
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
  markdown_repr: string;
  csv_repr: string;
  metadata: Record<string, any>;
}

export interface DocumentPageResponse {
  id: string;
  document_id: string;
  version_id: string;
  page_number: number;
  text_content: string;
  blocks: LayoutBlockResponse[];
  tables: FinancialTableResponse[];
  extraction_method: string;
  has_images: boolean;
  confidence: number;
  width: number;
  height: number;
  metadata: Record<string, any>;
}

export interface DocumentChunkResponse {
  id: string;
  document_id: string;
  document_version_id: string;
  page_number: number;
  page_numbers: number[];
  chunk_index: number;
  chunk_type: string;
  content: string;
  section_path: string;
  table_id: string | null;
  token_count: number;
  char_count: number;
  source_block_ids: string[];
  created_at: string;
}

export interface IngestionJobResponse {
  id: string;
  document_id: string;
  version_id: string;
  status: IngestionStatus;
  current_stage: IngestionStage;
  progress_pct: number;
  chunks_indexed: number;
  error_message: string | null;
  error_stage: string | null;
  error_details?: Record<string, any>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DocumentUploadResponse {
  document_id: string;
  version_id: string;
  job_id: string;
  title: string;
  document_type: string;
  status: string;
  created_at: string;
}

export interface RetrievalFilterRequest {
  document_ids?: string[];
  version_ids?: string[];
  ticker_symbols?: string[];
  fiscal_years?: number[];
  fiscal_periods?: string[];
  document_types?: string[];
  sections?: string[];
  chunk_types?: string[];
  table_only?: boolean;
  custom_metadata?: Record<string, any>;
}

export interface FinancialSignalsResponse {
  tickers: string[];
  company_names: string[];
  metrics: string[];
  fiscal_years: number[];
  fiscal_periods: string[];
  sections: string[];
  statement_types: string[];
  currencies: string[];
  is_comparison: boolean;
  is_table_lookup: boolean;
  is_multi_period: boolean;
}

export interface ProvenanceLineageResponse {
  document_id: string;
  document_version_id: string;
  page_numbers: number[];
  source_block_ids: string[];
  section_path: string;
  chunk_type: string;
  table_id: string | null;
  chunk_id: string | null;
}

export interface RankedEvidenceResponse {
  rank: number;
  chunk_id: string;
  document_id: string;
  document_version_id: string;
  page_number: number;
  page_numbers: number[];
  chunk_type: string;
  content: string;
  section_path: string;
  table_id: string | null;
  source_block_ids: string[];
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
  content_hash: string;
  ticker: string | null;
  fiscal_year: number | null;
  fiscal_period: string | null;
  retrieval_sources: string[];
  dense_score: number | null;
  sparse_score: number | null;
  fusion_score: number;
  reranker_score: number | null;
  final_score: number;
  provenance: ProvenanceLineageResponse;
  metadata: Record<string, any>;
}

export interface RetrievalSearchResponse {
  query_id: string;
  raw_query: string;
  normalized_query: string;
  query_type: string;
  signals: FinancialSignalsResponse;
  retrieval_strategy: string;
  execution_stages: string[];
  evidence_count: number;
  total_candidates: number;
  fallback_occurred: boolean;
  fallback_reason: string | null;
  evidence: RankedEvidenceResponse[];
  timing_ms: Record<string, number>;
  created_at: string;
}

export interface FiscalPeriodResponse {
  fiscal_year: number | null;
  period_type: string;
  source_text: string;
  start_date: string | null;
  end_date: string | null;
  is_uncertain: boolean;
  label: string;
}

export interface FinancialValueResponse {
  raw_value: string;
  display_value: string;
  numeric_value: string;
  unscaled_value: string;
  currency: string | null;
  scale: string;
  unit: string;
  is_negative: boolean;
  is_percentage: boolean;
}

export interface FinancialFactResponse {
  fact_id: string;
  metric: string;
  value: FinancialValueResponse;
  period: FiscalPeriodResponse;
  company: string | null;
  ticker: string | null;
  document_id: string;
  document_version_id: string;
  page_number: number;
  chunk_id: string;
  table_id: string | null;
  source_evidence_id: string;
  extraction_method: string;
  confidence: number;
  source_text: string;
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
  section_path: string;
  metadata: Record<string, any>;
}

export interface CalculationInputResponse {
  name: string;
  value: string;
  fact_id: string | null;
  source_description: string;
  unit: string;
  currency: string | null;
}

export interface CalculationResultResponse {
  calculation_id: string;
  operation: string;
  formula: string;
  inputs: CalculationInputResponse[];
  input_fact_ids: string[];
  raw_result: string;
  rounded_result: string;
  display_result: string;
  unit: string;
  currency: string | null;
  rounding_precision: number;
  success: boolean;
  error_message: string | null;
}

export interface ClaimResponse {
  claim_id: string;
  text: string;
  claim_type: string;
  source_fact_ids: string[];
  calculation_ids: string[];
  reasoning_step_ids: number[];
  confidence: number;
  is_grounded: boolean;
}

export interface CitationResponse {
  citation_id: string;
  claim_id: string;
  document_id: string;
  document_version_id: string;
  page_number: number;
  page_numbers: number[];
  chunk_id: string;
  table_id: string | null;
  section_path: string;
  ticker: string | null;
  source_excerpt: string;
  bounding_box: { x0: number; y0: number; x1: number; y1: number } | null;
  citation_type: string;
  verified: boolean;
  validation_notes: string | null;
}

export interface EvidenceConflictResponse {
  conflict_id: string;
  metric: string;
  period: string;
  conflicting_facts: FinancialFactResponse[];
  difference_description: string;
  resolved: boolean;
  resolved_fact_id: string | null;
  resolution_rationale: string | null;
}

export interface ReasoningPlanResponse {
  plan_id: string;
  query: string;
  operations: string[];
  target_metrics: string[];
  target_periods: string[];
  target_companies: string[];
  required_fact_keys: string[];
  steps_description: string[];
  is_multi_period: boolean;
  is_comparison: boolean;
}

export interface ReasoningStepTraceResponse {
  step_number: number;
  operation: string;
  description: string;
  input_fact_ids: string[];
  calculation_id: string | null;
  output_summary: string;
  status: string;
}

export interface GroundingValidationResultResponse {
  status: GroundingStatus;
  total_claims: number;
  grounded_claims: number;
  ungrounded_claims: number;
  conflicting_claims: number;
  unverified_citations: number;
  details: Record<string, any>[];
  validation_passed: boolean;
}

export interface AnswerPackageResponse {
  package_id: string;
  query_id: string;
  raw_query: string;
  normalized_query: string;
  answerability: AnswerabilityState;
  answerability_rationale: string;
  answer?: string;
  status?: string;
  grounding_status?: GroundingStatus;
  reasoning_plan: ReasoningPlanResponse;
  facts: FinancialFactResponse[];
  calculations: CalculationResultResponse[];
  reasoning_trace: ReasoningStepTraceResponse[];
  claims: ClaimResponse[];
  citations: CitationResponse[];
  evidence: RankedEvidenceResponse[];
  conflicts: EvidenceConflictResponse[];
  missing_facts: string[];
  grounding_validation: GroundingValidationResultResponse | null;
  confidence_score: number;
  warnings: string[];
  execution_time_ms: Record<string, number>;
  created_at: string;
}

export interface AnswerMetadataResponse {
  model_name: string;
  prompt_version: string;
  attempts: number;
  used_fallback: boolean;
  cache_hit: boolean;
}

export interface AnswerQueryResponse {
  answer_id: string;
  query_id: string;
  status: string;
  answer: string;
  raw_query?: string;
  answerability?: AnswerabilityState;
  answerability_rationale?: string;
  claims: ClaimResponse[];
  citations: CitationResponse[];
  calculations: CalculationResultResponse[];
  facts: FinancialFactResponse[];
  missing_facts?: string[];
  evidence?: RankedEvidenceResponse[];
  conflicts?: EvidenceConflictResponse[];
  grounding_validation?: GroundingValidationResultResponse | null;
  reasoning_plan: ReasoningPlanResponse | null;
  grounding_status: GroundingStatus;
  confidence_score: number;
  warnings: string[];
  metadata: AnswerMetadataResponse;
  execution_time_ms: Record<string, number>;
  created_at: string;
}

export interface AnswerQueryRequest {
  query: string;
  response_style?: ResponseStyle;
  include_citations?: boolean;
  citation_style?: string;
  filters?: RetrievalFilterRequest;
  top_k?: number;
  use_reranker?: boolean;
  custom_instructions?: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ComponentStatus {
  status: string;
  details: string | null;
}

export interface ReadyResponse {
  status: string;
  checks: Record<string, ComponentStatus>;
  timestamp: string;
}

export interface MetricsResponse {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  histograms: Record<string, Record<string, number>>;
  telemetry: Record<string, any>;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details: Record<string, any>;
  request_id?: string;
}
