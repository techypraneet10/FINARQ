"""Unit tests verifying domain interface protocols and runtime checkability."""

from typing import Any, BinaryIO, TypeVar

import pytest

from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult
from financial_rag.domain.interfaces.llm import LLMProviderProtocol
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol

T = TypeVar("T")


class MockStorage:
    """Conformant mock storage adapter."""

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        return f"s3://bucket/{key}"

    async def download(self, key: str) -> bytes:
        return b"content"

    async def delete(self, key: str) -> bool:
        return True

    async def exists(self, key: str) -> bool:
        return True

    async def get_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        return f"https://s3.amazonaws.com/{key}"

    async def get_metadata(self, key: str) -> dict[str, str]:
        return {"key": key}

    async def health_check(self) -> bool:
        return True


class IncompleteStorage:
    """Non-conformant storage adapter missing methods."""

    async def upload(self, key: str, data: bytes) -> str:
        return key


@pytest.mark.unit
def test_storage_protocol_runtime_check() -> None:
    """Verify runtime_checkable protocol correctly validates implementations."""
    valid_storage = MockStorage()
    assert isinstance(valid_storage, ObjectStorageProtocol)

    invalid_storage = IncompleteStorage()
    assert not isinstance(invalid_storage, ObjectStorageProtocol)


class MockVectorStore:
    """Conformant mock vector store adapter."""

    async def initialize_collection(
        self, dimension: int, collection_name: str | None = None
    ) -> bool:
        return True

    async def upsert_chunks(
        self, chunks: list[DocumentChunk], embeddings: list[list[float]]
    ) -> bool:
        return True

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievalResult]:
        return []

    async def delete_by_document_id(self, document_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
def test_vector_store_protocol_runtime_check() -> None:
    """Verify VectorStoreProtocol validates conforming objects."""
    store = MockVectorStore()
    assert isinstance(store, VectorStoreProtocol)


class MockLLMProvider:
    """Conformant mock LLM provider."""

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> str:
        return "response"

    async def structured_generate(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        raise NotImplementedError

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        yield "chunk"

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
def test_llm_provider_protocol_runtime_check() -> None:
    """Verify LLMProviderProtocol validates conforming objects."""
    llm = MockLLMProvider()
    assert isinstance(llm, LLMProviderProtocol)
