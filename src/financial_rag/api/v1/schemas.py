"""Pydantic API schemas for request/response payloads in API v1."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from financial_rag.domain.entities.security import AuditEventType, UserRole, UserStatus


class HealthResponse(BaseModel):
    """Liveness probe response payload."""

    status: str = Field(default="healthy", description="Current service health status")
    app_name: str = Field(description="Application service identifier")
    version: str = Field(description="Service semantic version")
    environment: str = Field(description="Runtime environment")
    timestamp: datetime = Field(description="Current UTC timestamp")


class VersionResponse(BaseModel):
    """Safe application version and build metadata payload."""

    application: str = Field(description="Application service identifier")
    version: str = Field(description="Semantic version")
    git_sha: str = Field(description="Git commit SHA or release identifier")
    build_timestamp: str = Field(description="UTC build timestamp")
    environment: str = Field(description="Runtime environment")
    python_version: str = Field(description="Python interpreter version")


class ComponentStatus(BaseModel):
    """Health check status for an individual subsystem or adapter."""

    status: str = Field(description="Component status ('healthy', 'disabled', 'unhealthy')")
    details: str | None = Field(default=None, description="Optional diagnostic information")


class ReadyResponse(BaseModel):
    """Readiness probe response payload."""

    status: str = Field(description="Overall service readiness status ('ready' or 'not_ready')")
    checks: dict[str, ComponentStatus] = Field(
        description="Health status of external dependencies and subsystem adapters"
    )
    timestamp: datetime = Field(description="Current UTC timestamp")


class ErrorDetail(BaseModel):
    """Detailed error object conforming to standard structured error envelopes."""

    code: str = Field(description="Standardized error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Contextual parameters or validation issues"
    )
    request_id: str | None = Field(default=None, description="Correlation Request ID")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: ErrorDetail


# ==========================================
# Phase 1 Ingestion Schemas
# ==========================================


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful document upload and job registration."""

    document_id: str = Field(description="Unique logical document identifier")
    version_id: str = Field(description="Unique document version identifier")
    job_id: str = Field(description="Asynchronous ingestion job identifier")
    title: str = Field(description="Document display title")
    document_type: str = Field(description="Categorical document type (e.g. 10-K, 10-Q)")
    status: str = Field(description="Initial ingestion status")
    created_at: datetime = Field(description="Upload UTC timestamp")


