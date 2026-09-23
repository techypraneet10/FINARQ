"""Architectural contract for document and artifact object storage."""

from typing import BinaryIO, Protocol, runtime_checkable


@runtime_checkable
class ObjectStorageProtocol(Protocol):
    """Contract for external blob/object storage (S3, MinIO, GCS)."""

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload object and return storage URI."""
        ...

    async def download(self, key: str) -> bytes:
        """Download raw bytes of the object."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete an object from storage."""
        ...

    async def exists(self, key: str) -> bool:
        """Check whether an object exists at the given key."""
        ...

    async def get_metadata(self, key: str) -> dict[str, str]:
        """Retrieve stored metadata for an object."""
        ...

    async def get_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        """Generate presigned download URL."""
        ...

    async def health_check(self) -> bool:
        """Verify storage connection health."""
        ...
