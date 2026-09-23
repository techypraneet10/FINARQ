"""Unit tests for retrieval configuration settings."""

from financial_rag.config.settings import RetrievalSettings, Settings


def test_retrieval_settings_defaults() -> None:
    settings = RetrievalSettings()
    assert settings.dense_top_k == 50
    assert settings.sparse_top_k == 50
    assert settings.candidate_pool_size == 50
    assert settings.rerank_top_k == 20
    assert settings.final_top_k == 10
    assert settings.rrf_k == 60
    assert settings.dense_weight == 1.0
    assert settings.sparse_weight == 1.0
    assert settings.reranker_provider == "mock"
    assert settings.enable_sparse_fallback is True
    assert settings.enable_dense_fallback is True


def test_settings_contains_retrieval() -> None:
    app_settings = Settings()
    assert hasattr(app_settings, "retrieval")
    assert isinstance(app_settings.retrieval, RetrievalSettings)
