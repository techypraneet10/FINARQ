"""Embeddings infrastructure package."""

from financial_rag.config.settings import EmbeddingSettings, get_settings
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.embeddings.openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider(
    settings: EmbeddingSettings | None = None,
) -> EmbeddingProviderProtocol:
    """Return configured embedding provider instance."""
    active_settings = settings or get_settings().embedding
    if active_settings.provider == "openai":
        return OpenAIEmbeddingProvider(embedding_settings=active_settings)
    return MockEmbeddingProvider(embedding_settings=active_settings)


__all__ = [
    "EmbeddingProviderProtocol",
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider",
]
