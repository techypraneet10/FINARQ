"""Retrieval evaluation metrics, curated datasets, and ablation runner."""

from financial_rag.application.retrieval.evaluation.dataset import (
    BenchmarkItem,
    get_benchmark_dataset,
    get_synthetic_financial_corpus,
)
from financial_rag.application.retrieval.evaluation.evaluator import (
    RetrievalBenchmarkEvaluator,
    StrategyMetrics,
)
from financial_rag.application.retrieval.evaluation.metrics import (
    calculate_retrieval_metrics,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

__all__ = [
    "BenchmarkItem",
    "RetrievalBenchmarkEvaluator",
    "StrategyMetrics",
    "calculate_retrieval_metrics",
    "get_benchmark_dataset",
    "get_synthetic_financial_corpus",
    "hit_rate_at_k",
    "mean_reciprocal_rank",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
]
