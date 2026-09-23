"""Dense semantic vector retriever adapter leveraging Qdrant and embedding models."""

from typing import Any

from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalFilter,
    RetrievalQuery,
    RetrievalSource,
)
from financial_rag.domain.exceptions import IncompatibleEmbeddingError, VectorStoreError
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.retrieval import DenseRetrieverProtocol
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.dense_retriever")


class QdrantDenseRetriever(DenseRetrieverProtocol):
    """Dense vector retriever using embeddings and Qdrant similarity search."""

    def __init__(
        self,
        embedding_provider: EmbeddingProviderProtocol,
        vector_store: VectorStoreProtocol,
        expected_dimension: int | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._expected_dimension = expected_dimension

    def _build_qdrant_filter(
        self, filters: RetrievalFilter | None, tenant_id: str | None = None
    ) -> dict[str, Any] | None:
        """Translate domain RetrievalFilter into infrastructure filter dict."""
        qdrant_filters: dict[str, Any] = {}

        if tenant_id:
            qdrant_filters["tenant_id"] = str(tenant_id)

        if not filters or filters.is_empty():
            return qdrant_filters or None

        if filters.tenant_id:
            qdrant_filters["tenant_id"] = str(filters.tenant_id)

        if filters.document_ids and len(filters.document_ids) == 1:
            qdrant_filters["document_id"] = str(filters.document_ids[0])

        if filters.version_ids and len(filters.version_ids) == 1:
            qdrant_filters["document_version_id"] = str(filters.version_ids[0])

        if filters.ticker_symbols and len(filters.ticker_symbols) == 1:
            qdrant_filters["ticker_symbol"] = str(filters.ticker_symbols[0])

        if filters.chunk_types and len(filters.chunk_types) == 1:
            qdrant_filters["chunk_type"] = str(filters.chunk_types[0])

        if filters.table_only is True:
            qdrant_filters["chunk_type"] = "table"

        # Add any custom metadata filters
        for k, v in filters.custom_metadata.items():
            qdrant_filters[k] = v

        return qdrant_filters or None

    async def retrieve(
        self,
        query: RetrievalQuery,
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Generate query vector and retrieve nearest semantic candidates from Qdrant."""
        limit = top_k or query.dense_top_k or query.top_k

        try:
            # 1. Generate query embedding
            query_text = query.normalized_query or query.raw_query
            query_vector = await self._embedding_provider.embed_text(query_text)

            # 2. Check dimension compatibility
            if self._expected_dimension and len(query_vector) != self._expected_dimension:
                raise IncompatibleEmbeddingError(
                    collection_dim=self._expected_dimension,
                    query_dim=len(query_vector),
                    collection_name="financial_chunks",
                )

            # 3. Translate domain filter
            qdrant_filters = self._build_qdrant_filter(query.filters, tenant_id=query.tenant_id)

            # 4. Search vector store
            raw_results = await self._vector_store.search(
                query_vector=query_vector,
                top_k=limit,
                filters=qdrant_filters,
            )

            # 5. Convert to domain RetrievalCandidate with provenance and rank
            candidates: list[RetrievalCandidate] = []
            for rank_idx, res in enumerate(raw_results, start=1):
                chunk = res.chunk
                candidate = RetrievalCandidate(
                    chunk=chunk,
                    dense_score=float(res.score),
                    dense_rank=rank_idx,
                    sparse_score=None,
                    sparse_rank=None,
                    fusion_score=0.0,
                    reranker_score=None,
                    final_score=float(res.score),
                    sources=[RetrievalSource.DENSE],
                    provenance=chunk.get_provenance(),
                )
                candidates.append(candidate)

            logger.info(
                f"Dense retrieval completed for query '{query.id}': found {len(candidates)} candidates"
            )
            return candidates

        except IncompatibleEmbeddingError:
            raise
        except Exception as ex:
            logger.error(f"Dense vector retrieval failed for query '{query.id}': {ex}")
            raise VectorStoreError(
                message=f"Dense vector retrieval failure: {ex}",
                details={"query_id": str(query.id), "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        """Check vector store and embedding provider health."""
        embed_ok = await self._embedding_provider.health_check()
        vector_ok = await self._vector_store.health_check()
        return embed_ok and vector_ok
