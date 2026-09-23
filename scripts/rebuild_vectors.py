"""Deterministic vector database rebuild tool for Financial RAG Platform."""

import argparse
import asyncio
import sys
from typing import Any

from sqlalchemy import select

from financial_rag.config.settings import Settings, get_settings
from financial_rag.infrastructure.embeddings import get_embedding_provider
from financial_rag.infrastructure.logging import get_logger, setup_logging
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.models import DocumentChunkORM
from financial_rag.infrastructure.vector_store import get_vector_store

logger = get_logger("financial_rag.scripts.rebuild_vectors")


async def rebuild_vectors(
    settings: Settings,
    tenant_id: str | None = None,
    document_id: str | None = None,
    batch_size: int = 50,
) -> dict[str, Any]:
    """Deterministically regenerate embeddings from PostgreSQL chunks and upsert to Qdrant."""
    session_manager = DatabaseSessionManager(settings.database)
    embedding_provider = get_embedding_provider(settings.embedding)
    vector_store = get_vector_store(settings.qdrant)

    total_chunks_processed = 0
    total_batches_upserted = 0
    failed_chunks = 0

    try:
        async with session_manager.session() as session:
            stmt = select(DocumentChunkORM).order_by(DocumentChunkORM.created_at.asc())
            if tenant_id:
                stmt = stmt.where(DocumentChunkORM.tenant_id == str(tenant_id))
            if document_id:
                stmt = stmt.where(DocumentChunkORM.document_id == str(document_id))

            result = await session.execute(stmt)
            chunks = result.scalars().all()
            total = len(chunks)
            logger.info(
                f"Found {total} chunks to index into Qdrant (embedding={settings.embedding.model_name})"
            )

            # Process in batches
            for i in range(0, total, batch_size):
                batch = chunks[i : i + batch_size]
                texts = [c.content for c in batch]

                try:
                    # Generate embeddings
                    vectors = await embedding_provider.embed_batch(texts)

                    # Upsert points into vector store
                    points = []
                    for chunk, vec in zip(batch, vectors, strict=True):
                        payload = {
                            "tenant_id": chunk.tenant_id,
                            "document_id": chunk.document_id,
                            "version_id": chunk.version_id,
                            "page_number": chunk.page_number,
                            "chunk_index": chunk.chunk_index,
                            "chunk_type": chunk.chunk_type,
                            "content": chunk.content,
                            "section_path": chunk.section_path,
                            "table_id": chunk.table_id,
                        }
                        points.append((str(chunk.id), vec, payload))

                    if hasattr(vector_store, "upsert_batch"):
                        await vector_store.upsert_batch(points)
                    elif hasattr(vector_store, "upsert_points"):
                        await vector_store.upsert_points(points)

                    total_chunks_processed += len(batch)
                    total_batches_upserted += 1
                    logger.info(
                        f"Upserted batch {total_batches_upserted} ({total_chunks_processed}/{total} chunks)"
                    )
                except Exception as ex:
                    failed_chunks += len(batch)
                    logger.error(
                        f"Error rebuilding batch {i}-{i + len(batch)}: {ex}", exc_info=True
                    )

    finally:
        await session_manager.close()

    return {
        "total_chunks_processed": total_chunks_processed,
        "total_batches_upserted": total_batches_upserted,
        "failed_chunks": failed_chunks,
        "embedding_model": settings.embedding.model_name,
        "embedding_dimension": settings.embedding.dimension,
    }


async def main_async(args: argparse.Namespace) -> int:
    settings = get_settings()
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)
    logger.info("=" * 60)
    logger.info("FINANCIAL RAG PLATFORM - DETERMINISTIC VECTOR REBUILD TOOL")
    logger.info("=" * 60)

    stats = await rebuild_vectors(
        settings=settings,
        tenant_id=args.tenant_id,
        document_id=args.document_id,
        batch_size=args.batch_size,
    )

    logger.info(f"Vector rebuild complete. Stats: {stats}")
    return 0 if stats["failed_chunks"] == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild Qdrant vector index deterministically.")
    parser.add_argument("--tenant-id", type=str, help="Optional tenant ID filter")
    parser.add_argument("--document-id", type=str, help="Optional document ID filter")
    parser.add_argument("--batch-size", type=int, default=50, help="Embedding batch size")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