class DocumentResponse(BaseModel):
    """Document metadata representation."""

    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    document_type: str = Field(description="Document type")
    ticker_symbol: str | None = Field(default=None, description="Stock ticker symbol")
    fiscal_year: int | None = Field(default=None, description="Fiscal year")
    fiscal_period: str | None = Field(default=None, description="Fiscal period (e.g. Q1, Q2, FY)")
    storage_uri: str = Field(description="Object storage URI")
    file_hash_sha256: str = Field(description="SHA-256 binary digest")
    pages_count: int = Field(description="Number of extracted pages")
    current_version_id: str | None = Field(default=None, description="Active document version ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    created_at: datetime = Field(description="Creation UTC timestamp")
    updated_at: datetime = Field(description="Last update UTC timestamp")


class DocumentVersionResponse(BaseModel):
    """Document immutable version record."""

    id: str = Field(description="Version ID")
    document_id: str = Field(description="Parent Document ID")
    version_number: int = Field(description="Incremental version sequence number")
    storage_uri: str = Field(description="Storage URI for this version's binary")
    file_hash_sha256: str = Field(description="SHA-256 hash of this version")
    filename: str = Field(description="Sanitized original filename")
    file_size_bytes: int = Field(description="Binary size in bytes")
    mime_type: str = Field(description="File MIME type")
    pages_count: int = Field(description="Total pages extracted")
    created_at: datetime = Field(description="Version creation timestamp")


class DocumentChunkResponse(BaseModel):
    """Extracted chunk representation with rich provenance."""

    id: str = Field(description="Chunk ID")
    document_id: str = Field(description="Document ID")
    document_version_id: str = Field(description="Document Version ID")
    page_number: int = Field(description="Primary page number")
    page_numbers: list[int] = Field(description="All pages spanned by chunk")
    chunk_index: int = Field(description="Sequential chunk index")
    chunk_type: str = Field(description="Chunk type ('text', 'table', 'section_header')")
    content: str = Field(description="Chunk text/markdown content")
    section_path: str = Field(description="Hierarchical section path")
    table_id: str | None = Field(default=None, description="Associated table ID if table chunk")
    token_count: int = Field(description="Estimated token count")
    char_count: int = Field(description="Character count")
    source_block_ids: list[str] = Field(default_factory=list, description="Source block IDs")
    created_at: datetime = Field(description="Creation UTC timestamp")


class LayoutBlockResponse(BaseModel):
    """Visual layout block bounding box and text content."""

    id: str = Field(description="Block ID")
    page_number: int = Field(description="Page number")
    block_type: str = Field(
        description="Block category ('text', 'title', 'table', 'header', 'footer')"
    )
    content: str = Field(description="Text content")
    reading_order: int = Field(default=0, description="Sequential reading order")
    bounding_box: dict[str, float] | None = Field(
        default=None, description="Coordinates bounding box (x0, y0, x1, y1)"
    )
    confidence: float = Field(default=1.0, description="Extraction confidence")
    section_path: str = Field(default="", description="Hierarchical section path")
    font_size: float | None = Field(default=None, description="Font point size")
    is_bold: bool = Field(default=False, description="Is bold flag")
    source_method: str = Field(default="native", description="Extraction method ('native', 'ocr')")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Block metadata")


class FinancialTableCellResponse(BaseModel):
    """Structured financial table cell model."""

    row_idx: int = Field(description="0-indexed row position")
    col_idx: int = Field(description="0-indexed column position")
    value: str = Field(description="Parsed or formatted cell text value")
    raw_text: str = Field(description="Original cell string")
    is_header: bool = Field(default=False, description="Header cell flag")
    currency: str | None = Field(default=None, description="Currency identifier")
    scale: float = Field(default=1.0, description="Multiplier scale")
    is_negative: bool = Field(default=False, description="Accounting negative flag")
    is_percentage: bool = Field(default=False, description="Percentage cell flag")
    bounding_box: dict[str, float] | None = Field(default=None, description="Cell bounding box")


class FinancialTableResponse(BaseModel):
    """Extracted financial table model with structured cells and markdown representation."""

    id: str = Field(description="Table ID")
    page_number: int = Field(description="Page number containing table")
    title: str = Field(default="", description="Table caption or title")
    headers: list[str] = Field(default_factory=list, description="Header column names")
    rows: list[list[str]] = Field(default_factory=list, description="Grid row string values")
    cells: list[FinancialTableCellResponse] = Field(
        default_factory=list, description="Structured parsed cell details"
    )
    units: str = Field(default="", description="Table unit description (e.g. 'In millions')")
    currency: str = Field(default="USD", description="Currency symbol or ISO code")
    scale: float = Field(default=1.0, description="Scale factor")
    footnotes: list[str] = Field(default_factory=list, description="Table footnotes")
    bounding_box: dict[str, float] | None = Field(default=None, description="Table bounding box")
    markdown_repr: str = Field(default="", description="Markdown grid representation")
    csv_repr: str = Field(default="", description="CSV representation")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Table metadata")


class DocumentPageResponse(BaseModel):
    """Full extracted document page with text, layout blocks, and financial tables."""

    id: str = Field(description="Page ID")
    document_id: str = Field(description="Document ID")
    version_id: str = Field(description="Version ID")
    page_number: int = Field(description="1-indexed page number")
    text_content: str = Field(description="Full extracted page text")
    blocks: list[LayoutBlockResponse] = Field(
        default_factory=list, description="Layout blocks with bounding boxes"
    )
    tables: list[FinancialTableResponse] = Field(
        default_factory=list, description="Structured tables"
    )
    extraction_method: str = Field(description="Extraction method ('native', 'ocr', 'fallback')")
    has_images: bool = Field(description="Whether page contains embedded images")
    confidence: float = Field(description="Overall OCR / extraction confidence")
    width: float = Field(description="Page width in points")
    height: float = Field(description="Page height in points")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Page metadata")


class IngestionJobResponse(BaseModel):
    """Asynchronous ingestion job state and progress diagnostics."""

    id: str = Field(description="Job ID")
    document_id: str = Field(description="Document ID")
    version_id: str = Field(description="Version ID")
    status: str = Field(description="Job status ('pending', 'processing', 'completed', 'failed')")
    current_stage: str = Field(description="Current pipeline stage")
    progress_pct: float = Field(description="Processing completion percentage (0-100)")
    chunks_indexed: int = Field(description="Number of indexed chunks")
    error_message: str | None = Field(default=None, description="Error message if failed")
    error_stage: str | None = Field(default=None, description="Stage at which failure occurred")
    error_details: dict[str, Any] = Field(
        default_factory=dict, description="Error diagnostic payload"
    )
    created_at: datetime = Field(description="Job creation timestamp")
    started_at: datetime | None = Field(default=None, description="Execution start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")


# ==========================================
# Phase 2 Retrieval Schemas
# ==========================================


class RetrievalFilterRequest(BaseModel):
    """Filter criteria applied across retrieval stages."""

    document_ids: list[str] | None = Field(
        default=None, description="Restricted list of document IDs"
    )
    version_ids: list[str] | None = Field(
        default=None, description="Restricted list of document version IDs"
    )
    ticker_symbols: list[str] | None = Field(
        default=None, description="Filter by stock ticker symbol (e.g. ['AAPL', 'MSFT'])"
    )
    fiscal_years: list[int] | None = Field(
        default=None, description="Filter by fiscal years (e.g. [2023, 2024])"
    )
    fiscal_periods: list[str] | None = Field(
        default=None, description="Filter by fiscal periods (e.g. ['Q1', 'Q3', 'FY'])"
    )
    document_types: list[str] | None = Field(
        default=None, description="Filter by document type (e.g. ['10-K', '10-Q'])"
    )
    sections: list[str] | None = Field(
        default=None, description="Filter by filing sections (e.g. ['Item 1A', 'Item 7'])"
    )
    chunk_types: list[str] | None = Field(
        default=None, description="Filter by chunk types ('text', 'table', 'section_header')"
    )
    table_only: bool | None = Field(
        default=None, description="Restrict retrieval strictly to table chunks"
    )
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional exact match metadata constraints"
    )


