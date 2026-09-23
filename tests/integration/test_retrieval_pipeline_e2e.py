"""End-to-end integration tests for document ingestion through hybrid retrieval and evidence selection."""

import pymupdf
import pytest

from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.common.types import DocumentType
from financial_rag.config.settings import QdrantSettings
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.normalization.document_normalizer import DocumentNormalizer
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from financial_rag.infrastructure.retrieval import (
    BM25SparseRetriever,
    CandidateDeduplicator,
    EvidenceSelector,
    EvidenceValidator,
    FinancialQueryAnalyzer,
    MockReranker,
    QdrantDenseRetriever,
    ReciprocalRankFusion,
)
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter


def _create_sample_financial_pdf() -> bytes:
    doc = pymupdf.open()
    page1 = doc.new_page(width=612, height=792)

    page1.insert_text(
        (50, 50),
        "ITEM 1A. RISK FACTORS\n"
        "Our operations are subject to macroeconomic challenges, supply chain risks, and AI competition.\n\n"
        "ITEM 8. FINANCIAL STATEMENTS\n"
        "Consolidated Statements of Operations\n"
        "Total net sales in fiscal 2024 were $391,035 million compared to $383,285 million in 2023.\n"
        "Operating income was $123,198 million in 2024.\n",
        fontsize=11,
    )
    pdf_bytes = doc.write()
    doc.close()
    return bytes(pdf_bytes)


@pytest.mark.asyncio
async def test_e2e_ingestion_and_hybrid_retrieval() -> None:
    # 1. Setup shared infrastructure
    embedding_provider = MockEmbeddingProvider(dimension=1536)
    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(location=":memory:", collection_name="e2e_financial_chunks")
    )
    sparse_retriever = BM25SparseRetriever()

    # 2. Build Ingestion Pipeline
    pipeline = IngestionPipeline(
        parser=PyMuPDFParser(),
        table_extractor=FinancialTableExtractor(normalizer=FinancialTableNormalizer()),
        table_normalizer=FinancialTableNormalizer(),
        normalizer=DocumentNormalizer(),
        structure_detector=FinancialStructureDetector(),
        chunker=StructureAwareChunker(),
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        sparse_retriever=sparse_retriever,
    )

    pdf_content = _create_sample_financial_pdf()
    _pages, chunks = await pipeline.execute(
        content=pdf_content,
        document_id="doc-e2e-aapl",
        version_id="ver-e2e-aapl-v1",
        document_type=DocumentType.SEC_10K,
        filename="AAPL_2024_10K.pdf",
    )
    assert len(chunks) > 0

    # 3. Build Retrieval Service
    retrieval_service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=QdrantDenseRetriever(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            expected_dimension=1536,
        ),
        sparse_retriever=sparse_retriever,
        fusion_strategy=ReciprocalRankFusion(default_k=60),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
    )

    # 4. Search for net sales in 2024
    evidence_set = await retrieval_service.search(
        raw_query="What were total net sales in 2024?",
        filters=RetrievalFilter(document_ids=["doc-e2e-aapl"]),
        top_k=3,
        use_reranker=True,
    )

    assert evidence_set.evidence_count > 0
    top_item = evidence_set.items[0]
    assert (
        "391,035" in top_item.content
        or "391035" in top_item.content
        or "sales" in top_item.content.lower()
    )
    assert top_item.document_id == "doc-e2e-aapl"
    assert top_item.document_version_id == "ver-e2e-aapl-v1"
    assert top_item.page_number == 1
    assert top_item.provenance is not None
    assert top_item.provenance.document_id == "doc-e2e-aapl"
