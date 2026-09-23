"""Unit tests for MockEmbeddingProvider and embedding factory."""

import pytest

from financial_rag.config.settings import EmbeddingSettings
from financial_rag.infrastructure.embeddings import get_embedding_provider
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider


@pytest.mark.unit
async def test_mock_embedding_provider_determinism() -> None:
    provider = MockEmbeddingProvider(dimension=128)
    text1 = "Total revenue was $383,285 million in fiscal 2023."
    text2 = "Total revenue was $383,285 million in fiscal 2023."
    diff_text = "Operating income was $114,301 million."

    emb1 = await provider.embed_text(text1)
    emb2 = await provider.embed_text(text2)
    emb_diff = await provider.embed_text(diff_text)

    assert len(emb1) == 128
    assert emb1 == emb2  # Deterministic repeatability
    assert emb1 != emb_diff


@pytest.mark.unit
async def test_mock_embedding_provider_batch() -> None:
    provider = MockEmbeddingProvider(dimension=64)
    texts = ["Item 1", "Item 1A", "Item 7", "Item 8"]
    batch_res = await provider.embed_batch(texts)

    assert len(batch_res) == 4
    for vec in batch_res:
        assert len(vec) == 64


@pytest.mark.unit
def test_embedding_factory() -> None:
    settings = EmbeddingSettings(provider="mock", dimension=256)
    provider = get_embedding_provider(settings)
    assert provider.dimension == 256
