"""Error classification and taxonomy mapping for platform reliability."""

from financial_rag.domain.entities.observability import (
    ErrorRecord,
    ErrorSeverity,
    ErrorTaxonomyCategory,
)
from financial_rag.domain.exceptions import (
    AnswerGenerationError,
    AnswerValidationError,
    CalculationError,
    ChunkingError,
    CitationMarkerError,
    ConfigurationError,
    ConflictingEvidenceError,
    DatabaseError,
    DivisionByZeroError,
    DocumentParsingError,
    DuplicateDocumentError,
    EmbeddingProviderError,
    ExternalServiceError,
    FileValidationError,
    GroundingValidationError,
    IncompatibleCompanyError,
    IncompatibleCurrencyError,
    IncompatibleEmbeddingError,
    IncompatiblePeriodError,
    IncompatibleUnitsError,
    IndexingError,
    IngestionPipelineError,
    InsufficientEvidenceError,
    InvalidCitationError,
    InvalidEvidenceError,
    LLMOutputFormatError,
    LLMProviderError,
    LLMTimeoutError,
    NumericalFidelityError,
    OCRError,
    PromptInjectionDetectedError,
    ReasoningError,
    RerankerError,
    RetrievalError,
    SparseIndexError,
    StorageError,
    TableExtractionError,
    UnsupportedClaimError,
    ValidationError,
    VectorStoreError,
)


class ErrorClassifier:
    """Classifies application exceptions into the standardized universal error taxonomy."""

    @staticmethod
    def classify(
        exception: Exception,
        trace_id: str | None = None,
        request_id: str | None = None,
    ) -> ErrorRecord:
        """Classify an exception into structured ErrorRecord."""
        msg = str(exception)
        details = getattr(exception, "details", {})
        code = getattr(exception, "code", type(exception).__name__)

        # Match specific exception types
        if isinstance(exception, (FileValidationError, ValidationError)):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.VALIDATION_ERROR,
                code=code,
                severity=ErrorSeverity.LOW,
                recoverable=True,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception,
            (
                DocumentParsingError,
                OCRError,
                ChunkingError,
                TableExtractionError,
                IngestionPipelineError,
                DuplicateDocumentError,
            ),
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.INGESTION_ERROR,
                code=code,
                severity=ErrorSeverity.MEDIUM,
                recoverable=False,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception,
            (
                SparseIndexError,
                IncompatibleEmbeddingError,
                InvalidEvidenceError,
                RerankerError,
                RetrievalError,
            ),
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.RETRIEVAL_ERROR,
                code=code,
                severity=ErrorSeverity.HIGH
                if isinstance(exception, IncompatibleEmbeddingError)
                else ErrorSeverity.MEDIUM,
                recoverable=True,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception,
            (
                DivisionByZeroError,
                IncompatibleUnitsError,
                IncompatibleCurrencyError,
                IncompatibleCompanyError,
                IncompatiblePeriodError,
                CalculationError,
            ),
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.CALCULATION_ERROR,
                code=code,
                severity=ErrorSeverity.MEDIUM,
                recoverable=True,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(exception, (InvalidCitationError, CitationMarkerError)):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.CITATION_ERROR,
                code=code,
                severity=ErrorSeverity.HIGH,
                recoverable=True,  # Fallback available
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(exception, (GroundingValidationError, UnsupportedClaimError)):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.GROUNDING_ERROR,
                code=code,
                severity=ErrorSeverity.HIGH,
                recoverable=True,  # Safe fallback available
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception, (InsufficientEvidenceError, ConflictingEvidenceError, ReasoningError)
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.REASONING_ERROR,
                code=code,
                severity=ErrorSeverity.LOW,  # Legitimate domain refusal states
                recoverable=True,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(exception, LLMTimeoutError):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.TIMEOUT,
                code=code,
                severity=ErrorSeverity.HIGH,
                recoverable=True,  # Retried or fallback
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception,
            (
                LLMOutputFormatError,
                NumericalFidelityError,
                AnswerValidationError,
                LLMProviderError,
                AnswerGenerationError,
                PromptInjectionDetectedError,
            ),
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.LLM_ERROR,
                code=code,
                severity=ErrorSeverity.HIGH
                if isinstance(exception, PromptInjectionDetectedError)
                else ErrorSeverity.MEDIUM,
                recoverable=True,  # Retried or fallback
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(
            exception,
            (
                StorageError,
                VectorStoreError,
                DatabaseError,
                EmbeddingProviderError,
                ExternalServiceError,
                IndexingError,
            ),
        ):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.DEPENDENCY_UNAVAILABLE,
                code=code,
                severity=ErrorSeverity.CRITICAL,
                recoverable=False,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        if isinstance(exception, ConfigurationError):
            return ErrorRecord(
                category=ErrorTaxonomyCategory.CONFIGURATION_ERROR,
                code=code,
                severity=ErrorSeverity.CRITICAL,
                recoverable=False,
                message=msg,
                details=details,
                trace_id=trace_id,
                request_id=request_id,
            )

        # Default fallback
        return ErrorRecord(
            category=ErrorTaxonomyCategory.INTERNAL_ERROR,
            code="INTERNAL_SERVER_ERROR",
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            message=msg or "An unexpected internal error occurred.",
            details={"exception_class": type(exception).__name__, **details},
            trace_id=trace_id,
            request_id=request_id,
        )
