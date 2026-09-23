"""Integration tests for retrieval strategy ablation study execution."""

import pytest

from financial_rag.application.evaluation.service import EvaluationService


@pytest.mark.asyncio
async def test_retrieval_ablation_study() -> None:
    eval_service = EvaluationService()
    ablation = await eval_service.run_retrieval_ablation("financial_rag_eval_v1")

    assert "dense_only" in ablation
    assert "sparse_only" in ablation
    assert "hybrid" in ablation
    assert "hybrid_rerank" in ablation

    # Check metrics structure
    for strat, met in ablation.items():
        assert met.strategy == strat
        assert met.recall_at_10 >= 0.0
        assert met.precision_at_10 >= 0.0
        assert met.mrr >= 0.0
