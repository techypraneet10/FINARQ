"""Unit tests for FileSystemStorageAdapter."""

import pytest

from financial_rag.config.settings import StorageSettings
from financial_rag.domain.exceptions import StorageError
from financial_rag.infrastructure.storage.filesystem import FileSystemStorageAdapter


@pytest.mark.unit
async def test_filesystem_storage_lifecycle(tmp_path) -> None:
    settings = StorageSettings(adapter="filesystem", local_dir=str(tmp_path))
    storage = FileSystemStorageAdapter(storage_settings=settings)

    key = "documents/doc-1/versions/v1/test.pdf"
    content = b"%PDF-1.7 sample content"
    metadata = {"doc_id": "doc-1", "author": "Acme"}

    # 1. Upload
    uri = await storage.upload(key, content, content_type="application/pdf", metadata=metadata)
    assert uri.startswith("file://")

    # 2. Exists
    assert await storage.exists(key) is True
    assert await storage.exists("nonexistent/key.pdf") is False

    # 3. Download
    downloaded = await storage.download(key)
    assert downloaded == content

    # 4. Metadata
    retrieved_meta = await storage.get_metadata(key)
    assert retrieved_meta["doc_id"] == "doc-1"
    assert retrieved_meta["content_type"] == "application/pdf"

    # 5. Delete
    deleted = await storage.delete(key)
    assert deleted is True
    assert await storage.exists(key) is False


@pytest.mark.unit
async def test_filesystem_storage_traversal_defense(tmp_path) -> None:
    settings = StorageSettings(adapter="filesystem", local_dir=str(tmp_path))
    storage = FileSystemStorageAdapter(storage_settings=settings)

    with pytest.raises(StorageError, match="Illegal path traversal detected"):
        await storage.upload("../../../outside.pdf", b"data")
