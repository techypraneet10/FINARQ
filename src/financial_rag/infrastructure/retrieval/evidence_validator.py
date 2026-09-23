"""Evidence quality validation and provenance integrity guardrails."""

from financial_rag.domain.entities.retrieval import RankedEvidence
from financial_rag.domain.interfaces.retrieval import EvidenceValidatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.evidence_validator")


class EvidenceValidator(EvidenceValidatorProtocol):
    """Enforces strict provenance, metadata, and textual completeness guardrails."""

    def validate_and_sanitize(
        self,
        evidence_items: list[RankedEvidence],
    ) -> list[RankedEvidence]:
        """Validate provenance completeness and discard corrupted/incomplete evidence items."""
        if not evidence_items:
            return []

        validated: list[RankedEvidence] = []

        for item in evidence_items:
            missing_fields: list[str] = []

            if not item.chunk_id or not str(item.chunk_id).strip():
                missing_fields.append("chunk_id")

            if not item.document_id or not str(item.document_id).strip():
                missing_fields.append("document_id")

            if item.page_number is None or item.page_number <= 0:
                missing_fields.append("page_number")

            if not item.content or not item.content.strip():
                missing_fields.append("content")

            if item.provenance is None:
                missing_fields.append("provenance")

            if missing_fields:
                logger.warning(
                    f"Rejecting invalid evidence item (chunk_id='{item.chunk_id}') missing fields: {missing_fields}"
                )
                continue

            validated.append(item)

        # Re-rank validated items in consecutive 1..N order
        reindexed: list[RankedEvidence] = []
        for rank, item in enumerate(validated, start=1):
            if item.rank != rank:
                # Reconstitute with adjusted sequential rank
                reindexed.append(
                    RankedEvidence(
                        rank=rank,
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        document_version_id=item.document_version_id,
                        page_number=item.page_number,
                        page_numbers=item.page_numbers,
                        chunk_type=item.chunk_type,
                        content=item.content,
                        section_path=item.section_path,
                        table_id=item.table_id,
                        source_block_ids=item.source_block_ids,
                        bounding_box=item.bounding_box,
                        content_hash=item.content_hash,
                        ticker=item.ticker,
                        fiscal_year=item.fiscal_year,
                        fiscal_period=item.fiscal_period,
                        retrieval_sources=item.retrieval_sources,
                        dense_score=item.dense_score,
                        sparse_score=item.sparse_score,
                        fusion_score=item.fusion_score,
                        reranker_score=item.reranker_score,
                        final_score=item.final_score,
                        provenance=item.provenance,
                        page_id=item.page_id,
                        metadata=item.metadata,
                    )
                )
            else:
                reindexed.append(item)

        return reindexed
