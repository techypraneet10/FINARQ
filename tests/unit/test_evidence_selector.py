"""Unit tests for evidence selection, table preservation, and diversity engine."""

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    FinancialSignals,
    RetrievalCandidate,
    RetrievalQuery,
)
from financial_rag.infrastructure.retrieval.evidence_selector import EvidenceSelector


def test_evidence_selector_table_preservation() -> None:
    selector = EvidenceSelector()

    text_chunk = DocumentChunk(
        id="c-text",
        document_id="doc-1",
        page_number=1,
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content="General discussion of balance sheet items.",
    )
    table_chunk = DocumentChunk(
        id="c-table",
        document_id="doc-1",
        page_number=2,
        chunk_index=1,
        chunk_type=ChunkType.TABLE,
        content="| Total assets | $364,980 |",
        table_id="table-bs-1",
    )

    cands = [
        RetrievalCandidate(chunk=text_chunk, final_score=0.9),
        RetrievalCandidate(chunk=table_chunk, final_score=0.8),
    ]

    query = RetrievalQuery(
        raw_query="What were total assets on the balance sheet?",
        normalized_query="What were total assets on the balance sheet?",
        signals=FinancialSignals(is_table_lookup=True),
    )

    evidence = selector.select(query, cands, top_k=2)
    assert len(evidence) == 2
    # Table chunk must be preserved in selection
    chunk_ids = [e.chunk_id for e in evidence]
    assert "c-table" in chunk_ids


def test_evidence_selector_multi_period_coverage() -> None:
    selector = EvidenceSelector()

    c_2023 = DocumentChunk(
        id="c-2023",
        document_id="doc-2023",
        page_number=1,
        chunk_index=0,
        content="Revenue was $100M in 2023.",
        metadata={"fiscal_year": 2023},
    )
    c_2024 = DocumentChunk(
        id="c-2024",
        document_id="doc-2024",
        page_number=1,
        chunk_index=0,
        content="Revenue was $120M in 2024.",
        metadata={"fiscal_year": 2024},
    )

    cands = [
        RetrievalCandidate(chunk=c_2024, final_score=0.95),
        RetrievalCandidate(chunk=c_2023, final_score=0.80),
    ]

    query = RetrievalQuery(
        raw_query="Compare revenue between 2023 and 2024",
        normalized_query="Compare revenue between 2023 and 2024",
        signals=FinancialSignals(fiscal_years=[2023, 2024], is_multi_period=True),
    )

    evidence = selector.select(query, cands, top_k=2)
    assert len(evidence) == 2
    ids = [e.chunk_id for e in evidence]
    assert "c-2023" in ids
    assert "c-2024" in ids


def test_evidence_selector_document_diversity() -> None:
    selector = EvidenceSelector()

    # 10 chunks from doc-1, 2 chunks from doc-2
    cands = [
        RetrievalCandidate(
            chunk=DocumentChunk(
                id=f"c1-{i}",
                document_id="doc-1",
                page_number=i,
                chunk_index=i,
                content=f"Text 1-{i}",
            ),
            final_score=0.9 - (i * 0.01),
        )
        for i in range(10)
    ]
    cands.append(
        RetrievalCandidate(
            chunk=DocumentChunk(
                id="c2-1", document_id="doc-2", page_number=1, chunk_index=0, content="Text 2-1"
            ),
            final_score=0.85,
        )
    )

    query = RetrievalQuery(raw_query="test", normalized_query="test")
    evidence = selector.select(query, cands, top_k=5, max_chunks_per_document=3)

    # Must contain doc-2 despite doc-1 having higher scores because doc-1 cap is 3
    doc_ids = [e.document_id for e in evidence]
    assert doc_ids.count("doc-1") <= 3
    assert "doc-2" in doc_ids
