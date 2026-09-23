"""OpenAI / Generic REST text embedding provider adapter."""

from typing import Any

from financial_rag.config.settings import EmbeddingSettings, get_settings
from financial_rag.domain.exceptions import EmbeddingProviderError
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.embeddings.openai")


class OpenAIEmbeddingProvider(EmbeddingProviderProtocol):
    """Generates vector embeddings using OpenAI API."""

    def __init__(self, embedding_settings: EmbeddingSettings | None = None) -> None:
        self._settings = embedding_settings or get_settings().embedding
        self._dimension = self._settings.dimension
        self._model_name = self._settings.model_name
        self._batch_size = self._settings.batch_size
        self._client = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self._settings.api_key.get_secret_value())
            except ImportError as ex:
                raise EmbeddingProviderError(
                    provider="openai",
                    message="openai package is required for OpenAIEmbeddingProvider.",
                ) from ex
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        res = await self.embed_batch([text])
        return res[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            client = self._get_client()
            results: list[list[float]] = []

            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                response = await client.embeddings.create(
                    input=batch,
                    model=self._model_name,
                )
                for item in response.data:
                    results.append(item.embedding)

            return results
        except Exception as ex:
            raise EmbeddingProviderError(
                provider="openai",
                message=f"Failed to generate embeddings: {ex}",
                details={"model": self._model_name, "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        try:
            vec = await self.embed_text("health probe")
            return len(vec) == self._dimension
        except Exception:
            return False
