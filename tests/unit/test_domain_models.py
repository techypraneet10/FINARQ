from datetime import UTC, datetime
from uuid import uuid4

import pytest

from financial_rag.common.types import DocumentType, IngestionStatus
from financial_rag.domain.entities.models import (
    Answer,
    Citation,
    Document,
    DocumentChunk,
    EvaluationRun,
    IngestionJob,
    ReasoningStep,
    User,
)


@pytest.mark.unit
def test_document_entity_instantiation() -> None:
    """Test Document entity attributes and mutability."""
    doc_id = str(uuid4())
    doc = Document(
        id=doc_id,
        title="Apple Inc. 10-K FY2023",
        document_type=DocumentType.SEC_10K,
        ticker_symbol="AAPL",
        fiscal_year=2023,
        fiscal_period="FY",
        storage_uri="s3://financial-documents/aapl-2023-10k.pdf",
        file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        pages_count=120,
    )

    assert doc.id == doc_id
    assert doc.title == "Apple Inc. 10-K FY2023"
    assert doc.document_type == DocumentType.SEC_10K
    assert doc.ticker_symbol == "AAPL"
    assert doc.fiscal_year == 2023
    assert doc.pages_count == 120


@pytest.mark.unit
def test_document_chunk_provenance() -> None:
    """Verify DocumentChunk attributes and provenance lineage construction."""
    chunk = DocumentChunk(
        id="chunk-001",
        document_id="doc-001",
        page_number=15,
        content="Total revenue was $383,285 million in 2023.",
        chunk_index=0,
        section_path="Part I > Item 1. Business",
    )

    assert chunk.page_number == 15
    assert chunk.page_numbers == [15]
    assert chunk.char_count == len("Total revenue was $383,285 million in 2023.")
    provenance = chunk.get_provenance()
    assert provenance.document_id == "doc-001"
    assert provenance.chunk_id == "chunk-001"
    assert provenance.section_path == "Part I > Item 1. Business"


@pytest.mark.unit
def test_citation_and_answer_composition() -> None:
    """Test Answer composition with verifiable Citations and deterministic ReasoningSteps."""
    citation = Citation(
        id="cit-001",
        document_id="doc-001",
        document_title="Apple Inc. 10-K FY2023",
        page_number=32,
        snippet="Total net sales for fiscal year 2023 were $383,285 million.",
        ticker_symbol="AAPL",
    )

    reasoning = ReasoningStep(
        step_number=1,
        description="Calculate Gross Margin Percentage",
        formula="(Gross Profit / Total Revenue) * 100",
        inputs={"gross_profit": 169148, "total_revenue": 383285},
        output=44.13,
    )

    answer = Answer(
        query_id="query-123",
        text="Apple's gross margin for FY2023 was 44.13%, calculated from gross profit of $169,148M.",
        citations=[citation],
        reasoning_steps=[reasoning],
        confidence_score=1.0,
    )

    assert answer.query_id == "query-123"
    assert len(answer.citations) == 1
    assert answer.citations[0].ticker_symbol == "AAPL"
    assert len(answer.reasoning_steps) == 1
    assert answer.reasoning_steps[0].output == 44.13


@pytest.mark.unit
def test_ingestion_job_state() -> None:
    """Test IngestionJob state transitions."""
    job = IngestionJob(
        id="job-100",
        document_id="doc-100",
        status=IngestionStatus.PENDING,
    )
    assert job.status == IngestionStatus.PENDING

    job.status = IngestionStatus.PROCESSING
    assert job.status == IngestionStatus.PROCESSING

    job.status = IngestionStatus.INDEXED
    job.chunks_indexed = 45
    job.completed_at = datetime.now(UTC)
    assert job.chunks_indexed == 45
    assert job.completed_at is not None


@pytest.mark.unit
def test_user_and_evaluation_entities() -> None:
    """Test User and EvaluationRun entities."""
    user = User(id="usr-1", email="analyst@firm.com")
    assert user.email == "analyst@firm.com"
    assert user.is_active is True

    eval_run = EvaluationRun(
        dataset_name="FinanceBench-v1",
        factual_precision=0.98,
        retrieval_recall=0.95,
        citation_precision=1.0,
        numerical_accuracy=1.0,
    )
    assert eval_run.factual_precision == 0.98
    assert eval_run.citation_precision == 1.0
