"""Object storage infrastructure package."""

from financial_rag.config.settings import StorageSettings, get_settings
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.infrastructure.storage.filesystem import FileSystemStorageAdapter
from financial_rag.infrastructure.storage.s3 import S3StorageAdapter


def get_storage_adapter(settings: StorageSettings | None = None) -> ObjectStorageProtocol:
    """Factory function returning configured storage adapter instance."""
    active_settings = settings or get_settings().storage
    if active_settings.adapter == "s3":
        return S3StorageAdapter(storage_settings=active_settings)
    return FileSystemStorageAdapter(storage_settings=active_settings)


__all__ = [
    "FileSystemStorageAdapter",
    "ObjectStorageProtocol",
    "S3StorageAdapter",
    "get_storage_adapter",
]
