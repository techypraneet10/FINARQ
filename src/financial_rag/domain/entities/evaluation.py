"""Domain entities for Phase 5 Evaluation, Benchmark Datasets, and Regression Engine."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from financial_rag.common.types import utc_now
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    GroundingStatus,
    ReasoningOperation,
)


class EvaluationCategory(StrEnum):
    """Evaluation test case categorization."""

    RETRIEVAL = "retrieval"
    NUMERICAL_REASONING = "numerical_reasoning"
    CITATION = "citation"
    GROUNDING = "grounding"
    HALLUCINATION = "hallucination"
    CONFLICT = "conflict"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MULTI_PERIOD = "multi_period"
    MULTI_DOCUMENT = "multi_document"
    QUALITATIVE = "qualitative"
    ADVERSARIAL_INJECTION = "adversarial_injection"
    TENANT_ISOLATION = "tenant_isolation"
    END_TO_END = "end_to_end"


class PipelineStage(StrEnum):
    """Pipeline boundary stages for diagnostic failure attribution."""

    INGESTION = "INGESTION"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    RETRIEVAL = "RETRIEVAL"
    RERANKING = "RERANKING"
    EVIDENCE = "EVIDENCE"
    CITATION = "CITATION"
    REASONING = "REASONING"
    LLM_GENERATION = "LLM_GENERATION"
    VALIDATION = "VALIDATION"
    API = "API"


class NumericalErrorType(StrEnum):
    """Granular error taxonomy for financial calculation failures."""

    NONE = "NONE"
    WRONG_OPERAND = "WRONG_OPERAND"
    WRONG_SIGN = "WRONG_SIGN"
    WRONG_SCALE = "WRONG_SCALE"
    WRONG_CURRENCY = "WRONG_CURRENCY"
    WRONG_PERIOD = "WRONG_PERIOD"
    WRONG_FORMULA = "WRONG_FORMULA"
    WRONG_RESULT = "WRONG_RESULT"
    MISSING_VALUE = "MISSING_VALUE"
    UNSUPPORTED_CALCULATION = "UNSUPPORTED_CALCULATION"


class RegressionSeverity(StrEnum):
    """Severity levels for detected performance or quality regressions."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ExpectedFact:
    """Expected financial fact in an evaluation case."""

    metric: str
    company: str | None = None
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    expected_value: str | None = None
    scale: str | None = None
    currency: str = "USD"


@dataclass(frozen=True)
class ExpectedCalculation:
    """Expected mathematical calculation in an evaluation case."""

    operation: ReasoningOperation
    expected_result_str: str
    tolerance_pct: float = 0.01  # Default 1% tolerance for floating/rounding variations
    expected_formula: str | None = None


@dataclass(frozen=True)
class EvaluationCase:
    """A single comprehensive gold-standard evaluation test case."""

    case_id: str
    category: EvaluationCategory
    query: str
    dataset_version: str = "financial_rag_eval_v1"
    expected_answerability: AnswerabilityStatus = AnswerabilityStatus.ANSWERABLE
    expected_document_ids: list[str] = field(default_factory=list)
    expected_page_numbers: list[int] = field(default_factory=list)
    expected_chunk_ids: list[str] = field(default_factory=list)
    expected_facts: list[ExpectedFact] = field(default_factory=list)
    expected_calculations: list[ExpectedCalculation] = field(default_factory=list)
    expected_citations_count: int = 1
    expected_grounding_status: GroundingStatus = GroundingStatus.GROUNDED
    expected_answer_contains: list[str] = field(default_factory=list)
    forbidden_answer_contains: list[str] = field(default_factory=list)
    is_adversarial: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationDataset:
    """A versioned collection of evaluation test cases."""

    dataset_version: str
    description: str
    cases: list[EvaluationCase]
    created_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_cases_by_category(self, category: EvaluationCategory) -> list[EvaluationCase]:
        """Filter test cases by category."""
        return [c for c in self.cases if c.category == category]


# ============================================================
# Layer-Specific Evaluation Metrics
# ============================================================


@dataclass
class RetrievalEvalMetrics:
    """Retrieval quality and ranking metrics."""

    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    hit_rate_at_1: float = 0.0
    hit_rate_at_3: float = 0.0
    hit_rate_at_5: float = 0.0
    hit_rate_at_10: float = 0.0
    mrr: float = 0.0
    map_score: float = 0.0
    ndcg_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    strategy: str = "hybrid"
    mean_latency_ms: float = 0.0


@dataclass
class FactExtractionEvalMetrics:
    """Fact extraction precision, recall, and exact match."""

    exact_match: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    value_accuracy: float = 0.0
    scale_accuracy: float = 0.0
    period_accuracy: float = 0.0


