"""Architectural contract for provider-agnostic text embeddings."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProviderProtocol(Protocol):
    """Contract for computing vector representations of financial text."""

    @property
    def model_name(self) -> str:
        """Identifier of the active embedding model."""
        ...

    @property
    def dimension(self) -> int:
        """Expected output dimension of the vector embedding."""
        ...

    async def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a single text segment."""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of text segments."""
        ...

    async def health_check(self) -> bool:
        """Verify embedding provider service connectivity."""
        ...
