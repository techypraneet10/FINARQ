import time
from collections.abc import Callable

from financial_rag.common.types import DocumentType, IngestionStage
from financial_rag.domain.entities.models import (
    DocumentChunk,
    DocumentPage,
)
from financial_rag.domain.exceptions import IngestionPipelineError
from financial_rag.domain.interfaces.chunker import ChunkerProtocol
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.normalizer import (
    DocumentNormalizerProtocol,
    StructureDetectorProtocol,
)
from financial_rag.domain.interfaces.parser import PDFParserProtocol
from financial_rag.domain.interfaces.retrieval import SparseRetrieverProtocol
from financial_rag.domain.interfaces.table import (
    TableExtractorProtocol,
    TableNormalizerProtocol,
)
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.tracer import tracer

logger = get_logger("financial_rag.application.ingestion.pipelines")


class IngestionPipeline:
    """Coordinates transformation from raw PDF bytes to indexed vector records."""

    def __init__(
        self,
        parser: PDFParserProtocol,
        table_extractor: TableExtractorProtocol,
        table_normalizer: TableNormalizerProtocol,
        normalizer: DocumentNormalizerProtocol,
        structure_detector: StructureDetectorProtocol,
        chunker: ChunkerProtocol,
        embedding_provider: EmbeddingProviderProtocol,
        vector_store: VectorStoreProtocol,
        sparse_retriever: SparseRetrieverProtocol | None = None,
    ) -> None:
        self._parser = parser
        self._table_extractor = table_extractor
        self._table_normalizer = table_normalizer
        self._normalizer = normalizer
        self._structure_detector = structure_detector
        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._sparse_retriever = sparse_retriever

    async def process_document(
        self,
        content: bytes,
        document_id: str,
        version_id: str,
        document_type: DocumentType = DocumentType.OTHER,
        filename: str = "",
        tenant_id: str = "default_tenant",
        on_stage_change: Callable[[IngestionStage, float], None] | None = None,
    ) -> tuple[list[DocumentPage], list[DocumentChunk]]:
        """Run full extraction, normalization, chunking, embedding, and vector indexing."""

        def _notify(stage: IngestionStage, progress: float) -> None:
            if on_stage_change:
                on_stage_change(stage, progress)

        total_start = time.perf_counter()
        current_stage = "PARSING"

        try:
            async with tracer.async_span(
                "ingestion.pipeline",
                attributes={"document_id": document_id, "tenant_id": tenant_id},
            ):
                # Stage 1: PARSING
                current_stage = "PARSING"
                _notify(IngestionStage.PARSING, 10.0)
                logger.info(
                    f"Pipeline Stage: PARSING for document {document_id} (tenant={tenant_id})"
                )
                t0 = time.perf_counter()
                async with tracer.async_span("ingestion.parsing"):
                    parsed_doc = await self._parser.parse(content, filename=filename)
                metrics_registry.record_ingestion_stage(
                    "parsing", (time.perf_counter() - t0) * 1000.0, "success"
                )
                pages = parsed_doc.pages
                for page in pages:
                    page.document_id = document_id
                    page.version_id = version_id
                    page.tenant_id = tenant_id

                # Stage 2: EXTRACTING_TABLES
                current_stage = "EXTRACTING_TABLES"
                _notify(IngestionStage.EXTRACTING_TABLES, 25.0)
                logger.info(f"Pipeline Stage: EXTRACTING_TABLES for document {document_id}")
                t0 = time.perf_counter()
                with tracer.span("ingestion.extract_tables"):
                    for page in pages:
                        extracted_tables = self._table_extractor.extract_tables(page)
                        page.tables = [
                            self._table_normalizer.normalize_table(t) for t in extracted_tables
                        ]
                metrics_registry.record_ingestion_stage(
                    "table_extraction", (time.perf_counter() - t0) * 1000.0, "success"
                )

                # Stage 3: NORMALIZING
                current_stage = "NORMALIZING"
                _notify(IngestionStage.NORMALIZING, 40.0)
                logger.info(f"Pipeline Stage: NORMALIZING for document {document_id}")
                t0 = time.perf_counter()
                with tracer.span("ingestion.normalizing"):
                    pages = self._normalizer.normalize(pages)
                metrics_registry.record_ingestion_stage(
                    "normalizing", (time.perf_counter() - t0) * 1000.0, "success"
                )

                # Stage 4: FINANCIAL STRUCTURE DETECTION
                current_stage = "STRUCTURE_DETECTION"
                logger.info(f"Pipeline Stage: STRUCTURE DETECTION for document {document_id}")
                t0 = time.perf_counter()
                with tracer.span("ingestion.structure_detection"):
                    pages = self._structure_detector.detect_structure(
                        pages, document_type=document_type
                    )
                metrics_registry.record_ingestion_stage(
                    "structure_detection", (time.perf_counter() - t0) * 1000.0, "success"
                )

                # Stage 5: CHUNKING
                current_stage = "CHUNKING"
                _notify(IngestionStage.CHUNKING, 55.0)
                logger.info(f"Pipeline Stage: CHUNKING for document {document_id}")
                t0 = time.perf_counter()
                with tracer.span("ingestion.chunking"):
                    chunks = self._chunker.chunk_document(
                        document_id=document_id,
                        version_id=version_id,
                        pages=pages,
                    )
                metrics_registry.record_ingestion_stage(
                    "chunking", (time.perf_counter() - t0) * 1000.0, "success"
                )
                for chunk in chunks:
                    chunk.tenant_id = tenant_id

                if not chunks:
                    logger.warning(f"No chunks generated for document {document_id}")

                # Stage 6: EMBEDDING
                current_stage = "EMBEDDING"
                _notify(IngestionStage.EMBEDDING, 75.0)
                logger.info(f"Pipeline Stage: EMBEDDING for {len(chunks)} chunks")
                t0 = time.perf_counter()
                chunk_texts = [c.content for c in chunks]
                async with tracer.async_span(
                    "ingestion.embedding", attributes={"chunks_count": len(chunks)}
                ):
                    embeddings = await self._embedding_provider.embed_batch(chunk_texts)
                metrics_registry.record_ingestion_stage(
                    "embedding", (time.perf_counter() - t0) * 1000.0, "success"
                )

                # Stage 7: INDEXING
                current_stage = "INDEXING"
                _notify(IngestionStage.INDEXING, 90.0)
                logger.info(f"Pipeline Stage: INDEXING into Qdrant for document {document_id}")
                t0 = time.perf_counter()
                async with tracer.async_span(
                    "ingestion.indexing", attributes={"chunks_count": len(chunks)}
                ):
                    if chunks and embeddings:
                        await self._vector_store.upsert_chunks(chunks=chunks, embeddings=embeddings)
                    if chunks and self._sparse_retriever:
                        await self._sparse_retriever.index_chunks(chunks)
                metrics_registry.record_ingestion_stage(
                    "indexing", (time.perf_counter() - t0) * 1000.0, "success"
                )

                total_duration_ms = (time.perf_counter() - total_start) * 1000.0
                metrics_registry.record_ingestion_latency(total_duration_ms)

                _notify(IngestionStage.COMPLETED, 100.0)
                return pages, chunks

        except Exception as ex:
            metrics_registry.record_ingestion_stage(current_stage.lower(), 0.0, "failure")
            logger.error(f"Ingestion pipeline execution failure: {ex}")
            raise IngestionPipelineError(
                stage="PIPELINE_EXECUTION",
                message=str(ex),
                details={"document_id": str(document_id), "version_id": str(version_id)},
            ) from ex

    # Alias for backwards compatibility
    execute = process_document
