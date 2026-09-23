"""Unit tests for DocumentValidator and hashing utilities."""

import pytest

from financial_rag.application.ingestion.hashing import calculate_sha256
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.config.settings import IngestionSettings
from financial_rag.domain.exceptions import FileValidationError


@pytest.mark.unit
def test_sha256_calculation() -> None:
    data = b"%PDF-1.7 sample financial document"
    assert calculate_sha256(data) == calculate_sha256(data)
    assert len(calculate_sha256(data)) == 64


@pytest.mark.unit
def test_validator_accepts_valid_pdf() -> None:
    validator = DocumentValidator()
    valid_pdf_bytes = b"%PDF-1.7\nSample document body"
    safe_name = validator.validate_file(
        content=valid_pdf_bytes,
        filename="Apple_10K_FY2023.pdf",
        content_type="application/pdf",
    )
    assert safe_name == "Apple_10K_FY2023.pdf"


@pytest.mark.unit
def test_validator_sanitizes_path_traversal() -> None:
    validator = DocumentValidator()
    valid_pdf_bytes = b"%PDF-1.7\nSample document body"
    safe_name = validator.validate_file(
        content=valid_pdf_bytes,
        filename="../../etc/passwd/report.pdf",
        content_type="application/pdf",
    )
    assert "/" not in safe_name
    assert ".." not in safe_name
    assert safe_name.endswith(".pdf")


@pytest.mark.unit
def test_validator_rejects_missing_magic_bytes() -> None:
    validator = DocumentValidator()
    invalid_bytes = b"NOT_A_PDF_FILE_HEADER"
    with pytest.raises(
        FileValidationError, match="Missing standard '%PDF-' magic header signature"
    ):
        validator.validate_file(
            content=invalid_bytes,
            filename="fake.pdf",
            content_type="application/pdf",
        )


@pytest.mark.unit
def test_validator_rejects_empty_file() -> None:
    validator = DocumentValidator()
    with pytest.raises(FileValidationError, match="Uploaded file is empty"):
        validator.validate_file(
            content=b"",
            filename="empty.pdf",
            content_type="application/pdf",
        )


@pytest.mark.unit
def test_validator_rejects_oversized_file() -> None:
    settings = IngestionSettings(max_file_size_bytes=1024)
    validator = DocumentValidator(settings=settings)
    large_pdf = b"%PDF-1.7" + (b"0" * 2048)
    with pytest.raises(FileValidationError, match="exceeds maximum allowed limit"):
        validator.validate_file(
            content=large_pdf,
            filename="large.pdf",
            content_type="application/pdf",
        )


@pytest.mark.unit
def test_validator_generates_storage_key() -> None:
    validator = DocumentValidator()
    key = validator.generate_storage_key(
        document_id="doc-123",
        version_id="ver-456",
        filename="sample.pdf",
    )
    assert key == "tenants/default_tenant/documents/doc-123/versions/ver-456/sample.pdf"

    key_custom = validator.generate_storage_key(
        document_id="doc-123",
        version_id="ver-456",
        filename="sample.pdf",
        tenant_id="tenant-xyz",
    )
    assert key_custom == "tenants/tenant-xyz/documents/doc-123/versions/ver-456/sample.pdf"