class RetrievalSearchRequest(BaseModel):
    """User inquiry search request payload."""

    query: str = Field(
        min_length=2,
        max_length=2000,
        description="User financial query or question",
        examples=["What was Apple's total revenue in fiscal year 2024?"],
    )
    filters: RetrievalFilterRequest | None = Field(
        default=None, description="Optional metadata filter parameters"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of final top evidence items to return",
    )
    dense_top_k: int | None = Field(
        default=None,
        ge=1,
        le=500,
        description="Override candidate count retrieved from dense vector search",
    )
    sparse_top_k: int | None = Field(
        default=None,
        ge=1,
        le=500,
        description="Override candidate count retrieved from sparse lexical search",
    )
    rerank_top_k: int | None = Field(
        default=None,
        ge=1,
        le=200,
        description="Override candidate count selected after reranking",
    )
    use_reranker: bool = Field(
        default=True, description="Enable cross-encoder reranking over fused candidates"
    )


class FinancialSignalsResponse(BaseModel):
    """High-confidence extracted financial and corporate signals."""

    tickers: list[str] = Field(description="Identified company ticker symbols")
    company_names: list[str] = Field(description="Identified company names")
    metrics: list[str] = Field(description="Identified financial metrics")
    fiscal_years: list[int] = Field(description="Identified fiscal years")
    fiscal_periods: list[str] = Field(description="Identified fiscal quarters / periods")
    sections: list[str] = Field(description="Identified SEC filing sections")
    statement_types: list[str] = Field(description="Identified financial statements")
    currencies: list[str] = Field(description="Identified currencies")
    is_comparison: bool = Field(description="Query contains comparative / growth intent")
    is_table_lookup: bool = Field(description="Query targets structured tabular data")
    is_multi_period: bool = Field(description="Query spans multiple fiscal periods")


