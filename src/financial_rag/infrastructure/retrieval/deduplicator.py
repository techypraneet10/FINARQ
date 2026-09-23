"""Candidate deduplication mechanism using stable chunk identity and provenance merging."""

from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalSource,
)
from financial_rag.domain.interfaces.retrieval import CandidateDeduplicatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.deduplicator")


class CandidateDeduplicator(CandidateDeduplicatorProtocol):
    """Deduplicates candidates based on (document_version_id, chunk_id) or chunk_id."""

    def deduplicate(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:
        """Merge identical candidate occurrences while aggregating scores and provenance."""
        if not candidates:
            return []

        seen: dict[tuple[str, str], RetrievalCandidate] = {}

        for cand in candidates:
            key = (str(cand.chunk.document_version_id or ""), str(cand.chunk.id))

            if key not in seen:
                seen[key] = cand
            else:
                # Merge duplicate properties into existing candidate
                existing = seen[key]

                # 1. Merge retrieval sources
                all_sources = set(existing.sources) | set(cand.sources)
                if (
                    RetrievalSource.DENSE in all_sources and RetrievalSource.SPARSE in all_sources
                ) or RetrievalSource.BOTH in all_sources:
                    existing.sources = [RetrievalSource.BOTH]
                else:
                    existing.sources = list(all_sources)

                # 2. Merge scores if present
                if existing.dense_score is None and cand.dense_score is not None:
                    existing.dense_score = cand.dense_score
                    existing.dense_rank = cand.dense_rank

                if existing.sparse_score is None and cand.sparse_score is not None:
                    existing.sparse_score = cand.sparse_score
                    existing.sparse_rank = cand.sparse_rank

                if cand.fusion_score > existing.fusion_score:
                    existing.fusion_score = cand.fusion_score

                if cand.reranker_score is not None and (
                    existing.reranker_score is None or cand.reranker_score > existing.reranker_score
                ):
                    existing.reranker_score = cand.reranker_score

                # Maintain best final score
                existing.final_score = max(existing.final_score, cand.final_score)

        deduped = list(seen.values())
        # Sort by final score descending
        deduped.sort(key=lambda c: c.final_score, reverse=True)

        logger.info(
            f"Deduplicated candidate pool from {len(candidates)} down to {len(deduped)} unique chunks"
        )
        return deduped
