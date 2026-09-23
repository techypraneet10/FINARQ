"""Unit tests for evidence quality validation guardrails."""

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.retrieval import RankedEvidence, RetrievalSource
from financial_rag.domain.entities.value_objects import ProvenanceLineage
from financial_rag.infrastructure.retrieval.evidence_validator import EvidenceValidator


def test_evidence_validator_valid_items() -> None:
    validator = EvidenceValidator()

    prov = ProvenanceLineage(
        document_id="doc-1",
        document_version_id="ver-1",
        page_numbers=[1],
        chunk_id="chunk-1",
    )
    item = RankedEvidence(
        rank=1,
        chunk_id="chunk-1",
        document_id="doc-1",
        document_version_id="ver-1",
        page_number=1,
        page_numbers=[1],
        chunk_type=ChunkType.TEXT,
        content="Valid content string",
        section_path="Section A",
        table_id=None,
        source_block_ids=[],
        bounding_box=None,
        content_hash="abc",
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
        retrieval_sources=[RetrievalSource.BOTH],
        dense_score=0.9,
        sparse_score=0.9,
        fusion_score=0.95,
        reranker_score=0.95,
        final_score=0.95,
        provenance=prov,
    )

    validated = validator.validate_and_sanitize([item])
    assert len(validated) == 1
    assert validated[0].chunk_id == "chunk-1"


def test_evidence_validator_rejection_of_corrupted() -> None:
    validator = EvidenceValidator()

    prov = ProvenanceLineage(document_id="doc-1", document_version_id="ver-1", page_numbers=[1])

    # Corrupted item 1: empty chunk_id
    corrupted_1 = RankedEvidence(
        rank=1,
        chunk_id="",
        document_id="doc-1",
        document_version_id="ver-1",
        page_number=1,
        page_numbers=[1],
        chunk_type=ChunkType.TEXT,
        content="Text",
        section_path="",
        table_id=None,
        source_block_ids=[],
        bounding_box=None,
        content_hash="abc",
        ticker=None,
        fiscal_year=None,
        fiscal_period=None,
        retrieval_sources=[RetrievalSource.DENSE],
        dense_score=0.9,
        sparse_score=None,
        fusion_score=0.9,
        reranker_score=None,
        final_score=0.9,
        provenance=prov,
    )

    # Valid item 2
    valid_2 = RankedEvidence(
        rank=2,
        chunk_id="chunk-2",
        document_id="doc-1",
        document_version_id="ver-1",
        page_number=2,
        page_numbers=[2],
        chunk_type=ChunkType.TEXT,
        content="Valid text",
        section_path="",
        table_id=None,
        source_block_ids=[],
        bounding_box=None,
        content_hash="xyz",
        ticker=None,
        fiscal_year=None,
        fiscal_period=None,
        retrieval_sources=[RetrievalSource.SPARSE],
        dense_score=None,
        sparse_score=0.8,
        fusion_score=0.8,
        reranker_score=None,
        final_score=0.8,
        provenance=prov,
    )

    validated = validator.validate_and_sanitize([corrupted_1, valid_2])
    assert len(validated) == 1
    # valid_2 should be retained and reindexed to rank 1
    assert validated[0].chunk_id == "chunk-2"
    assert validated[0].rank == 1
