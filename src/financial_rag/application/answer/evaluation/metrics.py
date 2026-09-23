"""Evaluation data structures and calculation metrics for Phase 4 LLM Answer Orchestration."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AnswerEvaluationMetrics:
    """Quantitative performance metrics for answer synthesis and fidelity."""

    total_queries: int = 0
    successful_answers: int = 0
    faithfulness_score: float = 1.0
    numerical_fidelity_score: float = 1.0
    citation_preservation_score: float = 1.0
    grounding_preservation_score: float = 1.0
    refusal_correctness_score: float = 1.0
    style_compliance_score: float = 1.0
    fallback_rate: float = 0.0
    cache_hit_rate: float = 0.0
    average_latency_ms: float = 0.0


@dataclass
class AnswerEvaluationResult:
    """Comprehensive evaluation run summary."""

    run_id: str
    dataset_name: str
    metrics: AnswerEvaluationMetrics
    details: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
