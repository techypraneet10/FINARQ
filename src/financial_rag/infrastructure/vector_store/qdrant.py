"""Qdrant vector database adapter with provenance and multi-tenant payload preservation."""

import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from financial_rag.common.types import ChunkType
from financial_rag.config.settings import QdrantSettings, get_settings
from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult
from financial_rag.domain.exceptions import VectorStoreError
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.vector_store.qdrant")


class QdrantVectorStoreAdapter(VectorStoreProtocol):
    """Vector database adapter for Qdrant with full provenance lineage and tenant isolation."""

    def __init__(
        self,
        qdrant_settings: QdrantSettings | None = None,
        custom_client: AsyncQdrantClient | None = None,
    ) -> None:
        self._settings = qdrant_settings or get_settings().qdrant
        self._collection_name = self._settings.collection_name
        self._client: AsyncQdrantClient | None = custom_client

    def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            if self._settings.location:
                # In-memory or local storage path (useful for tests/dev)
                self._client = AsyncQdrantClient(location=self._settings.location)
            else:
                api_key = self._settings.api_key.get_secret_value() or None
                self._client = AsyncQdrantClient(
                    host=self._settings.host,
                    port=self._settings.port,
                    api_key=api_key,
                    https=self._settings.use_https,
                )
        return self._client

    async def initialize_collection(
        self, dimension: int, collection_name: str | None = None
    ) -> bool:
        """Create Qdrant collection with cosine distance if not already present."""
        target_col = collection_name or self._collection_name
        client = self._get_client()

        try:
            exists = await client.collection_exists(collection_name=target_col)
            if not exists:
                await client.create_collection(
                    collection_name=target_col,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection '{target_col}' with dimension={dimension}")
            return True
        except Exception as ex:
            raise VectorStoreError(
                message=f"Failed to initialize Qdrant collection '{target_col}': {ex}",
                details={"collection": target_col, "error": str(ex)},
            ) from ex

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> bool:
        """Upsert document chunk vectors along with tenant ID and rich provenance metadata payloads."""
        if not chunks:
            return True

        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                message="Chunks and embeddings lists must have identical lengths for upsert.",
                details={"chunks_count": len(chunks), "embeddings_count": len(embeddings)},
            )

        client = self._get_client()
        target_col = self._collection_name

        try:
            # Ensure collection is initialized
            dimension = len(embeddings[0])
            await self.initialize_collection(dimension=dimension, collection_name=target_col)

            points: list[models.PointStruct] = []
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                # Derive deterministic UUID for vector point
                try:
                    point_id = str(uuid.UUID(str(chunk.id)))
                except ValueError:
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"chunk:{chunk.id}"))

                # Complete provenance lineage and multi-tenancy payload
                payload: dict[str, Any] = {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "document_version_id": str(chunk.document_version_id),
                    "tenant_id": str(chunk.tenant_id),
                    "page_number": chunk.page_number,
                    "page_numbers": chunk.page_numbers or [chunk.page_number],
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type.value,
                    "content": chunk.content,
                    "section_path": chunk.section_path,
                    "table_id": str(chunk.table_id) if chunk.table_id else None,
                    "source_block_ids": [str(bid) for bid in chunk.source_block_ids],
                    "token_count": chunk.token_count,
                    "char_count": chunk.char_count,
                    "created_at": chunk.created_at.isoformat(),
                    "metadata": chunk.metadata,
                }

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

            await client.upsert(
                collection_name=target_col,
                points=points,
                wait=True,
            )
            logger.info(
                f"Upserted {len(points)} vector points into Qdrant collection '{target_col}'"
            )
            return True

        except Exception as ex:
            raise VectorStoreError(
                message=f"Failed to upsert chunks into Qdrant: {ex}",
                details={"collection": target_col, "error": str(ex)},
            ) from ex

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Perform cosine similarity search on indexed financial vectors with tenant isolation."""
        client = self._get_client()
        target_col = self._collection_name

        try:
            # Check if collection exists before querying
            exists = await client.collection_exists(collection_name=target_col)
            if not exists:
                logger.info(
                    f"Qdrant collection '{target_col}' does not exist yet; returning empty candidate list."
                )
                return []

            effective_tenant = tenant_id or (filters.get("tenant_id") if filters else None)
            conditions: list[Any] = []

            # 1. Enforce tenant isolation in Qdrant filter
            if effective_tenant:
                conditions.append(
                    models.FieldCondition(
                        key="tenant_id", match=models.MatchValue(value=str(effective_tenant))
                    )
                )

            # 2. Add domain metadata filters
            if filters:
                for k, v in filters.items():
                    if k == "tenant_id":
                        continue
                    if isinstance(v, list):
                        for item in v:
                            conditions.append(
                                models.FieldCondition(key=k, match=models.MatchValue(value=item))
                            )
                    else:
                        conditions.append(
                            models.FieldCondition(key=k, match=models.MatchValue(value=v))
                        )

            query_filter = models.Filter(must=conditions) if conditions else None

            query_res = await client.query_points(
                collection_name=target_col,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )

            results: list[RetrievalResult] = []
            for hit in query_res.points:
                p = hit.payload or {}
                point_tenant = p.get("tenant_id", "default_tenant")

                # Defense-in-depth: Discard unexpected foreign tenant vectors
                if effective_tenant and point_tenant != str(effective_tenant):
                    logger.warning(
                        f"Cross-tenant vector filtered out during search: requested={effective_tenant}, actual={point_tenant}"
                    )
                    continue

                chunk = DocumentChunk(
                    id=p.get("chunk_id", str(hit.id)),
                    document_id=p.get("document_id", ""),
                    document_version_id=p.get("document_version_id", ""),
                    tenant_id=point_tenant,
                    page_number=p.get("page_number", 1),
                    page_numbers=p.get("page_numbers", [p.get("page_number", 1)]),
                    chunk_index=p.get("chunk_index", 0),
                    chunk_type=ChunkType(p.get("chunk_type", "text")),
                    content=p.get("content", ""),
                    section_path=p.get("section_path", ""),
                    table_id=p.get("table_id"),
                    source_block_ids=p.get("source_block_ids", []),
                    token_count=p.get("token_count", 0),
                    char_count=p.get("char_count", 0),
                    metadata=p.get("metadata", {}),
                )
                results.append(
                    RetrievalResult(
                        chunk=chunk,
                        score=float(hit.score),
                        retrieval_method="dense_vector",
                    )
                )

            return results

        except Exception as ex:
            err_msg = str(ex).lower()
            if "not found" in err_msg or "doesn't exist" in err_msg or "404" in err_msg:
                logger.info(
                    f"Qdrant collection '{target_col}' not found or empty ({ex}); returning empty candidate list."
                )
                return []
            raise VectorStoreError(
                message=f"Failed to search Qdrant vector store: {ex}",
                details={"collection": target_col, "error": str(ex)},
            ) from ex

    async def delete_by_document_id(self, document_id: str, tenant_id: str | None = None) -> bool:
        """Remove all indexed chunks belonging to a specific document, optionally scoped to tenant."""
        client = self._get_client()
        target_col = self._collection_name

        try:
            conditions: list[Any] = [
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(document_id)),
                )
            ]
            if tenant_id:
                conditions.append(
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=str(tenant_id)),
                    )
                )

            await client.delete(
                collection_name=target_col,
                points_selector=models.FilterSelector(filter=models.Filter(must=conditions)),
            )
            logger.info(f"Deleted vector chunks for document '{document_id}' from Qdrant")
            return True
        except Exception as ex:
            raise VectorStoreError(
                message=f"Failed to delete document vectors from Qdrant: {ex}",
                details={"document_id": document_id, "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.get_collections()
            return True
        except Exception as ex:
            logger.warning(f"Qdrant health check failed: {ex}")
            return False
