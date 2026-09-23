"""Cross-encoder reranking adapters and deterministic test implementations."""

import math
from typing import Any

from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalQuery,
)
from financial_rag.domain.exceptions import RerankerError
from financial_rag.domain.interfaces.retrieval import RerankerProtocol
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.retrieval.sparse_retriever import tokenize_financial_text

logger = get_logger("financial_rag.infrastructure.retrieval.reranker")


class MockReranker(RerankerProtocol):
    """Deterministic reranker scoring query-candidate relevance based on financial signal alignment.

    Used for reproducible CI/test environments and offline test benchmarks.
    """

    def __init__(self, model_name: str = "mock-financial-reranker") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def _score_candidate(self, query: RetrievalQuery, candidate: RetrievalCandidate) -> float:
        """Compute deterministic relevance score based on token overlap and signal alignment."""
        content_lower = candidate.chunk.content.lower()
        section_lower = candidate.chunk.section_path.lower()
        combined_text = content_lower + " " + section_lower

        query_tokens = tokenize_financial_text(query.normalized_query)
        if not query_tokens:
            return float(candidate.fusion_score or candidate.final_score or 0.5)

        # 1. Base lexical token overlap ratio
        matched_tokens = 0
        for token in query_tokens:
            if token in combined_text:
                matched_tokens += 1

        overlap_ratio = matched_tokens / max(1, len(query_tokens))

        # 2. Financial signal alignment boosts
        signal_boost = 0.0

        # Exact Ticker match
        for ticker in query.signals.tickers:
            t_lower = ticker.lower()
            if t_lower in combined_text or candidate.chunk.metadata.get("ticker_symbol") == ticker:
                signal_boost += 0.25

        # Exact Fiscal Year match
        for year in query.signals.fiscal_years:
            if str(year) in combined_text:
                signal_boost += 0.25

        # Exact Metric match
        for metric in query.signals.metrics:
            if metric.lower() in combined_text:
                signal_boost += 0.20

        # SEC Section alignment
        for section in query.signals.sections:
            if any(term in section_lower for term in tokenize_financial_text(section)):
                signal_boost += 0.30

        # Table alignment for numerical/table queries
        if (
            query.signals.is_table_lookup or "table" in query.normalized_query.lower()
        ) and candidate.chunk.chunk_type.value == "table":
            signal_boost += 0.25

        # Blend base fusion score (40%) + token overlap (30%) + signal boost (30%)
        base_score = float(candidate.fusion_score or candidate.final_score or 0.5)
        raw_rerank = (0.4 * base_score) + (0.3 * overlap_ratio) + (0.3 * min(1.0, signal_boost))

        # Scale into [0.0, 1.0] interval
        return min(1.0, max(0.0, raw_rerank))

    async def rerank(
        self,
        query: RetrievalQuery,
        candidates: list[RetrievalCandidate],
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Rerank candidates using deterministic signal alignment."""
        if not candidates:
            return []

        limit = top_k or query.rerank_top_k or len(candidates)
        bounded_pool = candidates[: max(1, query.rerank_top_k * 2)]

        scored_candidates: list[RetrievalCandidate] = []
        for cand in bounded_pool:
            score = self._score_candidate(query, cand)
            # Create updated candidate with reranker score
            updated = RetrievalCandidate(
                chunk=cand.chunk,
                dense_score=cand.dense_score,
                dense_rank=cand.dense_rank,
                sparse_score=cand.sparse_score,
                sparse_rank=cand.sparse_rank,
                fusion_score=cand.fusion_score,
                reranker_score=score,
                final_score=score,
                sources=cand.sources,
                provenance=cand.provenance or cand.chunk.get_provenance(),
            )
            scored_candidates.append(updated)

        # Sort by reranker score descending
        scored_candidates.sort(key=lambda x: float(x.reranker_score or 0.0), reverse=True)
        result = scored_candidates[:limit]

        logger.info(
            f"MockReranker reranked {len(bounded_pool)} candidates down to {len(result)} for query '{query.id}'"
        )
        return result

    async def health_check(self) -> bool:
        return True


class CrossEncoderReranker(RerankerProtocol):
    """Production cross-encoder reranker adapter for sentence-transformers / HuggingFace models."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        max_length: int = 512,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._max_length = max_length
        self._model: Any = None

    def _load_model(self) -> Any:
        """Lazy load cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore[import-not-found]

                self._model = CrossEncoder(
                    self._model_name,
                    max_length=self._max_length,
                    device=self._device,
                )
                logger.info(
                    f"Loaded CrossEncoder model '{self._model_name}' on device '{self._device}'"
                )
            except ImportError as ex:
                raise RerankerError(
                    provider="sentence-transformers",
                    message="sentence-transformers package is required for CrossEncoderReranker.",
                ) from ex
            except Exception as ex:
                raise RerankerError(
                    provider="cross-encoder",
                    message=f"Failed to load cross-encoder model '{self._model_name}': {ex}",
                ) from ex
        return self._model

    async def rerank(
        self,
        query: RetrievalQuery,
        candidates: list[RetrievalCandidate],
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Score query-candidate pairs with cross-encoder."""
        if not candidates:
            return []

        limit = top_k or query.rerank_top_k or len(candidates)
        # Safety bound: cap candidate pool size sent to reranker
        bounded_pool = candidates[:50]

        try:
            model = self._load_model()
            query_text = query.normalized_query or query.raw_query
            pairs = [[query_text, c.chunk.content] for c in bounded_pool]

            raw_scores = model.predict(pairs)

            # Convert sigmoid / raw scores to list of floats
            scored_candidates: list[RetrievalCandidate] = []
            for cand, score in zip(bounded_pool, raw_scores, strict=True):
                # Sigmoid normalization if scores are unconstrained logits
                float_score = float(score)
                norm_score = (
                    1.0 / (1.0 + math.exp(-float_score))
                    if float_score < -5 or float_score > 5
                    else float_score
                )

                updated = RetrievalCandidate(
                    chunk=cand.chunk,
                    dense_score=cand.dense_score,
                    dense_rank=cand.dense_rank,
                    sparse_score=cand.sparse_score,
                    sparse_rank=cand.sparse_rank,
                    fusion_score=cand.fusion_score,
                    reranker_score=norm_score,
                    final_score=norm_score,
                    sources=cand.sources,
                    provenance=cand.provenance or cand.chunk.get_provenance(),
                )
                scored_candidates.append(updated)

            scored_candidates.sort(key=lambda x: float(x.reranker_score or 0.0), reverse=True)
            return scored_candidates[:limit]

        except Exception as ex:
            logger.error(f"Cross-encoder inference failed for query '{query.id}': {ex}")
            raise RerankerError(
                provider="cross-encoder",
                message=f"Reranker inference failure: {ex}",
                details={"query_id": str(query.id), "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        try:
            self._load_model()
            return True
        except Exception:
            return False
