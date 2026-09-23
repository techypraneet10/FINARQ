"""Vector store infrastructure package."""

from financial_rag.config.settings import QdrantSettings, get_settings
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter


def get_vector_store(
    qdrant_settings: QdrantSettings | None = None,
) -> VectorStoreProtocol:
    """Factory function returning configured vector store adapter."""
    settings = qdrant_settings or get_settings().qdrant
    return QdrantVectorStoreAdapter(qdrant_settings=settings)


__all__ = [
    "QdrantVectorStoreAdapter",
    "VectorStoreProtocol",
    "get_vector_store",
]
