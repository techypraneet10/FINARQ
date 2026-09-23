"""End-to-end integration test for the full pipeline: Retrieval -> Reasoning -> Answer Synthesis."""

import pytest

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.application.reasoning.service import ReasoningService
from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.config.settings import RetrievalSettings
from financial_rag.domain.entities.answer import AnswerRequest, AnswerStatus, ResponseStyle
from financial_rag.infrastructure.llm.answerability_gate import DeterministicAnswerabilityGate
from financial_rag.infrastructure.llm.cache import InMemoryAnswerCache
from financial_rag.infrastructure.llm.context_builder import DeterministicContextBuilder
from financial_rag.infrastructure.llm.fake_provider import FakeLLMProvider
from financial_rag.infrastructure.llm.prompt_builder import VersionedPromptBuilder
from financial_rag.infrastructure.llm.renderer import DeterministicResponseRenderer
from financial_rag.infrastructure.llm.validator import DeterministicAnswerValidator
from financial_rag.infrastructure.reasoning.answerability import DeterministicAnswerabilityEvaluator
from financial_rag.infrastructure.reasoning.calculator import DeterministicFinancialCalculator
from financial_rag.infrastructure.reasoning.citation_generator import DeterministicCitationGenerator
from financial_rag.infrastructure.reasoning.citation_validator import DeterministicCitationValidator
from financial_rag.infrastructure.reasoning.claim_builder import DeterministicClaimBuilder
from financial_rag.infrastructure.reasoning.conflict_detector import DeterministicConflictDetector
from financial_rag.infrastructure.reasoning.fact_extractor import DeterministicFactExtractor
from financial_rag.infrastructure.reasoning.grounding_validator import (
    DeterministicGroundingValidator,
)
from financial_rag.infrastructure.reasoning.period_normalizer import FiscalPeriodNormalizer
from financial_rag.infrastructure.reasoning.planner import DeterministicReasoningPlanner
from financial_rag.infrastructure.reasoning.value_parser import FinancialValueParser
from financial_rag.infrastructure.retrieval.deduplicator import CandidateDeduplicator
from financial_rag.infrastructure.retrieval.dense_retriever import QdrantDenseRetriever
from financial_rag.infrastructure.retrieval.evidence_selector import EvidenceSelector
from financial_rag.infrastructure.retrieval.evidence_validator import EvidenceValidator
from financial_rag.infrastructure.retrieval.fusion import ReciprocalRankFusion
from financial_rag.infrastructure.retrieval.query_analyzer import FinancialQueryAnalyzer
from financial_rag.infrastructure.retrieval.reranker import MockReranker
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever


@pytest.mark.asyncio
async def test_end_to_end_answer_orchestration_pipeline() -> None:
    from uuid import uuid4

    from financial_rag.common.types import ChunkType
    from financial_rag.domain.entities.models import DocumentChunk

    table_chunk = DocumentChunk(
        id=str(uuid4()),
        document_id=str(uuid4()),
        document_version_id=str(uuid4()),
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

    class MockEmbeddingProvider:
        async def embed_query(self, text: str) -> list[float]:
            return [0.1] * 1536

    class MockVectorStore:
        async def search(self, *args, **kwargs):
            return []

    dense_retriever = QdrantDenseRetriever(
        embedding_provider=MockEmbeddingProvider(),  # type: ignore[arg-type]
        vector_store=MockVectorStore(),  # type: ignore[arg-type]
        expected_dimension=1536,
    )
    retrieval_service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=dense_retriever,
        sparse_retriever=bm25_retriever,
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
        retrieval_settings=RetrievalSettings(final_top_k=5),
    )

    # 2. Setup Reasoning Layer
    val_parser = FinancialValueParser()
    per_normalizer = FiscalPeriodNormalizer()
    fact_extractor = DeterministicFactExtractor(
        value_parser=val_parser, period_normalizer=per_normalizer
    )
    calculator = DeterministicFinancialCalculator()
    conflict_detector = DeterministicConflictDetector()
    planner = DeterministicReasoningPlanner()
    claim_builder = DeterministicClaimBuilder()
    citation_gen = DeterministicCitationGenerator()
    citation_val = DeterministicCitationValidator()
    grounding_val = DeterministicGroundingValidator()
    answerability_eval = DeterministicAnswerabilityEvaluator()

    reasoning_service = ReasoningService(
        retrieval_service=retrieval_service,
        planner=planner,
        fact_extractor=fact_extractor,
        calculator=calculator,
        conflict_detector=conflict_detector,
        claim_builder=claim_builder,
        citation_generator=citation_gen,
        citation_validator=citation_val,
        grounding_validator=grounding_val,
        answerability_evaluator=answerability_eval,
    )

    # 3. Setup Answer Orchestration Layer
    context_builder = DeterministicContextBuilder()
    prompt_builder = VersionedPromptBuilder()
    gate = DeterministicAnswerabilityGate()
    validator = DeterministicAnswerValidator()
    renderer = DeterministicResponseRenderer()
    cache = InMemoryAnswerCache()
    fake_llm = FakeLLMProvider(mode="valid")

    answer_service = AnswerOrchestrationService(
        reasoning_service=reasoning_service,
        llm_provider=fake_llm,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        answerability_gate=gate,
        validator=validator,
        renderer=renderer,
        cache=cache,
        max_retries=1,
    )

    # 4. Execute End-to-End Query
    req = AnswerRequest(
        query="What was Apple's total net sales growth from 2023 to 2024?",
        response_style=ResponseStyle.STANDARD,
        include_citations=True,
    )

    response = await answer_service.generate_answer(req)

    # 5. Assert Verifications
    assert response.status == AnswerStatus.COMPLETED
    assert "Apple" in response.answer_text
    assert len(response.citations) > 0
    assert len(response.calculations) > 0
    assert response.calculations[0].success is True
    assert "+2.02%" in response.calculations[0].display_result
    assert response.confidence_score >= 0.85
    assert response.metadata["cache_hit"] is False

    # 6. Test Cache Hit on repeated identical query
    cached_response = await answer_service.generate_answer(req)
    assert cached_response.metadata["cache_hit"] is True