class ProvenanceLineageResponse(BaseModel):
    """Verifiable source lineage tracing an evidence item to its origin."""

    document_id: str = Field(description="Parent Document ID")
    document_version_id: str = Field(description="Document Version ID")
    page_numbers: list[int] = Field(description="All document page numbers containing chunk")
    source_block_ids: list[str] = Field(description="Extracted layout block IDs")
    section_path: str = Field(description="Document hierarchy section path")
    chunk_type: str = Field(description="Chunk type ('text', 'table', 'section_header')")
    table_id: str | None = Field(default=None, description="Table ID if extracted from table")
    chunk_id: str | None = Field(default=None, description="Unique chunk identifier")


class RankedEvidenceResponse(BaseModel):
    """A single verified, ranked evidence chunk with complete provenance and score transparency."""

    rank: int = Field(description="Ordinal ranking (1..N) in final evidence set")
    chunk_id: str = Field(description="Chunk ID")
    document_id: str = Field(description="Document ID")
    document_version_id: str = Field(description="Document Version ID")
    page_number: int = Field(description="Primary page number")
    page_numbers: list[int] = Field(description="All pages spanned by chunk")
    chunk_type: str = Field(description="Chunk type ('text', 'table', 'section_header')")
    content: str = Field(description="Text or Markdown content of chunk")
    section_path: str = Field(description="Hierarchical section path")
    table_id: str | None = Field(default=None, description="Associated table ID")
    source_block_ids: list[str] = Field(description="Source layout block IDs")
    bounding_box: dict[str, float] | None = Field(
        default=None, description="Bounding box coordinates"
    )
    content_hash: str = Field(description="SHA-256 hash of chunk content")
    ticker: str | None = Field(default=None, description="Associated ticker symbol")
    fiscal_year: int | None = Field(default=None, description="Associated fiscal year")
    fiscal_period: str | None = Field(default=None, description="Associated fiscal period")
    retrieval_sources: list[str] = Field(
        description="Retrieval systems producing candidate ('dense', 'sparse', 'both')"
    )
    dense_score: float | None = Field(default=None, description="Dense vector cosine score")
    sparse_score: float | None = Field(default=None, description="BM25 lexical score")
    fusion_score: float = Field(description="Reciprocal Rank Fusion score")
    reranker_score: float | None = Field(default=None, description="Cross-encoder reranking score")
    final_score: float = Field(description="Calibrated final evidence relevance score")
    provenance: ProvenanceLineageResponse = Field(description="Source provenance lineage")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata payload")


class RetrievalSearchResponse(BaseModel):
    """Complete ranked evidence set response for user retrieval inquiry."""

    query_id: str = Field(description="Unique correlation ID for this retrieval request")
    raw_query: str = Field(description="Original user query text")
    normalized_query: str = Field(description="Sanitized and normalized query text")
    query_type: str = Field(description="Query intent classification")
    signals: FinancialSignalsResponse = Field(description="Extracted financial signals")
    retrieval_strategy: str = Field(description="Retrieval execution strategy description")
    execution_stages: list[str] = Field(description="List of pipeline stages that executed")
    evidence_count: int = Field(description="Number of ranked evidence items returned")
    total_candidates: int = Field(description="Total candidate pool size before selection")
    fallback_occurred: bool = Field(
        default=False, description="Flag indicating if a graceful fallback occurred"
    )
    fallback_reason: str | None = Field(
        default=None, description="Diagnostic explanation if fallback occurred"
    )
    evidence: list[RankedEvidenceResponse] = Field(
        description="Ranked, deduplicated, provenance-preserving evidence items"
    )
    timing_ms: dict[str, float] = Field(description="Execution latency breakdown in milliseconds")
    created_at: datetime = Field(description="Retrieval response UTC timestamp")


# ==========================================
# Phase 3 Reasoning & AnswerPackage Schemas
# ==========================================


