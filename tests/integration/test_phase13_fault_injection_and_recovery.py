"""Phase 13 Comprehensive Fault Injection and Recovery Integration Tests.

Validates that the Financial RAG Platform:
1. Detects failures across dependencies (Postgres, Qdrant, Storage, Embedding, LLM).
2. Degrades gracefully to safe fallbacks (BM25 sparse fallback, deterministic calculation fallback).
3. Isolates faults using circuit breakers and fast-fails during outages.
4. Recovers automatically when downstream dependencies resume healthy operation.
5. Accurately propagates W3C distributed trace context end-to-end.
6. Handles streaming disconnects and document corruption cleanly.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.domain.entities.answer import AnswerRequest, AnswerStatus, ResponseStyle
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    CalculationResult,
    FinancialFact,
    FinancialScale,
    FinancialValue,
    FiscalPeriod,
    GroundingStatus,
    GroundingValidationResult,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.domain.entities.retrieval import RetrievalQuery
from financial_rag.domain.exceptions import (
    DocumentParsingError,
    InfrastructureError,
    LLMTimeoutError,
    StorageError,
)
from financial_rag.infrastructure.observability.error_classifier import ErrorClassifier
from financial_rag.infrastructure.observability.telemetry import telemetry_collector
from financial_rag.infrastructure.observability.tracer import tracer
from financial_rag.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)
from financial_rag.infrastructure.resilience.registry import circuit_breaker_registry


@pytest.fixture(autouse=True)
def reset_resilience_and_telemetry():
    """Reset circuit breakers and metrics before each test run."""
    circuit_breaker_registry.reset_all()
    yield
    circuit_breaker_registry.reset_all()


# =========================================================================
# 1. POSTGRESQL DEPENDENCY DEGRADATION & RECOVERY
# =========================================================================
@pytest.mark.asyncio
async def test_database_degradation_and_recovery_readiness(app, async_client: AsyncClient):
    """Test readiness endpoint behavior when database goes down and comes back up."""
    from financial_rag.api.dependencies import get_db_session_manager

    mock_db = AsyncMock()
    mock_db.health_check = AsyncMock(return_value=True)
    app.dependency_overrides[get_db_session_manager] = lambda: mock_db

    try:
        # Baseline: Healthy ready probe
        resp1 = await async_client.get("/ready")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["checks"]["database"]["status"] == "healthy"

        # Fault Injection: DB health check fails
        mock_db.health_check = AsyncMock(return_value=False)
        resp_failing = await async_client.get("/ready")
        assert resp_failing.status_code == 200  # Readiness returns degraded component
        data_failing = resp_failing.json()
        assert data_failing["checks"]["database"]["status"] == "unhealthy"

        # Check telemetry snapshot records the degradation
        snapshot = telemetry_collector.get_telemetry_snapshot()
        db_record = snapshot["dependency_health"].get("database")
        assert db_record is not None
        assert db_record["status"] == "unhealthy"
        assert db_record["fallback_active"] is True

        # Recovery: Restore DB
        mock_db.health_check = AsyncMock(return_value=True)
        resp_recovered = await async_client.get("/ready")
        assert resp_recovered.status_code == 200
        data_recovered = resp_recovered.json()
        assert data_recovered["checks"]["database"]["status"] == "healthy"

    finally:
        app.dependency_overrides.pop(get_db_session_manager, None)


# =========================================================================
# 2. QDRANT VECTOR DB FAILURE & SPARSE BM25 FALLBACK
# =========================================================================
@pytest.mark.asyncio
async def test_qdrant_vector_failure_and_sparse_fallback():
    """Test that dense retriever failure gracefully falls back to sparse BM25 retrieval."""
    mock_analyzer = MagicMock()
    query_obj = RetrievalQuery(
        raw_query="What was Apple's Q3 2024 revenue?",
        normalized_query="apple q3 2024 revenue",
    )
    mock_analyzer.analyze.return_value = query_obj

    # Dense retriever fails with connection error
    mock_dense = AsyncMock()
    mock_dense.retrieve.side_effect = InfrastructureError("Qdrant connection refused")

    from financial_rag.common.types import ChunkType
    from financial_rag.domain.entities.models import DocumentChunk
    from financial_rag.domain.entities.retrieval import (
        RankedEvidence,
        RetrievalCandidate,
        RetrievalSource,
    )

    doc_id = str(uuid4())
    ver_id = str(uuid4())
    chunk = DocumentChunk(
        id="chunk-sparse-001",
        document_id=doc_id,
        document_version_id=ver_id,
        tenant_id="default_tenant",
        page_number=1,
        chunk_index=0,
        content="Apple announced revenue of $85.8 billion for Q3 2024.",
        chunk_type=ChunkType.TEXT,
    )
    mock_candidate = RetrievalCandidate(
        chunk=chunk,
        sparse_score=0.92,
        final_score=0.92,
        sources=[RetrievalSource.SPARSE],
    )
    mock_sparse = AsyncMock()
    mock_sparse.retrieve.return_value = [mock_candidate]

    mock_fusion = MagicMock()
    mock_dedup = MagicMock()
    mock_dedup.deduplicate.return_value = [mock_candidate]

    mock_reranker = AsyncMock()
    mock_reranker.rerank.return_value = [mock_candidate]

    mock_selector = MagicMock()
    ranked_item = RankedEvidence(
        rank=1,
        chunk_id="chunk-sparse-001",
        document_id=doc_id,
        document_version_id=ver_id,
        page_number=1,
        page_numbers=[1],
        chunk_type=ChunkType.TEXT,
        content=chunk.content,
        section_path="Item 1",
        table_id=None,
        source_block_ids=[],
        bounding_box=None,
        content_hash="abc123hash",
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="Q3",
        retrieval_sources=[RetrievalSource.SPARSE],
        dense_score=None,
        sparse_score=0.92,
        fusion_score=0.92,
        reranker_score=None,
        final_score=0.92,
        provenance=chunk.get_provenance(),
    )
    mock_selector.select.return_value = [ranked_item]

    mock_validator = MagicMock()
    mock_validator.validate_and_sanitize.return_value = [ranked_item]

    service = RetrievalService(
        query_analyzer=mock_analyzer,
        dense_retriever=mock_dense,
        sparse_retriever=mock_sparse,
        fusion_strategy=mock_fusion,
        deduplicator=mock_dedup,
        reranker=mock_reranker,
        evidence_selector=mock_selector,
        evidence_validator=mock_validator,
    )

    evidence_set = await service.search(raw_query="What was Apple's Q3 2024 revenue?")

    assert evidence_set.fallback_occurred is True
    assert "Dense retrieval unavailable" in (evidence_set.fallback_reason or "")
    assert evidence_set.evidence_count == 1
    assert evidence_set.items[0].chunk_id == "chunk-sparse-001"

    # Verify telemetry fallback recorded
    snapshot = telemetry_collector.get_telemetry_snapshot()
    dense_fallbacks = [
        f for f in snapshot["recent_fallbacks"] if f["component"] == "retrieval_dense"
    ]
    assert len(dense_fallbacks) >= 1


# =========================================================================
# 3. LLM FAILURE, CIRCUIT BREAKER TRIPPING & RECOVERY
# =========================================================================
@pytest.mark.asyncio
async def test_llm_failure_circuit_breaker_tripping_and_recovery():
    """Test that consecutive LLM failures trip the circuit breaker and safely recover."""
    breaker = CircuitBreaker(
        service_name="test_llm_provider",
        failure_threshold=2,
        recovery_timeout_seconds=0.1,
        half_open_success_threshold=1,
    )

    assert breaker.state == CircuitBreakerState.CLOSED

    # Failure 1
    with pytest.raises(LLMTimeoutError):
        await breaker.execute(
            AsyncMock(side_effect=LLMTimeoutError(provider="openai", timeout_seconds=10.0))
        )
    assert breaker.state == CircuitBreakerState.CLOSED

    # Failure 2 -> Trips to OPEN
    with pytest.raises(LLMTimeoutError):
        await breaker.execute(
            AsyncMock(side_effect=LLMTimeoutError(provider="openai", timeout_seconds=10.0))
        )
    assert breaker.state == CircuitBreakerState.OPEN

    # Subsequent execution fast-fails with CircuitBreakerOpenError without calling downstream
    mock_fn = AsyncMock()
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await breaker.execute(mock_fn)
    assert not mock_fn.called
    assert "is OPEN" in str(exc_info.value)

    # Wait for cooldown
    await asyncio.sleep(0.15)
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    # Successful trial in HALF_OPEN recovers breaker to CLOSED
    recovered_fn = AsyncMock(return_value="recovered_response")
    result = await breaker.execute(recovered_fn)
    assert result == "recovered_response"
    assert breaker.state == CircuitBreakerState.CLOSED


# =========================================================================
# 4. LLM SYNTHESIS VALIDATION FAILURE & SAFE DETERMINISTIC FALLBACK
# =========================================================================
@pytest.mark.asyncio
async def test_llm_synthesis_validation_failure_fallback():
    """Test that when LLM returns invalid output, the pipeline falls back to deterministic rendering."""
    # Build a mock answer package
    val = FinancialValue(
        raw_value="85.8B",
        display_value="$85.8B",
        numeric_value=Decimal("85800000000"),
        unscaled_value=Decimal("85.8"),
        currency="USD",
        scale=FinancialScale.BILLIONS,
        unit="USD",
    )
    period = FiscalPeriod(fiscal_year=2024, period_type="Q3")
    fact = FinancialFact(
        fact_id="fact-1",
        metric="Revenue",
        value=val,
        period=period,
        company="Apple Inc.",
        ticker="AAPL",
        document_id=str(uuid4()),
        document_version_id=str(uuid4()),
        page_number=1,
        chunk_id="chunk-1",
        table_id=None,
        source_evidence_id="ev-1",
        extraction_method="table_cell",
        confidence=0.99,
        source_text="$85.8 billion",
    )
    calc = CalculationResult(
        calculation_id="calc-1",
        operation=ReasoningOperation.DIRECT_LOOKUP,
        formula="Lookup(Revenue, Q3 2024)",
        inputs=[],
        input_fact_ids=["fact-1"],
        raw_result=Decimal("85800000000"),
        rounded_result=Decimal("85.8"),
        display_result="$85.8B",
        unit="USD",
        currency="USD",
        success=True,
    )
    package = AnswerPackage(
        package_id="pkg-001",
        query_id="q-001",
        raw_query="What was Apple's Q3 2024 revenue?",
        normalized_query="apple q3 2024 revenue",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="Found verified metric.",
        reasoning_plan=ReasoningPlan(
            plan_id="plan-1",
            query="apple q3 2024 revenue",
            operations=[ReasoningOperation.DIRECT_LOOKUP],
            target_metrics=["Revenue"],
            target_periods=["Q3 2024"],
            target_companies=["Apple Inc."],
            required_fact_keys=["Revenue:Q3 2024"],
            steps_description=["Lookup Revenue for Q3 2024"],
        ),
        facts=[fact],
        calculations=[calc],
        reasoning_trace=[],
        claims=[],
        citations=[],
        evidence=[],
        conflicts=[],
        missing_facts=[],
        grounding_validation=GroundingValidationResult(
            status=GroundingStatus.GROUNDED,
            total_claims=1,
            grounded_claims=1,
            ungrounded_claims=0,
            conflicting_claims=0,
            unverified_citations=0,
        ),
        confidence_score=1.0,
    )

    mock_reasoning_svc = AsyncMock()
    mock_reasoning_svc.reason.return_value = package

    # LLM provider fails
    mock_llm = AsyncMock()
    mock_llm.structured_generate.side_effect = RuntimeError("OpenAI API 503 Service Unavailable")

    mock_ctx = MagicMock()
    mock_ctx.build_context.return_value = "Context: Apple Q3 2024 revenue was $85.8B"

    mock_prompt = MagicMock()
    mock_prompt.build_prompt.return_value = ("prompt text", "system instruction", "v1.0")

    mock_gate = MagicMock()
    mock_gate.evaluate_gate.return_value = None

    mock_validator = MagicMock()
    mock_renderer = MagicMock()
    mock_renderer.render_deterministic_fallback.return_value = (
        "Apple's Q3 2024 Revenue was $85.8B [Doc 1, p.1]."
    )

    svc = AnswerOrchestrationService(
        reasoning_service=mock_reasoning_svc,
        llm_provider=mock_llm,
        context_builder=mock_ctx,
        prompt_builder=mock_prompt,
        answerability_gate=mock_gate,
        validator=mock_validator,
        renderer=mock_renderer,
    )

    req = AnswerRequest(
        query="What was Apple's Q3 2024 revenue?",
        response_style=ResponseStyle.STANDARD,
        tenant_id="default_tenant",
    )

    response = await svc.generate_answer(req)

    assert response.status == AnswerStatus.COMPLETED
    assert "Apple's Q3 2024 Revenue was $85.8B" in response.answer_text
    assert response.metadata["used_fallback"] is True
    assert mock_renderer.render_deterministic_fallback.called


# =========================================================================
# 5. ERROR CLASSIFICATION & RECOVERABILITY MAPPING
# =========================================================================
def test_error_classification_recoverability():
    """Verify that every domain exception category correctly identifies recoverability."""
    # Recoverable: Network timeout, validation
    e_timeout = ErrorClassifier.classify(
        LLMTimeoutError(provider="anthropic", timeout_seconds=15.0)
    )
    assert e_timeout.recoverable is True
    assert e_timeout.category.value == "TIMEOUT"

    # Non-recoverable: Corrupted document parsing
    e_parse = ErrorClassifier.classify(DocumentParsingError("Corrupt PDF streams"))
    assert e_parse.recoverable is False
    assert e_parse.category.value == "INGESTION_ERROR"

    # Storage dependency error
    e_storage = ErrorClassifier.classify(StorageError("Bucket access forbidden"))
    assert e_storage.category.value == "DEPENDENCY_UNAVAILABLE"


# =========================================================================
# 6. DISTRIBUTED TRACING & W3C PROPAGATION INVARIANCE
# =========================================================================
@pytest.mark.asyncio
async def test_end_to_end_distributed_tracing_spans():
    """Verify that spans created during retrieval and reasoning share trace_id and record timings."""
    with tracer.span("test_root_operation", attributes={"tenant_id": "test_tenant"}) as root:  # noqa: SIM117
        with tracer.span("child_retrieval") as child:
            child.set_attribute("items_retrieved", 5)
            assert child.trace_id == root.trace_id
            assert child.parent_span_id == root.span_id

    spans = tracer.get_recorded_spans()
    root_span = next(s for s in spans if s.name == "test_root_operation")
    child_span = next(s for s in spans if s.name == "child_retrieval")

    assert root_span.duration_ms >= 0.0
    assert child_span.duration_ms >= 0.0
    assert child_span.attributes["items_retrieved"] == 5


# =========================================================================
# 7. SSE STREAMING DISCONNECT AND CLEAN TEARDOWN
# =========================================================================
@pytest.mark.asyncio
async def test_streaming_disconnect_handling():
    """Verify that streaming generation terminates gracefully when consumer disconnects."""
    mock_reasoning = AsyncMock()
    mock_llm = AsyncMock()

    async def infinite_tokens(*args, **kwargs):
        for i in range(100):
            yield f"token_{i} "

    mock_llm.generate_stream = infinite_tokens

    mock_ctx = MagicMock()
    mock_ctx.build_context.return_value = "context"
    mock_prompt = MagicMock()
    mock_prompt.build_prompt.return_value = ("p", "s", "v1")
    mock_gate = MagicMock()
    mock_gate.evaluate_gate.return_value = None

    svc = AnswerOrchestrationService(
        reasoning_service=mock_reasoning,
        llm_provider=mock_llm,
        context_builder=mock_ctx,
        prompt_builder=mock_prompt,
        answerability_gate=mock_gate,
        validator=MagicMock(),
        renderer=MagicMock(),
    )

    req = AnswerRequest(
        query="Stream test", response_style=ResponseStyle.STANDARD, tenant_id="test"
    )
    stream = svc.generate_answer_stream(req)

    # Consumer disconnects after reading 3 events
    received = []
    async for event in stream:
        received.append(event)
        if len(received) >= 3:
            break

    assert len(received) == 3


# =========================================================================
# 8. CORRUPTED DOCUMENT INGESTION ERROR HANDLING
# =========================================================================
@pytest.mark.asyncio
async def test_corrupt_pdf_ingestion_error_handling():
    """Verify that corrupted PDF input produces structured domain error without crashing."""
    from financial_rag.application.ingestion.pipelines import IngestionPipeline
    from financial_rag.domain.exceptions import IngestionPipelineError

    mock_parser = AsyncMock()
    mock_parser.parse.side_effect = DocumentParsingError("Corrupt PDF EOF marker")

    pipeline = IngestionPipeline(
        parser=mock_parser,
        table_extractor=MagicMock(),
        table_normalizer=MagicMock(),
        normalizer=MagicMock(),
        structure_detector=MagicMock(),
        chunker=MagicMock(),
        embedding_provider=AsyncMock(),
        vector_store=AsyncMock(),
    )

    with pytest.raises(IngestionPipelineError) as exc_info:
        await pipeline.process_document(
            content=b"not-a-valid-pdf-content",
            document_id=str(uuid4()),
            version_id=str(uuid4()),
            filename="corrupt.pdf",
        )

    assert "Corrupt PDF" in str(exc_info.value)
