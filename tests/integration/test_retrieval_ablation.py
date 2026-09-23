"""Integration test executing the full 10-query benchmark ablation suite."""

import pytest

from financial_rag.application.retrieval.evaluation.evaluator import RetrievalBenchmarkEvaluator


@pytest.mark.asyncio
async def test_run_retrieval_benchmark_ablation() -> None:
    """Execute complete 10-query benchmark evaluation comparing Dense, Sparse, Hybrid, and Reranked."""
    evaluator = RetrievalBenchmarkEvaluator()

    # 1. Seed benchmark corpus into dense and sparse indexes
    corpus_size = await evaluator.setup_corpus()
    assert corpus_size == 10

    # 2. Run full evaluation across all benchmark queries
    results = await evaluator.run_evaluation()

    assert "Dense Only" in results
    assert "Sparse Only" in results
    assert "Hybrid (RRF)" in results
    assert "Hybrid + Reranking" in results

    dense = results["Dense Only"]
    sparse = results["Sparse Only"]
    hybrid = results["Hybrid (RRF)"]
    reranked = results["Hybrid + Reranking"]

    assert dense.recall_at_10 >= 0.0
    assert sparse.recall_at_10 >= 0.0
    assert hybrid.recall_at_10 >= 0.0

    # Verify metrics are positive and bounded
    for _name, s in results.items():
        assert 0.0 <= s.mrr <= 1.0
        assert 0.0 <= s.recall_at_1 <= 1.0
        assert 0.0 <= s.recall_at_10 <= 1.0
        assert 0.0 <= s.precision_at_1 <= 1.0
        assert 0.0 <= s.ndcg_at_10 <= 1.0
        assert len(s.per_query_results) == 10

    # Verify that Hybrid + Reranking achieves high Recall and MRR
    assert reranked.recall_at_10 >= 0.8
    assert reranked.hit_rate_at_10 >= 0.9

    # Generate markdown table for reporting
    md_table = evaluator.format_ablation_markdown_table(results)
    assert "Retrieval Strategy" in md_table
    assert "Hybrid + Reranking" in md_table