class FiscalPeriodResponse(BaseModel):
    """Normalized financial reporting period schema."""

    fiscal_year: int | None = Field(default=None, description="Fiscal year (e.g. 2024)")
    period_type: str = Field(description="Period identifier ('FY', 'Q1', 'Q2', 'Q3', 'Q4', 'TTM')")
    source_text: str = Field(description="Verbatim source period text")
    start_date: str | None = Field(default=None, description="Period start date if known")
    end_date: str | None = Field(default=None, description="Period end date if known")
    is_uncertain: bool = Field(default=False, description="Flag indicating period ambiguity")
    label: str = Field(description="Human-readable formatted period label")


class FinancialValueResponse(BaseModel):
    """High-precision financial value representation schema."""

    raw_value: str = Field(description="Original verbatim string from document")
    display_value: str = Field(
        description="Standardized display representation (e.g. '$391.0 billion')"
    )
    numeric_value: str = Field(description="Fully scaled exact Decimal string representation")
    unscaled_value: str = Field(description="Unscaled Decimal string representation")
    currency: str | None = Field(default=None, description="ISO currency code or symbol")
    scale: str = Field(
        description="Multiplier scale ('exact', 'thousands', 'millions', 'billions', 'trillions', 'percent')"
    )
    unit: str = Field(description="Complete unit descriptor")
    is_negative: bool = Field(
        default=False, description="True if value represents an accounting negative"
    )
    is_percentage: bool = Field(default=False, description="True if value represents a percentage")


class FinancialFactResponse(BaseModel):
    """Extracted and verified financial fact schema."""

    fact_id: str = Field(description="Unique fact identifier")
    metric: str = Field(description="Financial metric name (e.g. 'Revenue', 'Operating Income')")
    value: FinancialValueResponse = Field(description="Structured financial value")
    period: FiscalPeriodResponse = Field(description="Reporting fiscal period")
    company: str | None = Field(default=None, description="Company or reporting entity name")
    ticker: str | None = Field(default=None, description="Stock ticker symbol")
    document_id: str = Field(description="Source document ID")
    document_version_id: str = Field(description="Source document version ID")
    page_number: int = Field(description="Page number containing fact")
    chunk_id: str = Field(description="Source chunk ID")
    table_id: str | None = Field(default=None, description="Source table ID if tabular")
    source_evidence_id: str = Field(description="ID of source evidence item")
    extraction_method: str = Field(
        description="Extraction method ('table_structured', 'narrative_regex')"
    )
    confidence: float = Field(description="Extraction confidence score (0.0 - 1.0)")
    source_text: str = Field(description="Verbatim source sentence or cell text")
    bounding_box: dict[str, float] | None = Field(
        default=None, description="Coordinates bounding box"
    )
    section_path: str = Field(default="", description="SEC filing section hierarchy path")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom fact metadata")


class CalculationInputResponse(BaseModel):
    """Operand input used in deterministic financial arithmetic."""

    name: str = Field(description="Input operand name and period description")
    value: str = Field(description="Decimal value string")
    fact_id: str | None = Field(default=None, description="Supporting FinancialFact ID")
    source_description: str = Field(description="Provenance description of operand")
    unit: str = Field(default="", description="Operand unit descriptor")
    currency: str | None = Field(default=None, description="Operand currency")


class CalculationResultResponse(BaseModel):
    """Audited deterministic calculation result."""

    calculation_id: str = Field(description="Unique calculation execution ID")
    operation: str = Field(
        description="Reasoning operation ('difference', 'percentage_change', 'growth_rate', etc.)"
    )
    formula: str = Field(description="Mathematical formula applied")
    inputs: list[CalculationInputResponse] = Field(description="List of input operands")
    input_fact_ids: list[str] = Field(description="IDs of supporting facts")
    raw_result: str = Field(description="Exact unrounded Decimal calculation result string")
    rounded_result: str = Field(description="Rounded Decimal calculation result string")
    display_result: str = Field(
        description="Formatted display string (e.g. '+20.00%', '$12.50 billion')"
    )
    unit: str = Field(description="Result unit")
    currency: str | None = Field(default=None, description="Result currency")
    rounding_precision: int = Field(default=2, description="Decimal places rounded to")
    success: bool = Field(description="True if calculation succeeded without error")
    error_message: str | None = Field(
        default=None, description="Error diagnostics if calculation failed"
    )


