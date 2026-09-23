"""Citation verification engine validating citations against retrieved evidence chunks."""

from financial_rag.domain.entities.reasoning import Citation
from financial_rag.domain.entities.retrieval import RankedEvidence
from financial_rag.domain.interfaces.reasoning import CitationValidatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.citation_validator")


class DeterministicCitationValidator(CitationValidatorProtocol):
    """Validates citations against the retrieved evidence pool to prevent hallucinated citations."""

    def validate_citations(
        self,
        citations: list[Citation],
        evidence_items: list[RankedEvidence],
    ) -> list[Citation]:
        """Validate presence and consistency of each citation against evidence."""
        validated: list[Citation] = []
        evidence_map = {str(e.chunk_id): e for e in evidence_items}

        for cit in citations:
            matched_evidence = evidence_map.get(cit.chunk_id)
            if not matched_evidence:
                validated.append(
                    Citation(
                        citation_id=cit.citation_id,
                        claim_id=cit.claim_id,
                        document_id=cit.document_id,
                        document_version_id=cit.document_version_id,
                        page_number=cit.page_number,
                        page_numbers=cit.page_numbers,
                        chunk_id=cit.chunk_id,
                        table_id=cit.table_id,
                        section_path=cit.section_path,
                        ticker=cit.ticker,
                        source_excerpt=cit.source_excerpt,
                        bounding_box=cit.bounding_box,
                        citation_type=cit.citation_type,
                        verified=False,
                        validation_notes=f"Referenced chunk '{cit.chunk_id}' not found in retrieved evidence set.",
                    )
                )
                continue

            # Verify document ID consistency
            if cit.document_id and matched_evidence.document_id != cit.document_id:
                validated.append(
                    Citation(
                        citation_id=cit.citation_id,
                        claim_id=cit.claim_id,
                        document_id=cit.document_id,
                        document_version_id=cit.document_version_id,
                        page_number=cit.page_number,
                        page_numbers=cit.page_numbers,
                        chunk_id=cit.chunk_id,
                        table_id=cit.table_id,
                        section_path=cit.section_path,
                        ticker=cit.ticker,
                        source_excerpt=cit.source_excerpt,
                        bounding_box=cit.bounding_box,
                        citation_type=cit.citation_type,
                        verified=False,
                        validation_notes=f"Document ID mismatch: cited '{cit.document_id}', found '{matched_evidence.document_id}'.",
                    )
                )
                continue

            # Verify page number
            if (
                cit.page_number not in matched_evidence.page_numbers
                and cit.page_number != matched_evidence.page_number
            ):
                validated.append(
                    Citation(
                        citation_id=cit.citation_id,
                        claim_id=cit.claim_id,
                        document_id=cit.document_id,
                        document_version_id=cit.document_version_id,
                        page_number=cit.page_number,
                        page_numbers=cit.page_numbers,
                        chunk_id=cit.chunk_id,
                        table_id=cit.table_id,
                        section_path=cit.section_path,
                        ticker=cit.ticker,
                        source_excerpt=cit.source_excerpt,
                        bounding_box=cit.bounding_box,
                        citation_type=cit.citation_type,
                        verified=False,
                        validation_notes=f"Page number mismatch: cited page {cit.page_number}, chunk belongs to {matched_evidence.page_numbers}.",
                    )
                )
                continue

            # All checks passed
            validated.append(
                Citation(
                    citation_id=cit.citation_id,
                    claim_id=cit.claim_id,
                    document_id=cit.document_id,
                    document_version_id=cit.document_version_id,
                    page_number=cit.page_number,
                    page_numbers=cit.page_numbers,
                    chunk_id=cit.chunk_id,
                    table_id=cit.table_id,
                    section_path=cit.section_path,
                    ticker=cit.ticker,
                    source_excerpt=cit.source_excerpt,
                    bounding_box=cit.bounding_box,
                    citation_type=cit.citation_type,
                    verified=True,
                    validation_notes="Verified valid against evidence provenance.",
                )
            )

        logger.info(
            f"Validated {len(validated)} citations ({sum(1 for c in validated if c.verified)} verified)"
        )
        return validated
