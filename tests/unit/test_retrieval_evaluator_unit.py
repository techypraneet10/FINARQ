"""Unit tests for RetrievalEvaluator metrics (Recall@K, Precision@K, HitRate@K, MRR, NDCG@K, MAP) and failure taxonomy."""

from uuid import uuid4

import pytest

from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult
from financial_rag.infrastructure.evaluation.retrieval_evaluator import RetrievalEvaluator


def create_mock_chunk(chunk_id: str, page_number: int, text: str = "sample text") -> DocumentChunk:
    return DocumentChunk(
        id=chunk_id,
        document_id=str(uuid4()),
        document_version_id=str(uuid4()),
        chunk_index=0,
        page_number=page_number,
        content=text,
    )


def test_retrieval_evaluator_perfect_recall_and_precision() -> None:
    evaluator = RetrievalEvaluator()
    chunk1 = create_mock_chunk("chunk-1", 45)
    chunk2 = create_mock_chunk("chunk-2", 45)

    results = [
        RetrievalResult(chunk=chunk1, score=0.95, retrieval_method="dense"),
        RetrievalResult(chunk=chunk2, score=0.90, retrieval_method="dense"),
    ]

    metrics = evaluator.evaluate_retrieval(
        retrieved_items=results,
        ground_truth_chunks=["chunk-1", "chunk-2"],
        ground_truth_pages=[45],
        strategy="dense",
        latency_ms=12.5,
    )

    assert metrics.recall_at_1 == 0.5
    assert metrics.recall_at_3 == 1.0
    assert metrics.recall_at_5 == 1.0
    assert metrics.recall_at_10 == 1.0

    assert metrics.precision_at_1 == 1.0
    assert metrics.precision_at_3 == pytest.approx(2.0 / 3.0)
    assert metrics.hit_rate_at_1 == 1.0
    assert metrics.mrr == 1.0
    assert metrics.ndcg_at_5 > 0.90
    assert metrics.map_score == 1.0
    assert metrics.strategy == "dense"
    assert metrics.mean_latency_ms == 12.5


def test_retrieval_evaluator_page_level_relevance() -> None:
    evaluator = RetrievalEvaluator()
    chunk1 = create_mock_chunk("chunk-diff-1", 48)
    chunk2 = create_mock_chunk("chunk-diff-2", 49)

    results = [
        RetrievalResult(chunk=chunk1, score=0.85, retrieval_method="sparse"),
        RetrievalResult(chunk=chunk2, score=0.80, retrieval_method="sparse"),
    ]

    metrics = evaluator.evaluate_retrieval(
        retrieved_items=results,
        ground_truth_chunks=[],
        ground_truth_pages=[48],
        strategy="sparse",
    )

    assert metrics.hit_rate_at_1 == 1.0
    assert metrics.mrr == 1.0
    assert metrics.recall_at_1 == 1.0
    assert metrics.precision_at_1 == 1.0
    assert metrics.map_score == 1.0


def test_retrieval_evaluator_empty_results_and_failure_taxonomy() -> None:
    evaluator = RetrievalEvaluator()
    empty_results: list[RetrievalResult] = []

    metrics = evaluator.evaluate_retrieval(
        retrieved_items=empty_results,
        ground_truth_chunks=["chunk-1"],
        ground_truth_pages=[45],
    )

    assert metrics.recall_at_10 == 0.0
    assert metrics.hit_rate_at_10 == 0.0
    assert metrics.mrr == 0.0
    assert metrics.map_score == 0.0

    failure = evaluator.classify_retrieval_failure(
        retrieved_items=empty_results,
        ground_truth_chunks=["chunk-1"],
        ground_truth_pages=[45],
    )
    assert failure == "EMPTY_RETRIEVAL_RESULTS"


def test_retrieval_evaluator_low_rank_relevance_failure() -> None:
    evaluator = RetrievalEvaluator()
    chunks = [create_mock_chunk(f"chunk-irrelevant-{i}", 100 + i) for i in range(5)]
    target_chunk = create_mock_chunk("chunk-target", 45)
    all_chunks = [*chunks, target_chunk]

    results = [
        RetrievalResult(chunk=c, score=0.5 - (i * 0.05), retrieval_method="hybrid")
        for i, c in enumerate(all_chunks)
    ]

    failure = evaluator.classify_retrieval_failure(
        retrieved_items=results,
        ground_truth_chunks=["chunk-target"],
        ground_truth_pages=[45],
    )
    assert failure == "LOW_RANK_RELEVANCE"


def test_retrieval_evaluator_no_failure() -> None:
    evaluator = RetrievalEvaluator()
    target_chunk = create_mock_chunk("chunk-target", 45)
    results = [RetrievalResult(chunk=target_chunk, score=0.99, retrieval_method="hybrid")]

    failure = evaluator.classify_retrieval_failure(
        retrieved_items=results,
        ground_truth_chunks=["chunk-target"],
        ground_truth_pages=[45],
    )
    assert failure == "NO_FAILURE"
