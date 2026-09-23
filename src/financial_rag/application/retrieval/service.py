"""Retrieval application orchestrator coordinating analysis, hybrid search, fusion, reranking, and selection."""

import asyncio
import hashlib
import json
import time

from financial_rag.config.settings import RetrievalSettings, get_settings
from financial_rag.domain.entities.retrieval import (
    EvidenceSet,
    RetrievalCandidate,
    RetrievalFilter,
    RetrievalQuery,
)
from financial_rag.domain.exceptions import RetrievalError
from financial_rag.domain.interfaces.cache import CacheProtocol
from financial_rag.domain.interfaces.retrieval import (
    CandidateDeduplicatorProtocol,
    DenseRetrieverProtocol,
    EvidenceSelectorProtocol,
    EvidenceValidatorProtocol,
    FusionStrategyProtocol,
    QueryAnalyzerProtocol,
    RerankerProtocol,
    RetrievalServiceProtocol,
    SparseRetrieverProtocol,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.telemetry import telemetry_collector
from financial_rag.infrastructure.observability.tracer import tracer

logger = get_logger("financial_rag.application.retrieval.service")


class RetrievalService(RetrievalServiceProtocol):
    """End-to-end orchestrator for the Financial Retrieval and Evidence Selection Engine."""

    def __init__(
        self,
        query_analyzer: QueryAnalyzerProtocol,
        dense_retriever: DenseRetrieverProtocol,
        sparse_retriever: SparseRetrieverProtocol,
        fusion_strategy: FusionStrategyProtocol,
        deduplicator: CandidateDeduplicatorProtocol,
        reranker: RerankerProtocol,
        evidence_selector: EvidenceSelectorProtocol,
        evidence_validator: EvidenceValidatorProtocol,
        retrieval_settings: RetrievalSettings | None = None,
        cache: CacheProtocol | None = None,
    ) -> None:
        self._analyzer = query_analyzer
        self._dense_retriever = dense_retriever
        self._sparse_retriever = sparse_retriever
        self._fusion = fusion_strategy
        self._deduplicator = deduplicator
        self._reranker = reranker
        self._selector = evidence_selector
        self._validator = evidence_validator
        self._settings = retrieval_settings or get_settings().retrieval
        self._cache = cache

    def _generate_cache_key(
        self,
        query: RetrievalQuery,
        top_k: int,
        use_reranker: bool,
    ) -> str:
        """Generate deterministic cache key for retrieval request."""
        payload = {
            "query": query.normalized_query,
            "filters": query.filters.to_dict(),
            "top_k": top_k,
            "use_reranker": use_reranker,
            "reranker_model": getattr(self._reranker, "model_name", "default"),
        }
        serialized = json.dumps(payload, sort_keys=True)
        return f"retrieval:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"

    async def search(
        self,
        raw_query: str,
        filters: RetrievalFilter | None = None,
        top_k: int = 10,
        dense_top_k: int | None = None,
        sparse_top_k: int | None = None,
        rerank_top_k: int | None = None,
        use_reranker: bool = True,
    ) -> EvidenceSet:
        """Execute full hybrid retrieval, fusion, reranking, and evidence selection workflow."""
        start_total = time.perf_counter()
        timing_ms: dict[str, float] = {}
        execution_stages: list[str] = []
        fallback_occurred = False
        fallback_reason: str | None = None

        async with tracer.async_span(
            "retrieval.hybrid_search", attributes={"top_k": top_k, "use_reranker": use_reranker}
        ):
            # 1. Query Analysis Stage
            t0 = time.perf_counter()
            with tracer.span("retrieval.query_analysis"):
                retrieval_query = self._analyzer.analyze(
                    raw_query=raw_query,
                    filters=filters,
                    top_k=top_k,
                    dense_top_k=dense_top_k or self._settings.dense_top_k,
                    sparse_top_k=sparse_top_k or self._settings.sparse_top_k,
                    rerank_top_k=rerank_top_k or self._settings.rerank_top_k,
                )
            timing_ms["query_analysis"] = (time.perf_counter() - t0) * 1000.0
            execution_stages.append("query_analysis")

            # 2. Parallel Dense and Sparse Retrieval Stage
            t_search_start = time.perf_counter()
            async with tracer.async_span("retrieval.parallel_fetch"):
                dense_task = self._dense_retriever.retrieve(
                    query=retrieval_query, top_k=retrieval_query.dense_top_k
                )
                sparse_task = self._sparse_retriever.retrieve(
                    query=retrieval_query, top_k=retrieval_query.sparse_top_k
                )

                dense_result, sparse_result = await asyncio.gather(
                    dense_task, sparse_task, return_exceptions=True
                )
            timing_ms["retrieval_io"] = (time.perf_counter() - t_search_start) * 1000.0

            dense_candidates: list[RetrievalCandidate] = []
            sparse_candidates: list[RetrievalCandidate] = []

            # Evaluate Dense Retrieval result
            if isinstance(dense_result, BaseException):
                logger.warning(f"Dense vector retrieval failed: {dense_result}")
                if not self._settings.enable_sparse_fallback:
                    raise RetrievalError(
                        message=f"Dense retrieval failure: {dense_result}",
                        details={"error": str(dense_result)},
                    ) from dense_result
                fallback_occurred = True
                fallback_reason = (
                    f"Dense retrieval unavailable ({dense_result}); fell back to sparse-only."
                )
                telemetry_collector.record_fallback("retrieval_dense", str(dense_result))
            else:
                dense_candidates = dense_result
                execution_stages.append("dense_retrieval")

            # Evaluate Sparse Retrieval result
            if isinstance(sparse_result, BaseException):
                logger.warning(f"Sparse lexical retrieval failed: {sparse_result}")
                if not self._settings.enable_dense_fallback:
                    raise RetrievalError(
                        message=f"Sparse retrieval failure: {sparse_result}",
                        details={"error": str(sparse_result)},
                    ) from sparse_result
                fallback_occurred = True
                fallback_reason = (
                    (fallback_reason + " | ") if fallback_reason else ""
                ) + f"Sparse retrieval unavailable ({sparse_result}); fell back to dense-only."
                telemetry_collector.record_fallback("retrieval_sparse", str(sparse_result))
            else:
                sparse_candidates = sparse_result
                execution_stages.append("sparse_retrieval")

            # Verify at least one retrieval stream succeeded
            if not dense_candidates and not sparse_candidates and fallback_occurred:
                raise RetrievalError(
                    message="Both dense and sparse retrieval systems failed.",
                    details={"reason": fallback_reason},
                )

            # 3. Fusion Stage
            t_fusion_start = time.perf_counter()
            with tracer.span("retrieval.fusion"):
                if dense_candidates and sparse_candidates:
                    fused_candidates = self._fusion.fuse(
                        dense_candidates=dense_candidates,
                        sparse_candidates=sparse_candidates,
                        rrf_k=self._settings.rrf_k,
                        dense_weight=self._settings.dense_weight,
                        sparse_weight=self._settings.sparse_weight,
                    )
                    strategy = "hybrid_rrf"
                    execution_stages.append("candidate_fusion")
                elif dense_candidates:
                    fused_candidates = dense_candidates
                    strategy = "dense_only_fallback" if fallback_occurred else "dense_only"
                else:
                    fused_candidates = sparse_candidates
                    strategy = "sparse_only_fallback" if fallback_occurred else "sparse_only"

            timing_ms["fusion"] = (time.perf_counter() - t_fusion_start) * 1000.0

            # 4. Deduplication Stage
            t_dedup_start = time.perf_counter()
            with tracer.span("retrieval.deduplication"):
                deduped_candidates = self._deduplicator.deduplicate(fused_candidates)
            timing_ms["deduplication"] = (time.perf_counter() - t_dedup_start) * 1000.0
            execution_stages.append("deduplication")

            # 5. Reranking Stage
            t_rerank_start = time.perf_counter()
            final_candidates = deduped_candidates

            if use_reranker and deduped_candidates:
                rerank_pool = deduped_candidates[: self._settings.candidate_pool_size]
                try:
                    async with tracer.async_span(
                        "retrieval.reranking", attributes={"candidates": len(rerank_pool)}
                    ):
                        final_candidates = await self._reranker.rerank(
                            query=retrieval_query,
                            candidates=rerank_pool,
                            top_k=retrieval_query.rerank_top_k,
                        )
                        strategy += "+reranker"
                        execution_stages.append("reranking")
                        timing_ms["reranking"] = (time.perf_counter() - t_rerank_start) * 1000.0
                        metrics_registry.record_rerank_metrics(
                            duration_ms=timing_ms["reranking"],
                            candidate_count=len(rerank_pool),
                            selected_count=len(final_candidates),
                            fallback=False,
                        )
                except Exception as ex:
                    logger.warning(
                        f"Reranker failed; gracefully falling back to fused candidates: {ex}"
                    )
                    fallback_occurred = True
                    fallback_reason = (
                        (fallback_reason + " | ") if fallback_reason else ""
                    ) + f"Reranker failed ({ex}); fell back to fused ranking."
                    telemetry_collector.record_fallback("retrieval_reranker", str(ex))
                    final_candidates = deduped_candidates
                    timing_ms["reranking"] = (time.perf_counter() - t_rerank_start) * 1000.0
                    metrics_registry.record_rerank_metrics(
                        duration_ms=timing_ms["reranking"],
                        candidate_count=len(rerank_pool),
                        selected_count=len(final_candidates),
                        fallback=True,
                    )
            else:
                timing_ms["reranking"] = 0.0

            # 6. Evidence Selection Stage
            t_select_start = time.perf_counter()
            with tracer.span("retrieval.evidence_selection"):
                selected_evidence = self._selector.select(
                    query=retrieval_query,
                    candidates=final_candidates,
                    top_k=top_k,
                    diversity_threshold=self._settings.diversity_threshold,
                    max_chunks_per_document=self._settings.max_chunks_per_document,
                )
            timing_ms["evidence_selection"] = (time.perf_counter() - t_select_start) * 1000.0
            execution_stages.append("evidence_selection")

            # 7. Validation & Guardrails Stage
            t_val_start = time.perf_counter()
            with tracer.span("retrieval.evidence_validation"):
                validated_evidence = self._validator.validate_and_sanitize(selected_evidence)
            timing_ms["validation"] = (time.perf_counter() - t_val_start) * 1000.0
            execution_stages.append("validation")

            # Compute total pipeline execution latency
            timing_ms["total"] = (time.perf_counter() - start_total) * 1000.0

            # Record telemetry metrics
            metrics_registry.record_retrieval_metrics(
                mode=strategy,
                duration_ms=timing_ms["total"],
                candidates_count=len(fused_candidates),
                fallback=fallback_occurred,
            )

            evidence_set = EvidenceSet(
                query_id=retrieval_query.id,
                query=retrieval_query,
                items=validated_evidence,
                total_candidates=len(fused_candidates),
                retrieval_strategy=strategy,
                execution_stages=execution_stages,
                timing_ms=timing_ms,
                fallback_occurred=fallback_occurred,
                fallback_reason=fallback_reason,
            )

            logger.info(
                f"Completed retrieval for query '{retrieval_query.id}' in {timing_ms['total']:.2f}ms: "
                f"strategy={strategy}, evidence_count={evidence_set.evidence_count}"
            )
            return evidence_set
