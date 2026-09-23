"""Evidence selection engine balancing relevance, structural diversity, and table preservation."""

import hashlib
from collections import defaultdict

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.retrieval import (
    RankedEvidence,
    RetrievalCandidate,
    RetrievalQuery,
)
from financial_rag.domain.interfaces.retrieval import EvidenceSelectorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.evidence_selector")


class EvidenceSelector(EvidenceSelectorProtocol):
    """Selects top evidence respecting financial structures, multi-period requirements, and diversity."""

    def select(
        self,
        query: RetrievalQuery,
        candidates: list[RetrievalCandidate],
        top_k: int = 10,
        diversity_threshold: float = 0.8,
        max_chunks_per_document: int = 5,
    ) -> list[RankedEvidence]:
        """Select top-ranked evidence with diversity and structural guarantees."""
        if not candidates:
            return []

        limit = min(top_k, len(candidates))

        # Track diversity constraints
        selected_candidates: list[RetrievalCandidate] = []
        doc_counts: dict[str, int] = defaultdict(int)
        represented_years: set[int] = set()
        represented_tables: set[str] = set()

        # Step 1: Multi-period query handling
        # If the query is multi-period (e.g. 2023 vs 2024), ensure top candidate for each target year is prioritized
        target_years = set(query.signals.fiscal_years)
        if query.signals.is_multi_period and len(target_years) > 1:
            for year in sorted(target_years):
                for cand in candidates:
                    cand_year = cand.chunk.metadata.get("fiscal_year")
                    if not cand_year and str(year) in cand.chunk.content:
                        cand_year = year

                    if cand_year == year and cand not in selected_candidates:
                        selected_candidates.append(cand)
                        doc_counts[str(cand.chunk.document_id)] += 1
                        represented_years.add(year)
                        break

        # Step 2: Table preservation for table / numerical / balance inquiries
        if query.signals.is_table_lookup or query.signals.statement_types:
            for cand in candidates:
                if (
                    cand.chunk.chunk_type == ChunkType.TABLE
                    and cand not in selected_candidates
                    and len(selected_candidates) < limit
                ):
                    tid = str(cand.chunk.table_id or cand.chunk.id)
                    if tid not in represented_tables:
                        selected_candidates.append(cand)
                        doc_counts[str(cand.chunk.document_id)] += 1
                        represented_tables.add(tid)
                        break

        # Step 3: Main greedy selection respecting document diversity
        for cand in candidates:
            if len(selected_candidates) >= limit:
                break

            if cand in selected_candidates:
                continue

            doc_id = str(cand.chunk.document_id)
            if doc_counts[doc_id] >= max_chunks_per_document:
                continue

            selected_candidates.append(cand)
            doc_counts[doc_id] += 1

        # Sort final selection by final_score descending
        selected_candidates.sort(key=lambda c: float(c.final_score), reverse=True)

        # Step 4: Map into domain RankedEvidence entities with complete provenance lineage
        ranked_evidence: list[RankedEvidence] = []
        for rank, cand in enumerate(selected_candidates, start=1):
            chunk = cand.chunk
            prov = cand.provenance or chunk.get_provenance()

            content_hash = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
            meta = chunk.metadata or {}

            # Extract bounding box if present
            bb_dict = None
            if "bounding_box" in meta and isinstance(meta["bounding_box"], dict):
                bb_dict = meta["bounding_box"]

            evidence_item = RankedEvidence(
                rank=rank,
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_version_id=chunk.document_version_id,
                page_number=chunk.page_number,
                page_numbers=chunk.page_numbers or [chunk.page_number],
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                section_path=chunk.section_path,
                table_id=chunk.table_id,
                source_block_ids=chunk.source_block_ids,
                bounding_box=bb_dict,
                content_hash=content_hash,
                ticker=meta.get("ticker_symbol") or meta.get("ticker"),
                fiscal_year=meta.get("fiscal_year"),
                fiscal_period=meta.get("fiscal_period"),
                retrieval_sources=cand.sources,
                dense_score=cand.dense_score,
                sparse_score=cand.sparse_score,
                fusion_score=cand.fusion_score,
                reranker_score=cand.reranker_score,
                final_score=cand.final_score,
                provenance=prov,
                tenant_id=chunk.tenant_id,
                metadata=meta,
            )
            ranked_evidence.append(evidence_item)

        logger.info(
            f"Evidence selection returned {len(ranked_evidence)} items (top_k={top_k}) for query '{query.id}'"
        )
        return ranked_evidence
