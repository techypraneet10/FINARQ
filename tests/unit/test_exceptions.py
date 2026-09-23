"""Unit tests for domain and infrastructure exception hierarchies."""

import pytest

from financial_rag.domain.exceptions import (
    ConfigurationError,
    DatabaseError,
    DomainError,
    EmbeddingProviderError,
    ExternalServiceError,
    FinancialRAGError,
    InfrastructureError,
    LLMProviderError,
    NotFoundError,
    StorageError,
    ValidationError,
    VectorStoreError,
)


@pytest.mark.unit
def test_base_financial_rag_error() -> None:
    """Test base exception attributes and serialization."""
    err = FinancialRAGError(
        message="Base system failure",
        code="SYS_ERR",
        details={"trace": "xyz"},
    )

    assert str(err) == "Base system failure"
    assert err.code == "SYS_ERR"
    assert err.details == {"trace": "xyz"}

    data = err.to_dict()
    assert data["code"] == "SYS_ERR"
    assert data["message"] == "Base system failure"
    assert data["details"] == {"trace": "xyz"}


@pytest.mark.unit
def test_not_found_error_formatting() -> None:
    """Test NotFoundError formats standard message and details."""
    err = NotFoundError(resource_type="Document", resource_id="doc-999")
    assert "Document with ID 'doc-999' was not found" in err.message
    assert err.code == "RESOURCE_NOT_FOUND"
    assert err.details["resource_type"] == "Document"
    assert err.details["resource_id"] == "doc-999"


@pytest.mark.unit
def test_external_service_and_provider_errors() -> None:
    """Test LLM and embedding provider errors contain provider context."""
    llm_err = LLMProviderError(
        provider="openai",
        message="Rate limit exceeded",
        details={"model": "gpt-4o"},
    )
    assert "External service 'openai' error: Rate limit exceeded" in llm_err.message
    assert llm_err.code == "LLM_PROVIDER_ERROR"
    assert llm_err.details["service_name"] == "openai"
    assert llm_err.details["model"] == "gpt-4o"

    emb_err = EmbeddingProviderError(
        provider="gemini",
        message="Dimension mismatch",
    )
    assert emb_err.code == "EMBEDDING_PROVIDER_ERROR"
    assert emb_err.details["service_name"] == "gemini"


@pytest.mark.unit
def test_infrastructure_exceptions_hierarchy() -> None:
    """Verify infrastructure exceptions inherit from InfrastructureError."""
    assert issubclass(StorageError, InfrastructureError)
    assert issubclass(VectorStoreError, InfrastructureError)
    assert issubclass(DatabaseError, InfrastructureError)
    assert issubclass(ExternalServiceError, InfrastructureError)
    assert issubclass(InfrastructureError, FinancialRAGError)
    assert issubclass(DomainError, FinancialRAGError)
    assert issubclass(ConfigurationError, FinancialRAGError)
    assert issubclass(ValidationError, FinancialRAGError)
