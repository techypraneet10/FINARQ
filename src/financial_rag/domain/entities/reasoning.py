"""Domain entities and value objects for deterministic financial reasoning and grounding.

These models represent structured facts, normalized Decimal financial values,
fiscal periods, deterministic calculations, claims, verifiable citations,
grounding validation results, and the verified AnswerPackage.
Zero dependencies on external frameworks, databases, or LLMs.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from financial_rag.common.types import (
    CitationId,
    DocumentId,
    QueryId,
    TableId,
    VersionId,
)
from financial_rag.domain.entities.retrieval import RankedEvidence


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class AnswerabilityStatus(StrEnum):
    """Explicit answerability classification state for financial inquiries."""

    ANSWERABLE = "answerable"
    PARTIALLY_ANSWERABLE = "partially_answerable"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    INVALID_QUERY = "invalid_query"
    CALCULATION_FAILED = "calculation_failed"
    GROUNDING_FAILED = "grounding_failed"


class GroundingStatus(StrEnum):
    """Grounding validation outcome status across all claims in the package."""

    GROUNDED = "grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    UNGROUNDED = "ungrounded"
    CONFLICTING = "conflicting"


class ReasoningOperation(StrEnum):
    """Supported deterministic financial reasoning and arithmetic operations."""

    DIRECT_LOOKUP = "direct_lookup"
    COMPARISON = "comparison"
    DIFFERENCE = "difference"
    PERCENTAGE_CHANGE = "percentage_change"
    GROWTH_RATE = "growth_rate"
    RATIO = "ratio"
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    TREND = "trend"
    MULTI_PERIOD_COMPARISON = "multi_period_comparison"


class FinancialScale(StrEnum):
    """Magnitude multiplier scale for monetary and numerical quantities."""

    EXACT = "exact"  # 1.0
    THOUSANDS = "thousands"  # 1,000
    MILLIONS = "millions"  # 1,000,000
    BILLIONS = "billions"  # 1,000,000,000
    TRILLIONS = "trillions"  # 1,000,000,000,000
    PERCENT = "percent"  # 0.01

    @property
    def multiplier(self) -> Decimal:
        """Return exact Decimal multiplier corresponding to this scale."""
        if self == FinancialScale.THOUSANDS:
            return Decimal("1000")
        if self == FinancialScale.MILLIONS:
            return Decimal("1000000")
        if self == FinancialScale.BILLIONS:
            return Decimal("1000000000")
        if self == FinancialScale.TRILLIONS:
            return Decimal("1000000000000")
        if self == FinancialScale.PERCENT:
            return Decimal("0.01")
        return Decimal("1")


class CitationType(StrEnum):
    """Structural category of verifiable citation."""

    DIRECT_SOURCE = "direct_source"
    CALCULATION_SOURCE = "calculation_source"
    MULTI_SOURCE = "multi_source"
    TABLE_CELL = "table_cell"


@dataclass(frozen=True)
class FiscalPeriod:
    """Normalized representation of a financial reporting period."""

    fiscal_year: int | None
    period_type: str = "FY"  # e.g., "FY", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "TTM", "MONTH"
    source_text: str = ""
    start_date: str | None = None
    end_date: str | None = None
    is_uncertain: bool = False

    @property
    def label(self) -> str:
        """Formatted human-readable period label (e.g. 'FY2024' or 'Q1 2024')."""
        if self.fiscal_year is None:
            return self.source_text or "Unknown Period"
        if self.period_type in ("FY", "Full Year"):
            return f"FY{self.fiscal_year}"
        return f"{self.period_type} {self.fiscal_year}"

    def to_dict(self) -> dict[str, Any]:
        """Convert period to dictionary representation."""
        return {
            "fiscal_year": self.fiscal_year,
            "period_type": self.period_type,
            "source_text": self.source_text,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_uncertain": self.is_uncertain,
            "label": self.label,
        }


@dataclass(frozen=True)
class FinancialValue:
    """High-precision structured financial quantity with raw, display, and Decimal representations."""

    raw_value: str
    display_value: str
    numeric_value: Decimal  # Fully scaled exact Decimal (e.g., 391000000000)
    unscaled_value: Decimal  # Pre-scale value (e.g., 391.0)
    currency: str | None = "USD"
    scale: FinancialScale = FinancialScale.EXACT
    unit: str = "USD"
    is_negative: bool = False
    is_percentage: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert financial value to serializable dictionary."""
        return {
            "raw_value": self.raw_value,
            "display_value": self.display_value,
            "numeric_value": str(self.numeric_value),
            "unscaled_value": str(self.unscaled_value),
            "currency": self.currency,
            "scale": self.scale.value,
            "unit": self.unit,
            "is_negative": self.is_negative,
            "is_percentage": self.is_percentage,
        }


