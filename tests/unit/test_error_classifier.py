"""Unit tests for error classifier taxonomy and severity mapping."""

from financial_rag.domain.entities.observability import (
    ErrorSeverity,
    ErrorTaxonomyCategory,
)
from financial_rag.domain.exceptions import (
    CalculationError,
    GroundingValidationError,
    PromptInjectionDetectedError,
    StorageError,
    ValidationError,
)
from financial_rag.infrastructure.observability.error_classifier import ErrorClassifier


def test_classify_validation_error() -> None:
    rec = ErrorClassifier.classify(ValidationError("Field missing"))
    assert rec.category == ErrorTaxonomyCategory.VALIDATION_ERROR
    assert rec.severity == ErrorSeverity.LOW
    assert rec.recoverable is True


def test_classify_calculation_error() -> None:
    rec = ErrorClassifier.classify(
        CalculationError(operation="difference", message="Division impossible")
    )
    assert rec.category == ErrorTaxonomyCategory.CALCULATION_ERROR
    assert rec.severity == ErrorSeverity.MEDIUM


def test_classify_grounding_error() -> None:
    rec = ErrorClassifier.classify(GroundingValidationError(ungrounded_claim_ids=["claim-1"]))
    assert rec.category == ErrorTaxonomyCategory.GROUNDING_ERROR
    assert rec.severity == ErrorSeverity.HIGH


def test_classify_storage_error() -> None:
    rec = ErrorClassifier.classify(StorageError("Bucket connection timeout"))
    assert rec.category == ErrorTaxonomyCategory.DEPENDENCY_UNAVAILABLE
    assert rec.severity == ErrorSeverity.CRITICAL
    assert rec.recoverable is False


def test_classify_prompt_injection() -> None:
    rec = ErrorClassifier.classify(
        PromptInjectionDetectedError(source="document", pattern="ignore instructions")
    )
    assert rec.category == ErrorTaxonomyCategory.LLM_ERROR
    assert rec.severity == ErrorSeverity.HIGH
