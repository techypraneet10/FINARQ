"""End-to-end integration tests for the complete deterministic reasoning pipeline."""

import pytest

from financial_rag.application.reasoning.service import ReasoningService
from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.reasoning import AnswerabilityStatus, GroundingStatus
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever


@pytest.mark.asyncio
async def test_multi_period_growth_reasoning_pipeline() -> None:

    # 1. Index 3-year Apple financial table
    table_chunk = DocumentChunk(
        id="e2e-chunk-ops-table",
        document_id="doc-apple-10k-2024",
        document_version_id="ver-apple-2024-v1",
        page_number=45,
        chunk_index=0,
        chunk_type=ChunkType.TABLE,
        content="""### Consolidated Statements of Operations (in millions, except per share amounts)
| Metric | 2024 | 2023 | 2022 |
| --- | --- | --- | --- |
| Total net sales | 391,035 | 383,285 | 394,328 |
| Operating income | 123,217 | 114,301 | 119,437 |
| Net income | 93,736 | 96,995 | 99,803 |
""",
        section_path="Item 8 > Financial Statements",
        metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
    )
    await bm25_retriever.index_chunks([table_chunk])

    # Instantiate ReasoningService with the retrieval service dependency
    from financial_rag.api.dependencies import get_retrieval_service
    from financial_rag.config.settings import get_settings
    from financial_rag.infrastructure.embeddings import get_embedding_provider
    from financial_rag.infrastructure.retrieval import (
        CandidateDeduplicator,
        EvidenceSelector,
        EvidenceValidator,
        FinancialQueryAnalyzer,
        MockReranker,
        QdrantDenseRetriever,
        ReciprocalRankFusion,
    )
    from financial_rag.infrastructure.vector_store import get_vector_store

    settings = get_settings()
    emb = get_embedding_provider(settings.embedding)
    vdb = get_vector_store(settings.qdrant)
    dense = QdrantDenseRetriever(
        embedding_provider=emb, vector_store=vdb, expected_dimension=settings.embedding.dimension
    )

    r_service = get_retrieval_service(
        analyzer=FinancialQueryAnalyzer(),
        dense_retriever=dense,
        sparse_retriever=bm25_retriever,
        fusion_strategy=ReciprocalRankFusion(default_k=60),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
        settings=settings,
    )

    reasoning_service = ReasoningService(retrieval_service=r_service)

    # Execute growth inquiry: 2023 to 2024 revenue growth
    package = await reasoning_service.reason(
        raw_query="What was Apple's total net sales growth from 2023 to 2024?",
        use_reranker=False,
    )

    assert package.answerability == AnswerabilityStatus.ANSWERABLE
    assert len(package.calculations) >= 1

    growth_calc = package.calculations[0]
    assert growth_calc.success
    # ((391,035 - 383,285) / 383,285) * 100 = 7,750 / 383,285 * 100 ~= 2.02%
    assert "+2.02%" in growth_calc.display_result or "2.02" in str(growth_calc.rounded_result)

    # Check grounding and citations
    assert package.grounding_validation is not None
    assert package.grounding_validation.status == GroundingStatus.GROUNDED
    assert package.grounding_validation.grounded_claims >= 1
    assert len(package.citations) >= 1
    assert all(cit.verified for cit in package.citations)