class ReasoningPlanResponse(BaseModel):
    """Structured query reasoning plan."""

    plan_id: str = Field(description="Plan unique identifier")
    query: str = Field(description="Inquiry text")
    operations: list[str] = Field(description="Planned reasoning operations")
    target_metrics: list[str] = Field(description="Identified target metrics")
    target_periods: list[str] = Field(description="Identified target periods")
    target_companies: list[str] = Field(description="Identified target companies")
    required_fact_keys: list[str] = Field(description="Required facts for sufficiency")
    steps_description: list[str] = Field(description="Plain text plan execution steps")
    is_multi_period: bool = Field(description="Multi-period inquiry flag")
    is_comparison: bool = Field(description="Comparative inquiry flag")


class ReasoningStepTraceResponse(BaseModel):
    """Auditable reasoning step trace."""

    step_number: int = Field(description="Step sequence number")
    operation: str = Field(description="Reasoning operation performed")
    description: str = Field(description="Step description")
    input_fact_ids: list[str] = Field(description="Input fact IDs used")
    calculation_id: str | None = Field(
        default=None, description="Calculation ID if calculation step"
    )
    output_summary: str = Field(description="Step output summary")
    status: str = Field(description="Step execution status ('success', 'failed')")


class ClaimResponse(BaseModel):
    """Atomic verifiable factual or calculated claim."""

    claim_id: str = Field(description="Claim unique identifier")
    text: str = Field(description="Verifiable claim statement")
    claim_type: str = Field(
        description="Claim category ('direct_fact', 'calculated', 'comparison', 'trend')"
    )
    source_fact_ids: list[str] = Field(description="Supporting fact IDs")
    calculation_ids: list[str] = Field(description="Supporting calculation IDs")
    reasoning_step_ids: list[int] = Field(description="Associated reasoning step indices")
    confidence: float = Field(description="Claim confidence score")
    is_grounded: bool = Field(description="True if verified grounded against evidence")


class CitationResponse(BaseModel):
    """Verifiable source citation linking claim to exact source document provenance."""

    citation_id: str = Field(description="Citation unique identifier")
    claim_id: str = Field(description="Associated claim ID")
    document_id: str = Field(description="Document ID")
    document_version_id: str = Field(description="Document Version ID")
    page_number: int = Field(description="Page number")
    page_numbers: list[int] = Field(description="All pages spanned")
    chunk_id: str = Field(description="Source chunk ID")
    table_id: str | None = Field(default=None, description="Source table ID if tabular")
    section_path: str = Field(description="Document section path")
    ticker: str | None = Field(default=None, description="Company ticker")
    source_excerpt: str = Field(description="Verbatim source excerpt")
    bounding_box: dict[str, float] | None = Field(
        default=None, description="Visual coordinates bounding box"
    )
    citation_type: str = Field(
        description="Citation category ('direct_source', 'calculation_source', 'table_cell')"
    )
    verified: bool = Field(description="True if verified against retrieved evidence pool")
    validation_notes: str | None = Field(default=None, description="Verification notes")


class EvidenceConflictResponse(BaseModel):
    """Discrepancy detected across retrieved evidence."""

    conflict_id: str = Field(description="Conflict unique identifier")
    metric: str = Field(description="Disputed metric name")
    period: str = Field(description="Disputed fiscal period")
    conflicting_facts: list[FinancialFactResponse] = Field(description="All conflicting facts")
    difference_description: str = Field(description="Explanation of the numerical difference")
    resolved: bool = Field(description="True if resolved via table-first hierarchy")
    resolved_fact_id: str | None = Field(default=None, description="Fact selected as authoritative")
    resolution_rationale: str | None = Field(default=None, description="Reasoning for resolution")


