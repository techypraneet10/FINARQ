"""Evaluation framework for financial reasoning, calculations, citations, and grounding."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class ReasoningMetrics:
    """Arithmetic and reasoning performance metrics."""

    exact_match_accuracy: float = 1.0
    arithmetic_error_rate: float = 0.0
    unsupported_operation_rate: float = 0.0
    division_by_zero_handled_rate: float = 1.0
    average_latency_ms: float = 0.0


@dataclass
class CitationMetrics:
    """Citation provenance fidelity metrics."""

    citation_precision: float = 1.0
    citation_recall: float = 1.0
    unverified_citation_rate: float = 0.0
    page_level_accuracy: float = 1.0


@dataclass
class GroundingMetrics:
    """Claim-to-evidence grounding integrity metrics."""

    fully_grounded_rate: float = 1.0
    ungrounded_claim_rate: float = 0.0
    conflicting_claim_rate: float = 0.0


@dataclass
class ReasoningEvaluationSample:
    """A benchmark query with expected ground truth facts, calculations, and answerability."""

    query: str
    expected_answerability: str
    expected_metrics: list[str] = field(default_factory=list)
    expected_periods: list[str] = field(default_factory=list)
    expected_calculation_result: str | None = None
    expected_grounded: bool = True
    must_detect_conflict: bool = False


@dataclass
class ReasoningEvaluationResult:
    """Summary metrics evaluating the performance of the financial reasoning engine."""

    total_queries: int = 0
    answerable_queries: int = 0
    unanswerable_queries: int = 0
    reasoning_metrics: ReasoningMetrics = field(default_factory=ReasoningMetrics)
    citation_metrics: CitationMetrics = field(default_factory=CitationMetrics)
    grounding_metrics: GroundingMetrics = field(default_factory=GroundingMetrics)
    failures: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "answerable_queries": self.answerable_queries,
            "unanswerable_queries": self.unanswerable_queries,
            "reasoning_accuracy": round(self.reasoning_metrics.exact_match_accuracy, 4),
            "citation_precision": round(self.citation_metrics.citation_precision, 4),
            "fully_grounded_rate": round(self.grounding_metrics.fully_grounded_rate, 4),
            "failure_count": len(self.failures),
            "failures": self.failures,
            "created_at": self.created_at.isoformat(),
        }