@dataclass(frozen=True)
class FinancialFact:
    """An extracted, normalized, grounded atomic financial data point."""

    fact_id: str
    metric: str
    value: FinancialValue
    period: FiscalPeriod
    company: str | None
    ticker: str | None
    document_id: DocumentId
    document_version_id: VersionId
    page_number: int
    chunk_id: str
    table_id: TableId | None
    source_evidence_id: str
    extraction_method: str  # e.g., "table_cell", "table_structured", "narrative_regex"
    confidence: float
    source_text: str
    tenant_id: str = "default_tenant"
    bounding_box: dict[str, float] | None = None
    section_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert fact to serializable dictionary representation."""
        return {
            "fact_id": self.fact_id,
            "metric": self.metric,
            "value": self.value.to_dict(),
            "period": self.period.to_dict(),
            "company": self.company,
            "ticker": self.ticker,
            "document_id": str(self.document_id),
            "document_version_id": str(self.document_version_id),
            "tenant_id": self.tenant_id,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id,
            "table_id": str(self.table_id) if self.table_id else None,
            "source_evidence_id": self.source_evidence_id,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "source_text": self.source_text,
            "bounding_box": self.bounding_box,
            "section_path": self.section_path,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CalculationInput:
    """Input operand for a deterministic financial calculation."""

    name: str
    value: Decimal
    fact_id: str | None = None
    source_description: str = ""
    unit: str = ""
    currency: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert calculation input to dictionary."""
        return {
            "name": self.name,
            "value": str(self.value),
            "fact_id": self.fact_id,
            "source_description": self.source_description,
            "unit": self.unit,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class CalculationResult:
    """Deterministic calculation execution result with complete auditability."""

    calculation_id: str
    operation: ReasoningOperation
    formula: str
    inputs: list[CalculationInput]
    input_fact_ids: list[str]
    raw_result: Decimal
    rounded_result: Decimal
    display_result: str
    unit: str
    currency: str | None
    rounding_precision: int = 2
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert calculation result to serializable dictionary."""
        return {
            "calculation_id": self.calculation_id,
            "operation": self.operation.value,
            "formula": self.formula,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "input_fact_ids": self.input_fact_ids,
            "raw_result": str(self.raw_result),
            "rounded_result": str(self.rounded_result),
            "display_result": self.display_result,
            "unit": self.unit,
            "currency": self.currency,
            "rounding_precision": self.rounding_precision,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class ReasoningPlan:
    """Explicit declarative reasoning plan generated from query intent and signals."""

    plan_id: str
    query: str
    operations: list[ReasoningOperation]
    target_metrics: list[str]
    target_periods: list[str]
    target_companies: list[str]
    required_fact_keys: list[str]
    steps_description: list[str]
    is_multi_period: bool = False
    is_comparison: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert reasoning plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "query": self.query,
            "operations": [op.value for op in self.operations],
            "target_metrics": self.target_metrics,
            "target_periods": self.target_periods,
            "target_companies": self.target_companies,
            "required_fact_keys": self.required_fact_keys,
            "steps_description": self.steps_description,
            "is_multi_period": self.is_multi_period,
            "is_comparison": self.is_comparison,
        }


@dataclass(frozen=True)
class ReasoningStepTrace:
    """Individual auditable step in the executed reasoning trace."""

    step_number: int
    operation: ReasoningOperation
    description: str
    input_fact_ids: list[str]
    calculation_id: str | None
    output_summary: str
    status: str = "success"

    def to_dict(self) -> dict[str, Any]:
        """Convert step trace to dictionary."""
        return {
            "step_number": self.step_number,
            "operation": self.operation.value,
            "description": self.description,
            "input_fact_ids": self.input_fact_ids,
            "calculation_id": self.calculation_id,
            "output_summary": self.output_summary,
            "status": self.status,
        }


@dataclass(frozen=True)
class Claim:
    """Atomic factual or calculated statement backed by grounding evidence."""

    claim_id: str
    text: str
    claim_type: str  # e.g., "direct_fact", "calculated", "comparison", "trend"
    source_fact_ids: list[str]
    calculation_ids: list[str]
    reasoning_step_ids: list[int]
    tenant_id: str = "default_tenant"
    confidence: float = 1.0
    is_grounded: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert claim to dictionary representation."""
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type,
            "source_fact_ids": self.source_fact_ids,
            "calculation_ids": self.calculation_ids,
            "reasoning_step_ids": self.reasoning_step_ids,
            "tenant_id": self.tenant_id,
            "confidence": self.confidence,
            "is_grounded": self.is_grounded,
        }