class GroundingValidationResultResponse(BaseModel):
    """Grounding audit assessment report."""

    status: str = Field(
        description="Overall grounding status ('grounded', 'partially_grounded', 'ungrounded', 'conflicting')"
    )
    total_claims: int = Field(description="Total claims evaluated")
    grounded_claims: int = Field(description="Number of grounded claims")
    ungrounded_claims: int = Field(description="Number of ungrounded claims")
    conflicting_claims: int = Field(description="Number of conflicting claims")
    unverified_citations: int = Field(description="Number of unverified citations")
    details: list[dict[str, Any]] = Field(
        default_factory=list, description="Claim-by-claim audit logs"
    )
    validation_passed: bool = Field(description="True if all claims are grounded")


class ReasoningQueryRequest(BaseModel):
    """Inquiry request payload for deterministic financial reasoning."""

    query: str = Field(
        min_length=2,
        max_length=2000,
        description="Financial inquiry text",
        examples=["What was Apple's revenue growth from 2023 to 2024?"],
    )
    filters: RetrievalFilterRequest | None = Field(
        default=None, description="Optional retrieval metadata filters"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Candidate evidence items retrieved from Phase 2",
    )
    use_reranker: bool = Field(
        default=True, description="Enable cross-encoder reranker in retrieval stage"
    )


class AnswerPackageResponse(BaseModel):
    """Complete Verified Answer Package containing facts, calculations, claims, and citations."""

    package_id: str = Field(description="Unique AnswerPackage identifier")
    query_id: str = Field(description="Inquiry correlation ID")
    raw_query: str = Field(description="Original user query")
    normalized_query: str = Field(description="Normalized query text")
    answerability: str = Field(
        description="Answerability state ('answerable', 'partially_answerable', 'insufficient_evidence', 'conflicting_evidence', 'calculation_failed', 'grounding_failed')"
    )
    answerability_rationale: str = Field(
        description="Diagnostic rationale for answerability status"
    )
    reasoning_plan: ReasoningPlanResponse = Field(description="Formulated reasoning plan")
    facts: list[FinancialFactResponse] = Field(description="Extracted and verified financial facts")
    calculations: list[CalculationResultResponse] = Field(
        description="Executed deterministic calculations"
    )
    reasoning_trace: list[ReasoningStepTraceResponse] = Field(
        description="Auditable reasoning step trace"
    )
    claims: list[ClaimResponse] = Field(description="Atomic verifiable claims")
    citations: list[CitationResponse] = Field(description="Verified source citations")
    evidence: list[RankedEvidenceResponse] = Field(
        description="Underlying retrieved evidence chunks"
    )
    conflicts: list[EvidenceConflictResponse] = Field(
        default_factory=list, description="Detected evidence conflicts"
    )
    missing_facts: list[str] = Field(
        default_factory=list, description="Identified missing required facts"
    )
    grounding_validation: GroundingValidationResultResponse | None = Field(
        default=None, description="Formal grounding verification audit report"
    )
    confidence_score: float = Field(description="Overall confidence score (0.0 - 1.0)")
    warnings: list[str] = Field(
        default_factory=list, description="System warnings or conflict notices"
    )
    execution_time_ms: dict[str, float] = Field(
        description="Latency breakdown by reasoning stage in milliseconds"
    )
    created_at: str = Field(description="Answer package UTC creation timestamp")


# ==========================================
# Phase 4 LLM Answer Orchestration Schemas
# ==========================================


class AnswerQueryRequest(BaseModel):
    """Inquiry request payload for verified LLM answer generation."""

    query: str = Field(
        min_length=2,
        max_length=2000,
        description="Financial inquiry text",
        examples=["What was Apple's revenue growth from 2023 to 2024?"],
    )
    response_style: str = Field(
        default="standard",
        description="Target response presentation style ('concise', 'standard', 'detailed', 'analytical')",
    )
    include_citations: bool = Field(
        default=True,
        description="Include structured source citations and footnotes in response",
    )
    citation_style: str = Field(
        default="bracketed",
        description="Citation marker format (e.g. 'bracketed' for [C1])",
    )
    filters: RetrievalFilterRequest | None = Field(
        default=None, description="Optional retrieval metadata filters"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of candidate evidence chunks to retrieve",
    )
    use_reranker: bool = Field(
        default=True,
        description="Enable cross-encoder reranker in retrieval stage",
    )
    custom_instructions: str | None = Field(
        default=None,
        max_length=500,
        description="Optional presentation instructions (cannot override factual accuracy or grounding)",
    )


