"""S3/MinIO compatible object storage adapter."""

import asyncio
from typing import Any, BinaryIO

from financial_rag.config.settings import StorageSettings, get_settings
from financial_rag.domain.exceptions import StorageError
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.storage.s3")


class S3StorageAdapter(ObjectStorageProtocol):
    """Object storage adapter targeting AWS S3 or MinIO S3-compatible APIs."""

    def __init__(self, storage_settings: StorageSettings | None = None) -> None:
        self._settings = storage_settings or get_settings().storage
        self._bucket = self._settings.bucket_documents
        self._endpoint_url = self._settings.endpoint_url
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config

                self._client = boto3.client(
                    "s3",
                    endpoint_url=self._endpoint_url,
                    aws_access_key_id=self._settings.access_key.get_secret_value(),
                    aws_secret_access_key=self._settings.secret_key.get_secret_value(),
                    region_name=self._settings.region,
                    use_ssl=self._settings.use_ssl,
                    config=Config(signature_version="s3v4"),
                )
            except ImportError as ex:
                raise StorageError(
                    message="boto3 is required to use S3StorageAdapter. Please install boto3.",
                    code="DEPENDENCY_MISSING",
                ) from ex
        return self._client

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        try:
            client: Any = self._get_client()
            raw_bytes: bytes = data if isinstance(data, bytes) else data.read()
            meta = metadata or {}

            def _sync_upload() -> None:
                client.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=raw_bytes,
                    ContentType=content_type,
                    Metadata=meta,
                )

            await asyncio.to_thread(_sync_upload)
            storage_uri = f"s3://{self._bucket}/{key}"
            logger.info(f"Uploaded S3 object to {storage_uri}")
            return storage_uri
        except Exception as ex:
            raise StorageError(
                message=f"Failed to upload object to S3 at key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def download(self, key: str) -> bytes:
        try:
            client: object = self._get_client()

            def _sync_download() -> bytes:
                response = client.get_object(Bucket=self._bucket, Key=key)  # type: ignore[attr-defined]
                return response["Body"].read()  # type: ignore[no-any-return]

            return await asyncio.to_thread(_sync_download)
        except Exception as ex:
            raise StorageError(
                message=f"Failed to download object from S3 key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def delete(self, key: str) -> bool:
        try:
            client: object = self._get_client()

            def _sync_delete() -> None:
                client.delete_object(Bucket=self._bucket, Key=key)  # type: ignore[attr-defined]

            await asyncio.to_thread(_sync_delete)
            return True
        except Exception as ex:
            raise StorageError(
                message=f"Failed to delete S3 object at key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def exists(self, key: str) -> bool:
        try:
            client: object = self._get_client()

            def _sync_head() -> bool:
                try:
                    client.head_object(Bucket=self._bucket, Key=key)  # type: ignore[attr-defined]
                    return True
                except Exception:
                    return False

            return await asyncio.to_thread(_sync_head)
        except Exception:
            return False

    async def get_metadata(self, key: str) -> dict[str, str]:
        try:
            client: object = self._get_client()

            def _sync_head() -> dict[str, str]:
                resp = client.head_object(Bucket=self._bucket, Key=key)  # type: ignore[attr-defined]
                return resp.get("Metadata", {})  # type: ignore[no-any-return]

            return await asyncio.to_thread(_sync_head)
        except Exception:
            return {}

    async def get_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        try:
            client: object = self._get_client()

            def _sync_presign() -> str:
                return client.generate_presigned_url(  # type: ignore[no-any-return,attr-defined]
                    "get_object",
                    Params={"Bucket": self._bucket, "Key": key},
                    ExpiresIn=expires_in_seconds,
                )

            return await asyncio.to_thread(_sync_presign)
        except Exception as ex:
            raise StorageError(
                message=f"Failed to generate presigned URL for S3 key '{key}': {ex}",
                details={"key": key, "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        try:
            client: object = self._get_client()

            def _sync_check() -> bool:
                client.head_bucket(Bucket=self._bucket)  # type: ignore[attr-defined]
                return True

            return await asyncio.to_thread(_sync_check)
        except Exception:
            return False
