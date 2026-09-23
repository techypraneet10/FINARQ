"""Domain interface contracts for Phase 5 Evaluation and Regression Engine."""

from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.answer import AnswerResponse
from financial_rag.domain.entities.evaluation import (
    AnswerEvalMetrics,
    BaselineRecord,
    CitationEvalMetrics,
    EvaluationCase,
    EvaluationDataset,
    EvaluationScorecard,
    EvidenceEvalMetrics,
    FactExtractionEvalMetrics,
    FailureAttribution,
    GroundingEvalMetrics,
    NumericalReasoningEvalMetrics,
    QualityGateResult,
    QualityGateRule,
    RegressionReport,
    RetrievalEvalMetrics,
    SecurityEvalMetrics,
)
from financial_rag.domain.entities.models import RetrievalResult
from financial_rag.domain.entities.reasoning import AnswerPackage


@runtime_checkable
class DatasetLoaderProtocol(Protocol):
    """Protocol for loading and validating benchmark evaluation datasets."""

    def load_dataset(self, dataset_version: str) -> EvaluationDataset:
        """Load dataset by version string."""
        ...

    def list_available_datasets(self) -> list[str]:
        """List available dataset versions."""
        ...


@runtime_checkable
class RetrievalEvaluatorProtocol(Protocol):
    """Protocol for evaluating retrieval candidate quality."""

    def evaluate_retrieval(
        self,
        retrieved_items: list[RetrievalResult],
        ground_truth_chunks: list[str],
        ground_truth_pages: list[int] | None = None,
        strategy: str = "hybrid",
        latency_ms: float = 0.0,
    ) -> RetrievalEvalMetrics:
        """Compute retrieval metrics for candidate list."""
        ...


@runtime_checkable
class ReasoningEvaluatorProtocol(Protocol):
    """Protocol for evaluating fact extraction and deterministic arithmetic."""

    def evaluate_fact_extraction(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> FactExtractionEvalMetrics:
        """Compute fact extraction accuracy."""
        ...

    def evaluate_numerical_reasoning(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> NumericalReasoningEvalMetrics:
        """Compute numerical calculation correctness."""
        ...


@runtime_checkable
class CitationEvaluatorProtocol(Protocol):
    """Protocol for evaluating citation precision, recall, and validity."""

    def evaluate_citations(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> CitationEvalMetrics:
        """Compute citation fidelity metrics."""
        ...


@runtime_checkable
class GroundingEvaluatorProtocol(Protocol):
    """Protocol for evaluating evidence grounding integrity."""

    def evaluate_grounding(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> GroundingEvalMetrics:
        """Compute grounding rates."""
        ...


@runtime_checkable
class AnswerEvaluatorProtocol(Protocol):
    """Protocol for evaluating final synthesized answer quality."""

    def evaluate_answer(
        self,
        response: AnswerResponse,
        case: EvaluationCase,
    ) -> AnswerEvalMetrics:
        """Compute natural language answer metrics."""
        ...


@runtime_checkable
class RegressionDetectorProtocol(Protocol):
    """Protocol for detecting quality regressions against baseline."""

    def detect_regressions(
        self,
        current_scorecard: EvaluationScorecard,
        baseline: BaselineRecord,
        thresholds: dict[str, float] | None = None,
    ) -> RegressionReport:
        """Compare scorecard against baseline snapshot."""
        ...


@runtime_checkable
class BaselineStoreProtocol(Protocol):
    """Protocol for reading and persisting evaluation baselines."""

    def get_baseline(self, dataset_version: str) -> BaselineRecord | None:
        """Retrieve active baseline for dataset."""
        ...

    def save_baseline(self, baseline: BaselineRecord) -> None:
        """Persist new baseline record."""
        ...


@runtime_checkable
class QualityGateProtocol(Protocol):
    """Protocol for evaluating CI quality gates."""

    def evaluate_gates(
        self,
        scorecard: EvaluationScorecard,
        regression_report: RegressionReport | None = None,
        custom_rules: list[QualityGateRule] | None = None,
    ) -> QualityGateResult:
        """Evaluate scorecard against CI quality gate rules."""
        ...


@runtime_checkable
class ReportFormatterProtocol(Protocol):
    """Protocol for formatting evaluation scorecards and regression reports."""

    def format_json(
        self, scorecard: EvaluationScorecard, regression: RegressionReport | None = None
    ) -> str:
        """Format as machine-readable JSON."""
        ...

    def format_markdown(
        self, scorecard: EvaluationScorecard, regression: RegressionReport | None = None
    ) -> str:
        """Format as human-readable Markdown."""
        ...

    def format_csv(self, scorecard: EvaluationScorecard) -> str:
        """Format as tabular CSV."""
        ...


@runtime_checkable
class EvidenceEvaluatorProtocol(Protocol):
    """Protocol for evaluating evidence selection quality and coverage."""

    def evaluate_evidence(
        self,
        selected_evidence: list[Any],
        ground_truth_chunks: list[str],
        ground_truth_pages: list[int] | None = None,
        expected_table_id: str | None = None,
    ) -> EvidenceEvalMetrics:
        """Compute evidence selection quality and multi-source coverage."""
        ...


@runtime_checkable
class SecurityEvaluatorProtocol(Protocol):
    """Protocol for evaluating prompt injection defense and multi-tenant isolation."""

    def evaluate_security(
        self,
        response: AnswerResponse,
        case: EvaluationCase,
        tenant_context: str = "default_tenant",
    ) -> SecurityEvalMetrics:
        """Compute adversarial resistance and tenant boundary isolation metrics."""
        ...


@runtime_checkable
class FailureAttributionProtocol(Protocol):
    """Protocol for attributing test case failures to specific pipeline boundary stages."""

    def attribute_failure(
        self,
        case: EvaluationCase,
        answer_package: AnswerPackage | None,
        answer_response: AnswerResponse | None,
        retrieved_items: list[RetrievalResult] | None = None,
        error_exception: Exception | None = None,
    ) -> FailureAttribution | None:
        """Diagnose and return the earliest failing pipeline stage."""
        ...
