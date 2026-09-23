"""Deterministic citation generation layer mapping claims and facts to verifiable source evidence."""

from uuid import uuid4

from financial_rag.domain.entities.reasoning import (
    Citation,
    CitationType,
    Claim,
    FinancialFact,
)
from financial_rag.domain.entities.retrieval import RankedEvidence
from financial_rag.domain.interfaces.reasoning import CitationGeneratorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.citation_generator")


class DeterministicCitationGenerator(CitationGeneratorProtocol):
    """Constructs verifiable Citation objects from factual provenance and evidence lineage."""

    def generate_citations(
        self,
        claims: list[Claim],
        facts: list[FinancialFact],
        evidence_items: list[RankedEvidence],
    ) -> list[Citation]:
        """Generate verifiable citations for each claim referencing source facts and evidence."""
        citations: list[Citation] = []
        facts_by_id = {f.fact_id: f for f in facts}
        evidence_by_chunk_id = {str(e.chunk_id): e for e in evidence_items}

        for claim in claims:
            for fact_id in claim.source_fact_ids:
                fact = facts_by_id.get(fact_id)
                if not fact:
                    continue

                evidence = evidence_by_chunk_id.get(
                    fact.source_evidence_id
                ) or evidence_by_chunk_id.get(fact.chunk_id)

                cit_type = CitationType.DIRECT_SOURCE
                if claim.claim_type == "calculated":
                    cit_type = CitationType.CALCULATION_SOURCE
                elif "table" in fact.extraction_method:
                    cit_type = CitationType.TABLE_CELL

                # Derive exact bounding box and page numbers
                page_numbers = evidence.page_numbers if evidence else [fact.page_number]
                bbox = evidence.bounding_box if evidence else fact.bounding_box

                citation_id = str(uuid4())
                citations.append(
                    Citation(
                        citation_id=citation_id,
                        claim_id=claim.claim_id,
                        document_id=fact.document_id,
                        document_version_id=fact.document_version_id,
                        page_number=fact.page_number,
                        page_numbers=page_numbers,
                        chunk_id=fact.chunk_id,
                        table_id=fact.table_id,
                        section_path=fact.section_path
                        or (evidence.section_path if evidence else ""),
                        ticker=fact.ticker,
                        source_excerpt=fact.source_text[:300],
                        bounding_box=bbox,
                        citation_type=cit_type,
                        verified=evidence is not None,
                        validation_notes="Verified against retrieved evidence pool."
                        if evidence
                        else "Evidence chunk not found in active pool.",
                    )
                )

        logger.info(f"Generated {len(citations)} source citations")
        return citations
