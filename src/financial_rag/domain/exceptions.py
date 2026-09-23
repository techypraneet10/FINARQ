"""Core domain and application exceptions hierarchy."""

from typing import Any


class FinancialRAGError(Exception):
    """Base exception for all Financial RAG platform errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class DomainError(FinancialRAGError):
    """Exception raised when a domain invariant or business rule is violated."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_RULE_VIOLATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class ConfigurationError(FinancialRAGError):
    """Exception raised for invalid or missing configuration parameters."""

    def __init__(
        self,
        message: str,
        code: str = "CONFIGURATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class ValidationError(FinancialRAGError):
    """Exception raised when input data fails validation constraints."""

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class NotFoundError(FinancialRAGError):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"{resource_type} with ID '{resource_id}' was not found."
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})},
        )


class InfrastructureError(FinancialRAGError):
    """Base exception for infrastructure and external integration failures."""

    def __init__(
        self,
        message: str,
        code: str = "INFRASTRUCTURE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class StorageError(InfrastructureError):
    """Exception raised for object storage operational failures."""

    def __init__(
        self,
        message: str,
        code: str = "STORAGE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class VectorStoreError(InfrastructureError):
    """Exception raised for vector database operational failures."""

    def __init__(
        self,
        message: str,
        code: str = "VECTOR_STORE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class DatabaseError(InfrastructureError):
    """Exception raised for relational database operational failures."""

    def __init__(
        self,
        message: str,
        code: str = "DATABASE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class ExternalServiceError(InfrastructureError):
    """Exception raised when an external API or service fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        code: str = "EXTERNAL_SERVICE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        full_message = f"External service '{service_name}' error: {message}"
        super().__init__(
            message=full_message,
            code=code,
            details={"service_name": service_name, **(details or {})},
        )


class LLMProviderError(ExternalServiceError):
    """Exception raised during LLM API interactions."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            service_name=provider,
            message=message,
            code="LLM_PROVIDER_ERROR",
            details=details,
        )


class EmbeddingProviderError(ExternalServiceError):
    """Exception raised during embedding API interactions."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            service_name=provider,
            message=message,
            code="EMBEDDING_PROVIDER_ERROR",
            details=details,
        )


class FileValidationError(ValidationError):
    """Exception raised when an uploaded document file fails validation."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="FILE_VALIDATION_ERROR", details=details)


class DuplicateDocumentError(DomainError):
    """Exception raised when an identical binary document is uploaded."""

    def __init__(
        self,
        file_hash: str,
        existing_document_id: str,
        message: str = "A document with identical content already exists.",
    ) -> None:
        super().__init__(
            message=message,
            code="DUPLICATE_DOCUMENT",
            details={"file_hash": file_hash, "existing_document_id": existing_document_id},
        )


class DocumentParsingError(InfrastructureError):
    """Exception raised when a PDF parser fails to process document structure."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="DOCUMENT_PARSING_ERROR", details=details)


class OCRError(InfrastructureError):
    """Exception raised when OCR extraction fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="OCR_PROCESSING_ERROR", details=details)


class TableExtractionError(DomainError):
    """Exception raised when table extraction or normalization fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="TABLE_EXTRACTION_ERROR", details=details)


class ChunkingError(DomainError):
    """Exception raised when structure-aware chunking fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="CHUNKING_ERROR", details=details)


class IndexingError(InfrastructureError):
    """Exception raised when vector indexing fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="INDEXING_ERROR", details=details)


class IngestionPipelineError(FinancialRAGError):
    """Exception raised when an ingestion pipeline stage fails."""

    def __init__(
        self,
        stage: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Ingestion failed at stage [{stage}]: {message}",
            code="INGESTION_PIPELINE_ERROR",
            details={"stage": stage, **(details or {})},
        )


class RetrievalError(FinancialRAGError):
    """Base exception for retrieval pipeline operational failures."""

    def __init__(
        self,
        message: str,
        code: str = "RETRIEVAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class RerankerError(ExternalServiceError):
    """Exception raised when a cross-encoder reranker inference fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            service_name=provider,
            message=message,
            code="RERANKER_ERROR",
            details=details,
        )


