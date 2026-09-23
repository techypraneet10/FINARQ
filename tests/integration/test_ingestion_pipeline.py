"""Integration tests for the complete Ingestion Pipeline."""

import pytest

from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.common.types import ChunkType, DocumentType, IngestionStage
from financial_rag.config.settings import ChunkingSettings, QdrantSettings
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.normalization.document_normalizer import DocumentNormalizer
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.mark.integration
async def test_full_ingestion_pipeline_execution() -> None:
    # 1. Setup Vector Store with in-memory Qdrant
    qdrant_settings = QdrantSettings(
        collection_name="pipeline_integration_col", location=":memory:"
    )
    vector_store = QdrantVectorStoreAdapter(qdrant_settings=qdrant_settings)
    await vector_store.initialize_collection(dimension=128)

    # 2. Assemble Pipeline
    embedder = MockEmbeddingProvider(dimension=128)
    table_normalizer = FinancialTableNormalizer()
    table_extractor = FinancialTableExtractor(normalizer=table_normalizer)
    normalizer = DocumentNormalizer()
    structure_detector = FinancialStructureDetector()
    chunker = StructureAwareChunker(chunking_settings=ChunkingSettings())

    pipeline = IngestionPipeline(
        parser=PyMuPDFParser(),
        table_extractor=table_extractor,
        table_normalizer=table_normalizer,
        normalizer=normalizer,
        structure_detector=structure_detector,
        chunker=chunker,
        embedding_provider=embedder,
        vector_store=vector_store,
    )

    pdf_bytes = create_sample_10k_pdf()
    doc_id = "doc-integ-100"
    version_id = "ver-integ-100"

    stages_seen: list[IngestionStage] = []

    def on_stage(stage: IngestionStage, progress: float) -> None:
        stages_seen.append(stage)

    # 3. Execute Pipeline
    pages, chunks = await pipeline.execute(
        content=pdf_bytes,
        document_id=doc_id,
        version_id=version_id,
        document_type=DocumentType.SEC_10K,
        filename="apple_10k.pdf",
        on_stage_change=on_stage,
    )

    # Verify Stage progression
    assert IngestionStage.PARSING in stages_seen
    assert IngestionStage.EXTRACTING_TABLES in stages_seen
    assert IngestionStage.NORMALIZING in stages_seen
    assert IngestionStage.CHUNKING in stages_seen
    assert IngestionStage.EMBEDDING in stages_seen
    assert IngestionStage.INDEXING in stages_seen
    assert IngestionStage.COMPLETED in stages_seen

    # Verify Output Pages
    assert len(pages) == 3
    assert all(p.document_id == doc_id for p in pages)
    assert all(p.version_id == version_id for p in pages)

    # Verify Output Chunks
    assert len(chunks) > 0
    assert any(c.chunk_type == ChunkType.TABLE for c in chunks)
    assert any("item 1. business" in c.section_path.lower() for c in chunks)

    # Verify Vector Database retrieval
    query_vec = await embedder.embed_text("Acme Financial Corp risk factors")
    search_results = await vector_store.search(query_vector=query_vec, top_k=5)
    assert len(search_results) > 0
    assert search_results[0].chunk.document_id == doc_id