@dataclass(frozen=True)
class Citation:
    """Verifiable source citation pointing to specific document, page, chunk, or table."""

    citation_id: CitationId
    claim_id: str
    document_id: DocumentId
    document_version_id: VersionId
    page_number: int
    page_numbers: list[int]
    chunk_id: str
    table_id: TableId | None
    section_path: str
    ticker: str | None
    source_excerpt: str
    bounding_box: dict[str, float] | None
    citation_type: CitationType
    tenant_id: str = "default_tenant"
    verified: bool = False
    validation_notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert citation to dictionary representation."""
        return {
            "citation_id": str(self.citation_id),
            "claim_id": self.claim_id,
            "document_id": str(self.document_id),
            "document_version_id": str(self.document_version_id),
            "tenant_id": self.tenant_id,
            "page_number": self.page_number,
            "page_numbers": self.page_numbers,
            "chunk_id": self.chunk_id,
            "table_id": str(self.table_id) if self.table_id else None,
            "section_path": self.section_path,
            "ticker": self.ticker,
            "source_excerpt": self.source_excerpt,
            "bounding_box": self.bounding_box,
            "citation_type": self.citation_type.value,
            "verified": self.verified,
            "validation_notes": self.validation_notes,
        }


@dataclass(frozen=True)
class EvidenceConflict:
    """Detected numerical or structural conflict between multiple evidence sources."""

    conflict_id: str
    metric: str
    period: str
    conflicting_facts: list[FinancialFact]
    difference_description: str
    resolved: bool = False
    resolved_fact_id: str | None = None
    resolution_rationale: str | None = None
    tenant_id: str = "default_tenant"

    def to_dict(self) -> dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "conflict_id": self.conflict_id,
            "metric": self.metric,
            "period": self.period,
            "conflicting_facts": [f.to_dict() for f in self.conflicting_facts],
            "difference_description": self.difference_description,
            "resolved": self.resolved,
            "resolved_fact_id": self.resolved_fact_id,
            "resolution_rationale": self.resolution_rationale,
            "tenant_id": self.tenant_id,
        }


@dataclass(frozen=True)
class GroundingValidationResult:
    """Grounding validation scorecard verifying claim-evidence alignment."""

    status: GroundingStatus
    total_claims: int
    grounded_claims: int
    ungrounded_claims: int
    conflicting_claims: int
    unverified_citations: int
    details: list[dict[str, Any]] = field(default_factory=list)
    validation_passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "status": self.status.value,
            "total_claims": self.total_claims,
            "grounded_claims": self.grounded_claims,
            "ungrounded_claims": self.ungrounded_claims,
            "conflicting_claims": self.conflicting_claims,
            "unverified_citations": self.unverified_citations,
            "details": self.details,
            "validation_passed": self.validation_passed,
        }


@dataclass(frozen=True)
class AnswerPackage:
    """Verified, grounded answer container ready for downstream consumption.

    Contains extracted facts, normalized Decimal quantities, deterministic calculations,
    explicit reasoning traces, evidence-backed claims, verifiable citations,
    and grounding validation audits.
    """

    package_id: str
    query_id: QueryId
    raw_query: str
    normalized_query: str
    answerability: AnswerabilityStatus
    answerability_rationale: str
    reasoning_plan: ReasoningPlan
    facts: list[FinancialFact]
    calculations: list[CalculationResult]
    reasoning_trace: list[ReasoningStepTrace]
    claims: list[Claim]
    citations: list[Citation]
    evidence: list[RankedEvidence]
    tenant_id: str = "default_tenant"
    conflicts: list[EvidenceConflict] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    grounding_validation: GroundingValidationResult | None = None
    confidence_score: float = 1.0
    warnings: list[str] = field(default_factory=list)
    execution_time_ms: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Convert AnswerPackage to serializable dictionary representation."""
        return {
            "package_id": self.package_id,
            "query_id": str(self.query_id),
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "tenant_id": self.tenant_id,
            "answerability": self.answerability.value,
            "answerability_rationale": self.answerability_rationale,
            "reasoning_plan": self.reasoning_plan.to_dict(),
            "facts": [f.to_dict() for f in self.facts],
            "calculations": [c.to_dict() for c in self.calculations],
            "reasoning_trace": [t.to_dict() for t in self.reasoning_trace],
            "claims": [cl.to_dict() for cl in self.claims],
            "citations": [cit.to_dict() for cit in self.citations],
            "evidence": [ev.to_dict() for ev in self.evidence],
            "conflicts": [cf.to_dict() for cf in self.conflicts],
            "missing_facts": self.missing_facts,
            "grounding_validation": (
                self.grounding_validation.to_dict() if self.grounding_validation else None
            ),
            "confidence_score": self.confidence_score,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat(),
        }
