"""Local filesystem implementation of ObjectStorageProtocol."""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from financial_rag.config.settings import StorageSettings, get_settings
from financial_rag.domain.exceptions import StorageError
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.storage.filesystem")


class FileSystemStorageAdapter(ObjectStorageProtocol):
    """Local filesystem object storage adapter designed for development and isolated testing."""

    def __init__(self, storage_settings: StorageSettings | None = None) -> None:
        settings = storage_settings or get_settings().storage
        self._base_dir = Path(settings.local_dir).resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileSystemStorageAdapter initialized with root: {self._base_dir}")

    def _resolve_safe_path(self, key: str) -> Path:
        """Resolve storage key ensuring no directory traversal attacks occur."""
        clean_key = key.lstrip("/").replace("\\", "/")
        target_path = (self._base_dir / clean_key).resolve()
        if not str(target_path).startswith(str(self._base_dir)):
            raise StorageError(
                message=f"Illegal path traversal detected in key: {key}",
                code="PATH_TRAVERSAL_DETECTED",
            )
        return target_path

    def _get_meta_path(self, target_path: Path) -> Path:
        """Return the companion metadata JSON file path."""
        return target_path.with_name(f"{target_path.name}.meta.json")

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        try:
            target_path = self._resolve_safe_path(key)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            raw_bytes: bytes = data if isinstance(data, bytes) else data.read()

            # Atomic write to temp file then rename
            temp_path = target_path.with_suffix(".tmp")
            await asyncio.to_thread(temp_path.write_bytes, raw_bytes)
            if temp_path.exists():
                temp_path.replace(target_path)

            meta = metadata.copy() if metadata else {}
            meta["content_type"] = content_type
            meta["uploaded_at"] = datetime.now(UTC).isoformat()
            meta["size_bytes"] = str(len(raw_bytes))

            meta_path = self._get_meta_path(target_path)
            await asyncio.to_thread(meta_path.write_text, json.dumps(meta, indent=2), "utf-8")

            storage_uri = f"file://{target_path.as_posix()}"
            logger.info(f"Stored object at {storage_uri} ({len(raw_bytes)} bytes)")
            return storage_uri
        except Exception as ex:
            if isinstance(ex, StorageError):
                raise
            raise StorageError(
                message=f"Failed to upload object to storage at key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def download(self, key: str) -> bytes:
        try:
            target_path = self._resolve_safe_path(key)
            if not target_path.exists() or not target_path.is_file():
                raise StorageError(
                    message=f"Object not found in storage at key '{key}'",
                    code="OBJECT_NOT_FOUND",
                    details={"key": key},
                )
            return await asyncio.to_thread(target_path.read_bytes)
        except Exception as ex:
            if isinstance(ex, StorageError):
                raise
            raise StorageError(
                message=f"Failed to download object from key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def delete(self, key: str) -> bool:
        try:
            target_path = self._resolve_safe_path(key)
            meta_path = self._get_meta_path(target_path)

            deleted = False
            if target_path.exists():
                await asyncio.to_thread(target_path.unlink)
                deleted = True
            if meta_path.exists():
                await asyncio.to_thread(meta_path.unlink)

            return deleted
        except Exception as ex:
            raise StorageError(
                message=f"Failed to delete object at key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def exists(self, key: str) -> bool:
        try:
            target_path = self._resolve_safe_path(key)
            return await asyncio.to_thread(lambda: target_path.exists() and target_path.is_file())
        except Exception:
            return False

    async def get_metadata(self, key: str) -> dict[str, str]:
        try:
            target_path = self._resolve_safe_path(key)
            meta_path = self._get_meta_path(target_path)
            if not meta_path.exists():
                return {}
            content = await asyncio.to_thread(meta_path.read_text, "utf-8")
            return json.loads(content)  # type: ignore[no-any-return]
        except Exception:
            return {}

    async def get_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        target_path = self._resolve_safe_path(key)
        return f"file://{target_path.as_posix()}"

    async def health_check(self) -> bool:
        try:
            return self._base_dir.exists() and os.access(self._base_dir, os.W_OK)
        except Exception:
            return False