class SparseIndexError(InfrastructureError):
    """Exception raised when sparse lexical search or indexing fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="SPARSE_INDEX_ERROR", details=details)


class IncompatibleEmbeddingError(VectorStoreError):
    """Exception raised when query embedding dimension or model does not match indexed vector collection."""

    def __init__(
        self,
        collection_dim: int,
        query_dim: int,
        collection_name: str,
        message: str = "Vector dimension mismatch between query embedding and collection.",
    ) -> None:
        super().__init__(
            message=f"{message} Collection '{collection_name}' requires dim={collection_dim}, got dim={query_dim}",
            code="INCOMPATIBLE_EMBEDDING_DIMENSION",
            details={
                "collection_name": collection_name,
                "collection_dim": collection_dim,
                "query_dim": query_dim,
            },
        )


class InvalidEvidenceError(DomainError):
    """Exception raised when retrieved evidence fails quality guardrails or missing provenance."""

    def __init__(
        self,
        chunk_id: str,
        missing_fields: list[str],
        message: str = "Retrieved chunk failed evidence quality guardrails.",
    ) -> None:
        super().__init__(
            message=f"{message} Chunk '{chunk_id}' is missing required fields: {missing_fields}",
            code="INVALID_EVIDENCE_PROVENANCE",
            details={"chunk_id": chunk_id, "missing_fields": missing_fields},
        )


class ReasoningError(FinancialRAGError):
    """Base exception for deterministic financial reasoning failures."""

    def __init__(
        self,
        message: str,
        code: str = "REASONING_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class CalculationError(ReasoningError):
    """Exception raised when a deterministic calculation cannot be executed."""

    def __init__(
        self,
        operation: str,
        message: str,
        code: str = "CALCULATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        full_message = f"Calculation failed for operation '{operation}': {message}"
        super().__init__(
            message=full_message,
            code=code,
            details={"operation": operation, **(details or {})},
        )


class DivisionByZeroError(CalculationError):
    """Exception raised when a division or percentage change calculation has a zero denominator."""

    def __init__(
        self,
        operation: str,
        message: str = "Calculation attempted division by zero.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            operation=operation,
            message=message,
            code="DIVISION_BY_ZERO",
            details=details,
        )


class IncompatibleUnitsError(CalculationError):
    """Exception raised when trying to combine mathematically incompatible units (e.g. currency and %)."""

    def __init__(
        self,
        unit_a: str,
        unit_b: str,
        operation: str,
        message: str = "Attempted operation on incompatible financial units.",
    ) -> None:
        super().__init__(
            operation=operation,
            message=f"{message} Cannot combine '{unit_a}' with '{unit_b}'",
            code="INCOMPATIBLE_UNITS",
            details={"unit_a": unit_a, "unit_b": unit_b, "operation": operation},
        )


class IncompatibleCurrencyError(CalculationError):
    """Exception raised when combining different currencies without explicit exchange rate conversion."""

    def __init__(
        self,
        currency_a: str,
        currency_b: str,
        operation: str,
        message: str = "Cannot perform calculation across differing currencies without FX conversion.",
    ) -> None:
        super().__init__(
            operation=operation,
            message=f"{message} Found '{currency_a}' and '{currency_b}'",
            code="INCOMPATIBLE_CURRENCIES",
            details={"currency_a": currency_a, "currency_b": currency_b, "operation": operation},
        )


class IncompatibleCompanyError(CalculationError):
    """Exception raised when combining facts from different companies without cross-company query intent."""

    def __init__(
        self,
        company_a: str | None,
        company_b: str | None,
        operation: str,
        message: str = "Attempted calculation across different company entities without explicit cross-company intent.",
    ) -> None:
        super().__init__(
            operation=operation,
            message=f"{message} Entity '{company_a}' vs '{company_b}'",
            code="INCOMPATIBLE_COMPANY_ENTITIES",
            details={"company_a": company_a, "company_b": company_b, "operation": operation},
        )


class IncompatiblePeriodError(CalculationError):
    """Exception raised when attempting calculation across incompatible reporting periods."""

    def __init__(
        self,
        period_a: str,
        period_b: str,
        operation: str,
        message: str = "Attempted calculation across incompatible fiscal periods.",
    ) -> None:
        super().__init__(
            operation=operation,
            message=f"{message} Period '{period_a}' vs '{period_b}'",
            code="INCOMPATIBLE_FISCAL_PERIODS",
            details={"period_a": period_a, "period_b": period_b, "operation": operation},
        )


class InsufficientEvidenceError(ReasoningError):
    """Exception raised when required facts for reasoning or calculation are missing from retrieved evidence."""

    def __init__(
        self,
        missing_facts: list[str],
        message: str = "Insufficient evidence to answer financial inquiry.",
    ) -> None:
        super().__init__(
            message=f"{message} Missing required facts: {missing_facts}",
            code="INSUFFICIENT_EVIDENCE",
            details={"missing_facts": missing_facts},
        )


class ConflictingEvidenceError(ReasoningError):
    """Exception raised when conflicting factual values are discovered in retrieved evidence."""

    def __init__(
        self,
        metric: str,
        period: str,
        values: list[str],
        message: str = "Conflicting evidence values detected across retrieved sources.",
    ) -> None:
        super().__init__(
            message=f"{message} Metric '{metric}' ({period}) has conflicting values: {values}",
            code="CONFLICTING_EVIDENCE",
            details={"metric": metric, "period": period, "values": values},
        )


class GroundingValidationError(ReasoningError):
    """Exception raised when factual claims fail grounding validation against evidence."""

    def __init__(
        self,
        ungrounded_claim_ids: list[str],
        message: str = "Claims failed evidence grounding validation.",
    ) -> None:
        super().__init__(
            message=f"{message} Ungrounded claim IDs: {ungrounded_claim_ids}",
            code="GROUNDING_VALIDATION_FAILED",
            details={"ungrounded_claim_ids": ungrounded_claim_ids},
        )


class InvalidCitationError(ReasoningError):
    """Exception raised when a citation cannot be verified against source evidence provenance."""

    def __init__(
        self,
        citation_id: str,
        reason: str,
        message: str = "Citation failed provenance verification.",
    ) -> None:
        super().__init__(
            message=f"{message} Citation '{citation_id}': {reason}",
            code="INVALID_CITATION",
            details={"citation_id": citation_id, "reason": reason},
        )


# ============================================================
# Phase 4 Answer Orchestration & Synthesis Exceptions
# ============================================================


class AnswerGenerationError(FinancialRAGError):
    """Base exception for Phase 4 answer orchestration and synthesis failures."""

    def __init__(
        self,
        message: str,
        code: str = "ANSWER_GENERATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class AnswerValidationError(AnswerGenerationError):
    """Exception raised when LLM output fails post-generation validation audit."""

    def __init__(
        self,
        message: str,
        failure_reasons: list[str],
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{message} Failures: {'; '.join(failure_reasons)}",
            code="ANSWER_VALIDATION_FAILED",
            details={"failure_reasons": failure_reasons, **(details or {})},
        )


class CitationMarkerError(AnswerValidationError):
    """Exception raised when LLM hallucinates or alters citation markers (e.g. [C99] when only C1-C5 exist)."""

    def __init__(
        self,
        invalid_markers: list[str],
        message: str = "LLM output contained unknown or fabricated citation markers.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            failure_reasons=[f"Invalid citation markers: {invalid_markers}"],
            details={"invalid_markers": invalid_markers, **(details or {})},
        )


class NumericalFidelityError(AnswerValidationError):
    """Exception raised when generated text values conflict with verified Phase 3 numbers."""

    def __init__(
        self,
        discrepancies: list[str],
        message: str = "Numerical fidelity check failed between generated answer and verified facts.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            failure_reasons=discrepancies,
            details={"discrepancies": discrepancies, **(details or {})},
        )


class UnsupportedClaimError(AnswerValidationError):
    """Exception raised when generated answer contains unverified factual claims."""

    def __init__(
        self,
        unsupported_claims: list[str],
        message: str = "Generated response contains claims not supported by verified evidence.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            failure_reasons=unsupported_claims,
            details={"unsupported_claims": unsupported_claims, **(details or {})},
        )


class PromptInjectionDetectedError(AnswerGenerationError):
    """Exception raised when malicious prompt injection or override instructions are detected."""

    def __init__(
        self,
        source: str,
        pattern: str,
        message: str = "Potential prompt injection attempt detected and neutralized.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{message} (Source: {source})",
            code="PROMPT_INJECTION_DETECTED",
            details={"source": source, "pattern": pattern, **(details or {})},
        )


class LLMTimeoutError(LLMProviderError):
    """Exception raised when LLM generation exceeds configured request timeout."""

    def __init__(
        self,
        provider: str,
        timeout_seconds: float,
        message: str = "LLM provider request timed out.",
    ) -> None:
        super().__init__(
            provider=provider,
            message=f"{message} Exceeded {timeout_seconds}s limit",
            details={"timeout_seconds": timeout_seconds},
        )


class LLMOutputFormatError(AnswerGenerationError):
    """Exception raised when LLM output fails JSON / schema parsing."""

    def __init__(
        self,
        raw_output: str,
        expected_schema: str,
        message: str = "Failed to parse structured output from LLM provider.",
    ) -> None:
        super().__init__(
            message=f"{message} Expected: {expected_schema}",
            code="LLM_OUTPUT_FORMAT_ERROR",
            details={"expected_schema": expected_schema, "raw_output_preview": raw_output[:200]},
        )


# ============================================================
# Phase 6 Security, Authentication & Multi-Tenancy Exceptions
# ============================================================


class SecurityError(FinancialRAGError):
    """Base exception for authentication, authorization, and multi-tenancy security failures."""

    def __init__(
        self,
        message: str,
        code: str = "SECURITY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class AuthenticationError(SecurityError):
    """Exception raised when identity authentication or credentials validation fails."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        code: str = "AUTHENTICATION_FAILED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class InvalidTokenError(AuthenticationError):
    """Exception raised when a JWT or session token is invalid or malformed."""

    def __init__(
        self,
        message: str = "Invalid or corrupted authentication token.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="INVALID_TOKEN", details=details)


class TokenExpiredError(AuthenticationError):
    """Exception raised when an authentication token has expired."""

    def __init__(
        self,
        message: str = "Authentication token has expired.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="TOKEN_EXPIRED", details=details)


class TokenRevokedError(AuthenticationError):
    """Exception raised when a revoked token is presented."""

    def __init__(
        self,
        message: str = "Authentication token has been revoked.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="TOKEN_REVOKED", details=details)


class AccountSuspendedError(AuthenticationError):
    """Exception raised when a user account is suspended or disabled."""

    def __init__(
        self,
        message: str = "User account is suspended or disabled.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="ACCOUNT_SUSPENDED", details=details)


class AuthorizationError(SecurityError):
    """Exception raised when an authenticated principal lacks required permissions."""

    def __init__(
        self,
        message: str = "Principal is not authorized to perform this action.",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class TenantIsolationError(AuthorizationError):
    """Exception raised when cross-tenant resource access is attempted."""

    def __init__(
        self,
        resource_tenant_id: str,
        principal_tenant_id: str,
        resource_id: str | None = None,
        message: str = "Cross-tenant access violation: resource belongs to a different tenant.",
    ) -> None:
        super().__init__(
            message=message,
            code="CROSS_TENANT_ACCESS_DENIED",
            details={
                "resource_tenant_id": resource_tenant_id,
                "principal_tenant_id": principal_tenant_id,
                "resource_id": resource_id,
            },
        )


class TenantSuspendedError(AuthorizationError):
    """Exception raised when accessing resources under a suspended tenant organization."""

    def __init__(
        self,
        tenant_id: str,
        message: str = "Tenant organization account is currently suspended.",
    ) -> None:
        super().__init__(
            message=message,
            code="TENANT_SUSPENDED",
            details={"tenant_id": tenant_id},
        )


class RateLimitExceededError(SecurityError):
    """Exception raised when a client exceeds configured rate limits."""

    def __init__(
        self,
        endpoint: str,
        retry_after_seconds: float,
        message: str = "Rate limit exceeded. Please retry later.",
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details={
                "endpoint": endpoint,
                "retry_after_seconds": retry_after_seconds,
            },
        )