@dataclass
class NumericalReasoningEvalMetrics:
    """Deterministic mathematical correctness metrics."""

    calculation_accuracy: float = 1.0
    formula_accuracy: float = 1.0
    rounding_accuracy: float = 1.0
    zero_division_safety: float = 1.0
    unit_consistency: float = 1.0


@dataclass
class CitationEvalMetrics:
    """Citation precision, recall, and provenance validity metrics."""

    citation_precision: float = 1.0
    citation_recall: float = 1.0
    citation_validity: float = 1.0
    citation_completeness: float = 1.0


@dataclass
class GroundingEvalMetrics:
    """Evidence grounding and unsupported claim metrics."""

    grounded_answer_rate: float = 1.0
    unsupported_claim_rate: float = 0.0
    grounding_failure_rate: float = 0.0


@dataclass
class AnswerEvalMetrics:
    """End-to-end natural-language answer synthesis metrics."""

    faithfulness_score: float = 1.0
    numerical_fidelity_score: float = 1.0
    refusal_correctness_score: float = 1.0
    prompt_injection_resistance_score: float = 1.0
    style_compliance_score: float = 1.0
    fallback_utilization_rate: float = 0.0


@dataclass
class LatencyEvalMetrics:
    """Pipeline latency measurements across percentile distributions."""

    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    mean_total_ms: float = 0.0
    stage_breakdowns_ms: dict[str, float] = field(default_factory=dict)


@dataclass
class CostEvalMetrics:
    """LLM token and cost telemetry."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    cost_per_query_usd: float = 0.0


@dataclass
class EvidenceEvalMetrics:
    """Evidence selection and multi-source coverage metrics."""

    evidence_recall: float = 1.0
    evidence_precision: float = 1.0
    required_source_coverage: float = 1.0
    table_source_coverage: float = 1.0
    multi_source_coverage: float = 1.0


@dataclass
class SecurityEvalMetrics:
    """Adversarial security, prompt injection defense, and tenant isolation metrics."""

    prompt_injection_resistance_rate: float = 1.0
    system_prompt_leakage_rate: float = 0.0
    tenant_isolation_violation_rate: float = 0.0
    safe_handling_rate: float = 1.0


@dataclass
class FailureAttribution:
    """Diagnostic attribution of an evaluation case failure to the first failed pipeline stage."""

    case_id: str
    first_failed_stage: PipelineStage
    error_type: str
    severity: RegressionSeverity = RegressionSeverity.WARNING
    details: str = ""
    recommendation: str = ""


@dataclass
class EvaluationScorecard:
    """Consolidated multi-level evaluation scorecard."""

    evaluation_run_id: str
    dataset_version: str
    total_cases: int
    successful_cases: int
    retrieval: RetrievalEvalMetrics = field(default_factory=RetrievalEvalMetrics)
    evidence: EvidenceEvalMetrics = field(default_factory=EvidenceEvalMetrics)
    fact_extraction: FactExtractionEvalMetrics = field(default_factory=FactExtractionEvalMetrics)
    numerical_reasoning: NumericalReasoningEvalMetrics = field(
        default_factory=NumericalReasoningEvalMetrics
    )
    citations: CitationEvalMetrics = field(default_factory=CitationEvalMetrics)
    grounding: GroundingEvalMetrics = field(default_factory=GroundingEvalMetrics)
    answer: AnswerEvalMetrics = field(default_factory=AnswerEvalMetrics)
    security: SecurityEvalMetrics = field(default_factory=SecurityEvalMetrics)
    latency: LatencyEvalMetrics = field(default_factory=LatencyEvalMetrics)
    cost: CostEvalMetrics = field(default_factory=CostEvalMetrics)
    failures: list[FailureAttribution] = field(default_factory=list)
    composite_score: float = 1.0
    created_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# Regression & Quality Gate Models
# ============================================================


@dataclass(frozen=True)
class RegressionItem:
    """A detected metric regression against baseline."""

    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    threshold: float
    severity: RegressionSeverity
    details: str = ""


@dataclass
class RegressionReport:
    """Comprehensive regression audit comparing run against baseline."""

    run_id: str
    baseline_id: str
    has_regressions: bool
    regressions: list[RegressionItem] = field(default_factory=list)
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class BaselineRecord:
    """Immutable record of an approved baseline evaluation run."""

    baseline_id: str
    run_id: str
    dataset_version: str
    scorecard: EvaluationScorecard
    prompt_version: str
    model_name: str
    created_at: datetime = field(default_factory=utc_now)
    approved_by: str = "system"


@dataclass(frozen=True)
class QualityGateRule:
    """Rule defining a hard quality constraint for CI."""

    metric_name: str
    target_value: float
    comparator: str  # '>=', '<=', '==', '>'
    severity: RegressionSeverity = RegressionSeverity.CRITICAL


@dataclass
class QualityGateResult:
    """Result of evaluating CI quality gates."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    evaluated_rules: int = 0
    run_id: str = ""
    timestamp: datetime = field(default_factory=utc_now)