class AnswerMetadataResponse(BaseModel):
    """Audit metadata recorded during answer synthesis."""

    model_name: str = Field(description="LLM model identifier used")
    prompt_version: str = Field(description="Prompt template version identifier")
    attempts: int = Field(description="Number of generation/validation attempts")
    used_fallback: bool = Field(description="True if safe deterministic fallback was utilized")
    cache_hit: bool = Field(default=False, description="True if served from cache")


class AnswerQueryResponse(BaseModel):
    """Complete verified answer synthesis response."""

    answer_id: str = Field(description="Unique answer identifier")
    query_id: str = Field(description="Inquiry correlation ID")
    status: str = Field(
        description="Terminal answer status ('completed', 'partially_answered', 'insufficient_evidence', 'conflicting_evidence', 'calculation_failed', 'grounding_failed', 'invalid_query')"
    )
    answer: str = Field(
        description="Synthesized natural language answer with verified citation markers"
    )
    claims: list[ClaimResponse] = Field(description="Atomic verifiable claims")
    citations: list[CitationResponse] = Field(
        description="Verified citations supporting the answer"
    )
    calculations: list[CalculationResultResponse] = Field(
        description="Deterministic calculations referenced"
    )
    facts: list[FinancialFactResponse] = Field(description="Underlying verified financial facts")
    reasoning_plan: ReasoningPlanResponse | None = Field(
        default=None, description="Formulated reasoning plan"
    )
    grounding_status: str = Field(
        description="Grounding audit status ('grounded', 'partially_grounded', 'ungrounded')"
    )
    confidence_score: float = Field(description="Overall confidence score (0.0 - 1.0)")
    warnings: list[str] = Field(
        default_factory=list, description="Caveats, warnings, or conflict notices"
    )
    metadata: AnswerMetadataResponse = Field(description="Audit and provenance metadata")
    execution_time_ms: dict[str, float] = Field(
        description="Execution latency breakdown in milliseconds"
    )
    created_at: str = Field(description="Answer generation UTC timestamp")


class AnswerStreamEventResponse(BaseModel):
    """Server-Sent Event envelope for progressive answer synthesis streaming."""

    sequence: int = Field(description="Sequential event counter")
    event_type: str = Field(
        description="Event type ('stage_start', 'reasoning_complete', 'token_delta', 'calculations', 'citations', 'validation_result', 'answer_complete', 'error')"
    )
    payload: dict[str, Any] = Field(description="Structured event payload")
    timestamp: str = Field(description="UTC event timestamp in ISO format")


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: str = Field(
        ..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address"
    )
    password: str = Field(..., min_length=8, description="Plaintext password (min 8 chars)")
    tenant_name: str | None = Field(default=None, description="Optional tenant organization name")
    role: UserRole = Field(default=UserRole.OWNER, description="Initial role for new registration")


class LoginRequest(BaseModel):
    """User login payload."""

    email: str = Field(
        ..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address"
    )
    password: str


class TokenResponse(BaseModel):
    """JWT access and refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int = 900
    user_id: str
    tenant_id: str
    role: str
    permissions: list[str]


class RefreshTokenRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str


class UserResponse(BaseModel):
    """Public user identity representation."""

    id: str
    tenant_id: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateUserRequest(BaseModel):
    """Admin user creation request within tenant organization."""

    email: str = Field(
        ..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address"
    )
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.MEMBER)


class UpdateUserStatusRequest(BaseModel):
    """Update user lifecycle status."""

    status: UserStatus


class AuditEventResponse(BaseModel):
    """Security and compliance audit event representation."""

    event_id: str
    timestamp: datetime
    tenant_id: str | None
    actor_user_id: str | None
    event_type: AuditEventType
    resource_type: str
    resource_id: str | None
    action: str
    outcome: str
    request_id: str | None
    trace_id: str | None
    source_ip: str | None
    user_agent: str | None
    metadata: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
