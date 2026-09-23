"""Deterministic mock embedding provider for testing and offline environments."""

import hashlib
import math

from financial_rag.config.settings import EmbeddingSettings, get_settings
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.embeddings.mock")


class MockEmbeddingProvider(EmbeddingProviderProtocol):
    """Generates deterministic unit-normalized float vectors derived from text SHA-256 hash."""

    def __init__(
        self,
        dimension: int | None = None,
        model_name: str | None = None,
        embedding_settings: EmbeddingSettings | None = None,
    ) -> None:
        settings = embedding_settings or get_settings().embedding
        self._dimension = dimension if dimension is not None else settings.dimension
        self._model_name = model_name if model_name is not None else settings.model_name
        self._batch_size = settings.batch_size

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_deterministic_vector(self, text: str) -> list[float]:
        """Produce a deterministic normalized vector of length `dimension` for input text."""
        # Use SHA-256 seed to generate repeatable pseudo-random float coordinates
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed_ints = list(seed_bytes)

        raw_coords = []
        for i in range(self._dimension):
            idx1 = i % len(seed_ints)
            idx2 = (i * 7 + 3) % len(seed_ints)
            val = (seed_ints[idx1] * 256 + seed_ints[idx2]) / 65535.0 - 0.5
            raw_coords.append(val)

        # Normalize vector to unit length (L2 norm = 1.0)
        norm = math.sqrt(sum(x * x for x in raw_coords)) or 1.0
        return [x / norm for x in raw_coords]

    async def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for single text segment."""
        return self._generate_deterministic_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of texts."""
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            for text in batch:
                embeddings.append(self._generate_deterministic_vector(text))

        logger.info(f"Generated {len(embeddings)} mock embeddings (dim={self._dimension})")
        return embeddings

    async def health_check(self) -> bool:
        return True
