"""Document validation and security sanitization."""

import os
import re
from pathlib import Path

from financial_rag.config.settings import IngestionSettings, get_settings
from financial_rag.domain.exceptions import FileValidationError


class DocumentValidator:
    """Validates uploaded document files against size, MIME, magic bytes, and path security."""

    def __init__(self, settings: IngestionSettings | None = None) -> None:
        self._settings = settings or get_settings().ingestion

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and injection attacks."""
        base_name = os.path.basename(filename.replace("\\", "/"))
        # Remove any path traversal or null characters
        clean = re.sub(r"[^\w\.\-\_]", "_", base_name)
        clean = clean.lstrip(".")  # Prevent hidden files
        if not clean:
            clean = "document.pdf"
        if not clean.lower().endswith(".pdf"):
            clean = f"{clean}.pdf"
        return clean

    def validate_file(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        """Perform comprehensive validation on uploaded file binary.

        Returns:
            Sanitized filename.
        Raises:
            FileValidationError if any constraint fails.
        """
        # 1. File Size Check
        size_bytes = len(content)
        if size_bytes == 0:
            raise FileValidationError(
                message="Uploaded file is empty (0 bytes).",
                details={"filename": filename, "size_bytes": 0},
            )

        if size_bytes > self._settings.max_file_size_bytes:
            max_mb = self._settings.max_file_size_bytes / (1024 * 1024)
            actual_mb = size_bytes / (1024 * 1024)
            raise FileValidationError(
                message=f"Uploaded file size ({actual_mb:.2f} MB) exceeds maximum allowed limit ({max_mb:.2f} MB).",
                details={
                    "filename": filename,
                    "size_bytes": size_bytes,
                    "max_allowed_bytes": self._settings.max_file_size_bytes,
                },
            )

        # 2. Extension Validation (on input filename)
        raw_ext = Path(filename).suffix.lower()
        if raw_ext and raw_ext not in self._settings.allowed_extensions:
            raise FileValidationError(
                message=f"File extension '{raw_ext}' is not permitted. Allowed: {self._settings.allowed_extensions}",
                details={"filename": filename, "extension": raw_ext},
            )

        sanitized = self.sanitize_filename(filename)

        # 3. MIME Content-Type Validation (if provided)
        if (
            content_type
            and content_type.lower() not in self._settings.allowed_content_types
            and content_type != "application/octet-stream"
        ):
            raise FileValidationError(
                message=f"Content-Type '{content_type}' is not allowed. Expected: {self._settings.allowed_content_types}",
                details={"content_type": content_type},
            )

        # 4. Magic Bytes Inspection (PDF Signature)
        if not content.startswith(b"%PDF-"):
            raise FileValidationError(
                message="Invalid PDF file format. Missing standard '%PDF-' magic header signature.",
                details={"header_bytes": str(content[:10])},
            )

        return sanitized

    def generate_storage_key(
        self,
        document_id: str,
        version_id: str,
        filename: str,
        tenant_id: str = "default_tenant",
    ) -> str:
        """Generate a deterministic and tenant-isolated object storage key path."""
        safe_name = self.sanitize_filename(filename)
        clean_tenant = re.sub(r"[^\w\.\-\_]", "_", str(tenant_id))
        return f"tenants/{clean_tenant}/documents/{document_id}/versions/{version_id}/{safe_name}"
