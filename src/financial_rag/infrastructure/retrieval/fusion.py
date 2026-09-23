"""Reciprocal Rank Fusion (RRF) algorithm for multi-retrieval candidate blending."""

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalSource,
)
from financial_rag.domain.interfaces.retrieval import FusionStrategyProtocol
from financial_rag.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from financial_rag.domain.entities.models import DocumentChunk
    from financial_rag.domain.entities.value_objects import ProvenanceLineage

logger = get_logger("financial_rag.infrastructure.retrieval.fusion")


class ReciprocalRankFusion(FusionStrategyProtocol):
    """Principled rank-based fusion combining dense semantic and sparse lexical candidate pools."""

    def __init__(self, default_k: int = 60) -> None:
        self.default_k = default_k

    def fuse(
        self,
        dense_candidates: list[RetrievalCandidate],
        sparse_candidates: list[RetrievalCandidate],
        rrf_k: int | None = None,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
    ) -> list[RetrievalCandidate]:
        """Combine dense and sparse rankings using Reciprocal Rank Fusion.

        Formula:
            RRF_score(d) = (w_dense / (k + rank_dense(d))) + (w_sparse / (k + rank_sparse(d)))
        """
        k = rrf_k or self.default_k

        # Maps chunk_id -> dict with accumulated scores and best chunk reference
        combined_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "chunk": None,
                "dense_score": None,
                "dense_rank": None,
                "sparse_score": None,
                "sparse_rank": None,
                "rrf_score": 0.0,
                "sources": set(),
                "provenance": None,
            }
        )

        # 1. Process Dense candidates
        for rank, cand in enumerate(dense_candidates, start=1):
            cid = str(cand.chunk.id)
            entry = combined_data[cid]
            entry["chunk"] = cand.chunk
            entry["dense_score"] = cand.dense_score
            entry["dense_rank"] = cand.dense_rank or rank
            entry["rrf_score"] += dense_weight / (k + rank)
            entry["sources"].add(RetrievalSource.DENSE)
            if cand.provenance:
                entry["provenance"] = cand.provenance

        # 2. Process Sparse candidates
        for rank, cand in enumerate(sparse_candidates, start=1):
            cid = str(cand.chunk.id)
            entry = combined_data[cid]
            if entry["chunk"] is None:
                entry["chunk"] = cand.chunk
            entry["sparse_score"] = cand.sparse_score
            entry["sparse_rank"] = cand.sparse_rank or rank
            entry["rrf_score"] += sparse_weight / (k + rank)
            entry["sources"].add(RetrievalSource.SPARSE)
            if entry["provenance"] is None and cand.provenance:
                entry["provenance"] = cand.provenance

        if not combined_data:
            return []

        # 3. Sort candidates by RRF score descending
        sorted_entries = sorted(
            combined_data.values(), key=lambda x: float(x["rrf_score"]), reverse=True
        )

        # 4. Normalize RRF scores to [0.0, 1.0] for consistent downstream representation
        max_rrf = sorted_entries[0]["rrf_score"] if sorted_entries else 1.0
        norm_scale = max_rrf if max_rrf > 0 else 1.0

        fused_candidates: list[RetrievalCandidate] = []
        for entry in sorted_entries:
            chunk: DocumentChunk = entry["chunk"]
            sources_set: set[RetrievalSource] = entry["sources"]

            if len(sources_set) > 1 or (
                RetrievalSource.DENSE in sources_set and RetrievalSource.SPARSE in sources_set
            ):
                final_sources = [RetrievalSource.BOTH]
            else:
                final_sources = list(sources_set)

            norm_score = float(entry["rrf_score"]) / norm_scale
            prov: ProvenanceLineage = entry["provenance"] or chunk.get_provenance()

            candidate = RetrievalCandidate(
                chunk=chunk,
                dense_score=entry["dense_score"],
                dense_rank=entry["dense_rank"],
                sparse_score=entry["sparse_score"],
                sparse_rank=entry["sparse_rank"],
                fusion_score=norm_score,
                reranker_score=None,
                final_score=norm_score,
                sources=final_sources,
                provenance=prov,
            )
            fused_candidates.append(candidate)

        logger.info(
            f"RRF fusion blended {len(dense_candidates)} dense + {len(sparse_candidates)} sparse "
            f"into {len(fused_candidates)} unique candidates"
        )
        return fused_candidates
