"""Domain interfaces (architectural protocols) for deterministic financial reasoning.

These contracts decouple fact extraction, period normalization, value parsing,
deterministic calculations, conflict detection, claim generation, citation mapping,
grounding verification, and answerability evaluation from concrete implementations.
"""

from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    CalculationResult,
    Citation,
    Claim,
    EvidenceConflict,
    FinancialFact,
    FinancialValue,
    FiscalPeriod,
    GroundingValidationResult,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.domain.entities.retrieval import RankedEvidence, RetrievalQuery


@runtime_checkable
class FinancialValueParserProtocol(Protocol):
    """Contract for parsing monetary strings, scales, units, and parenthetical negatives into FinancialValue."""

    def parse(
        self,
        raw_str: str,
        context_units: str = "",
        context_currency: str = "USD",
        context_scale: float = 1.0,
    ) -> FinancialValue | None:
        """Parse raw string into structured Decimal-based FinancialValue."""
        ...

    def detect_currency(self, text: str, default: str = "USD") -> str:
        """Detect currency from string or context."""
        ...

    def detect_scale_from_text(self, text: str) -> Any:
        """Detect scale multiplier from text descriptors."""
        ...


@runtime_checkable
class PeriodNormalizerProtocol(Protocol):
    """Contract for normalizing temporal reporting period descriptions into FiscalPeriod."""

    def normalize(
        self,
        raw_period: str,
        default_year: int | None = None,
    ) -> FiscalPeriod:
        """Normalize period string (e.g. 'FY2024', 'Q3 2023', 'Three months ended March 31') into FiscalPeriod."""
        ...


@runtime_checkable
class FactExtractorProtocol(Protocol):
    """Contract for extracting structured FinancialFact instances from retrieved evidence."""

    def extract_facts(
        self,
        evidence_items: list[RankedEvidence],
    ) -> list[FinancialFact]:
        """Extract structured financial facts with provenance from table and text evidence."""
        ...


@runtime_checkable
class FinancialCalculatorProtocol(Protocol):
    """Contract for safe deterministic financial arithmetic over Decimal quantities."""

    def execute(
        self,
        operation: ReasoningOperation,
        facts: list[FinancialFact],
        company_override: str | None = None,
    ) -> CalculationResult:
        """Execute deterministic arithmetic without eval/exec and return auditable result."""
        ...


@runtime_checkable
class ReasoningPlannerProtocol(Protocol):
    """Contract for analyzing query intent and planning required operations and target facts."""

    def plan(
        self,
        query: RetrievalQuery,
    ) -> ReasoningPlan:
        """Generate structured reasoning plan for the inquiry."""
        ...


@runtime_checkable
class ConflictDetectorProtocol(Protocol):
    """Contract for discovering and resolving numerical and factual conflicts across evidence sources."""

    def detect_conflicts(
        self,
        facts: list[FinancialFact],
    ) -> list[EvidenceConflict]:
        """Identify conflicting factual values for identical metric/period/entity combinations."""
        ...


@runtime_checkable
class ClaimBuilderProtocol(Protocol):
    """Contract for constructing verifiable Claim statements from facts and calculation results."""

    def build_claims(
        self,
        plan: ReasoningPlan,
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
    ) -> list[Claim]:
        """Build atomic verifiable claims backed by fact and calculation IDs."""
        ...


@runtime_checkable
class CitationGeneratorProtocol(Protocol):
    """Contract for deterministically generating verifiable Citation objects from fact provenance."""

    def generate_citations(
        self,
        claims: list[Claim],
        facts: list[FinancialFact],
        evidence_items: list[RankedEvidence],
    ) -> list[Citation]:
        """Generate citations linking claims and supporting facts back to exact document chunks."""
        ...


@runtime_checkable
class CitationValidatorProtocol(Protocol):
    """Contract for validating citations against the retrieved evidence pool."""

    def validate_citations(
        self,
        citations: list[Citation],
        evidence_items: list[RankedEvidence],
    ) -> list[Citation]:
        """Verify that citations match valid chunks, pages, and excerpts in evidence."""
        ...


@runtime_checkable
class GroundingValidatorProtocol(Protocol):
    """Contract for validating that all claims are backed by unbroken evidence and calculation chains."""

    def validate(
        self,
        claims: list[Claim],
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
        citations: list[Citation],
        conflicts: list[EvidenceConflict],
    ) -> GroundingValidationResult:
        """Audit the entire grounding graph and evaluate overall GroundingStatus."""
        ...


@runtime_checkable
class AnswerabilityEvaluatorProtocol(Protocol):
    """Contract for classifying answerability status based on evidence sufficiency and validity."""

    def evaluate(
        self,
        plan: ReasoningPlan,
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
        conflicts: list[EvidenceConflict],
        grounding: GroundingValidationResult,
    ) -> tuple[AnswerabilityStatus, str, list[str]]:
        """Evaluate AnswerabilityStatus, rationale, and list of missing required facts."""
        ...


@runtime_checkable
class ReasoningServiceProtocol(Protocol):
    """Contract for the end-to-end reasoning application service producing verified AnswerPackages."""

    async def reason(
        self,
        raw_query: str,
        top_k: int = 10,
        filters: Any = None,
        use_reranker: bool = True,
    ) -> AnswerPackage:
        """Execute full retrieval, fact extraction, reasoning, grounding, and AnswerPackage construction."""
        ...
