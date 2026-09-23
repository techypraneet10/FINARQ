"""Unit tests for retrieval evaluation metrics calculations."""

import pytest

from financial_rag.application.retrieval.evaluation.metrics import (
    calculate_retrieval_metrics,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_recall_and_precision_at_k() -> None:
    ground_truth = {"c1", "c2", "c3"}
    retrieved = ["c1", "c4", "c2", "c5", "c6"]

    # Recall @ 1: retrieved {"c1"}, ground truth {"c1", "c2", "c3"} -> 1/3
    assert recall_at_k(retrieved, ground_truth, k=1) == pytest.approx(1.0 / 3.0)
    # Recall @ 3: retrieved {"c1", "c4", "c2"} -> 2/3
    assert recall_at_k(retrieved, ground_truth, k=3) == pytest.approx(2.0 / 3.0)
    # Precision @ 1: 1/1 = 1.0
    assert precision_at_k(retrieved, ground_truth, k=1) == 1.0
    # Precision @ 2: 1/2 = 0.5
    assert precision_at_k(retrieved, ground_truth, k=2) == 0.5
    # Precision @ 3: 2/3
    assert precision_at_k(retrieved, ground_truth, k=3) == pytest.approx(2.0 / 3.0)

    # Empty inputs
    assert recall_at_k([], ground_truth, k=5) == 0.0
    assert precision_at_k(retrieved, set(), k=5) == 0.0


def test_hit_rate_at_k() -> None:
    ground_truth = {"target-1"}
    assert hit_rate_at_k(["other", "target-1"], ground_truth, k=1) == 0.0
    assert hit_rate_at_k(["other", "target-1"], ground_truth, k=2) == 1.0
    assert hit_rate_at_k(["other"], ground_truth, k=10) == 0.0


def test_mean_reciprocal_rank() -> None:
    ground_truth = {"c3"}
    assert mean_reciprocal_rank(["c3", "c1", "c2"], ground_truth) == 1.0  # rank 1 -> 1/1
    assert mean_reciprocal_rank(["c1", "c3", "c2"], ground_truth) == 0.5  # rank 2 -> 1/2
    assert mean_reciprocal_rank(["c1", "c2", "c3"], ground_truth) == pytest.approx(1.0 / 3.0)
    assert mean_reciprocal_rank(["c1", "c2", "c4"], ground_truth) == 0.0


def test_ndcg_at_k() -> None:
    relevance = {"c1": 2.0, "c2": 1.0, "c3": 0.0}

    # Perfect ranking: ["c1", "c2"]
    perfect_ndcg = ndcg_at_k(["c1", "c2"], relevance, k=2)
    assert perfect_ndcg == pytest.approx(1.0)

    # Imperfect ranking: ["c2", "c1"]
    imperfect_ndcg = ndcg_at_k(["c2", "c1"], relevance, k=2)
    assert imperfect_ndcg < 1.0
    assert imperfect_ndcg > 0.0

    # Irrelevant first: ["c3", "c1"]
    worse_ndcg = ndcg_at_k(["c3", "c1"], relevance, k=2)
    assert worse_ndcg < imperfect_ndcg


def test_calculate_retrieval_metrics_suite() -> None:
    ground_truth = {"c1", "c2"}
    relevance = {"c1": 2.0, "c2": 1.0}
    retrieved = ["c1", "c3", "c2", "c4"]

    suite = calculate_retrieval_metrics(retrieved, ground_truth, relevance, k_list=[1, 3, 5])
    assert "mrr" in suite
    assert "recall@1" in suite
    assert "recall@3" in suite
    assert "precision@1" in suite
    assert "ndcg@3" in suite
    assert suite["mrr"] == 1.0
