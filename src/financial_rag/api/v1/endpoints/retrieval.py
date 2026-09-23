"""Retrieval API endpoint providing hybrid search, reranking, and evidence selection with tenant scoping."""

from fastapi import APIRouter, Depends, status

from financial_rag.api.dependencies import (
    RetrievalServiceDep,
    require_permission,
)
from financial_rag.api.v1.schemas import (
    FinancialSignalsResponse,
    ProvenanceLineageResponse,
    RankedEvidenceResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.domain.entities.security import Permission, PrincipalContext
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.api.v1.endpoints.retrieval")

router = APIRouter(prefix="/retrieval", tags=["Retrieval & Evidence Selection"])
search_router = APIRouter(tags=["Search"])


@router.post(
    "/search",
    response_model=RetrievalSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid retrieval and evidence selection",
    description=(
        "Executes query normalization, classification, financial signal extraction, "
        "parallel dense vector search (Qdrant) and sparse lexical search (BM25), "
        "Reciprocal Rank Fusion (RRF), deduplication, cross-encoder reranking, "
        "and diversity-preserving evidence selection with complete provenance and strict tenant scoping."
    ),
)
async def search_evidence(
    request: RetrievalSearchRequest,
    retrieval_service: RetrievalServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.RETRIEVAL_EXECUTE)),
) -> RetrievalSearchResponse:
    """Execute hybrid retrieval pipeline and return ranked evidence set scoped to caller's tenant."""
    logger.info(
        f"Received retrieval inquiry: '{request.query}' (top_k={request.top_k}) from user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )

    # Map request filters to domain RetrievalFilter, strictly binding caller's tenant
    domain_filter = RetrievalFilter(
        document_ids=request.filters.document_ids if request.filters else None,
        version_ids=request.filters.version_ids if request.filters else None,
        tenant_id=principal.tenant_id,
        ticker_symbols=request.filters.ticker_symbols if request.filters else None,
        fiscal_years=request.filters.fiscal_years if request.filters else None,
        fiscal_periods=request.filters.fiscal_periods if request.filters else None,
        document_types=request.filters.document_types if request.filters else None,
        sections=request.filters.sections if request.filters else None,
        chunk_types=request.filters.chunk_types if request.filters else None,
        table_only=request.filters.table_only if request.filters else None,
        custom_metadata=request.filters.custom_metadata if request.filters else {},
    )

    # Execute retrieval workflow
    evidence_set = await retrieval_service.search(
        raw_query=request.query,
        filters=domain_filter,
        top_k=request.top_k,
        dense_top_k=request.dense_top_k,
        sparse_top_k=request.sparse_top_k,
        rerank_top_k=request.rerank_top_k,
        use_reranker=request.use_reranker,
    )

    # Map domain EvidenceSet to API response schema
    evidence_items_response: list[RankedEvidenceResponse] = []
    for item in evidence_set.items:
        prov = item.provenance
        prov_resp = ProvenanceLineageResponse(
            document_id=str(prov.document_id),
            document_version_id=str(prov.document_version_id),
            page_numbers=prov.page_numbers,
            source_block_ids=[str(b) for b in prov.source_block_ids],
            section_path=prov.section_path,
            chunk_type=prov.chunk_type,
            table_id=str(prov.table_id) if prov.table_id else None,
            chunk_id=str(prov.chunk_id) if prov.chunk_id else None,
        )

        evidence_items_response.append(
            RankedEvidenceResponse(
                rank=item.rank,
                chunk_id=str(item.chunk_id),
                document_id=str(item.document_id),
                document_version_id=str(item.document_version_id),
                page_number=item.page_number,
                page_numbers=item.page_numbers,
                chunk_type=item.chunk_type.value,
                content=item.content,
                section_path=item.section_path,
                table_id=str(item.table_id) if item.table_id else None,
                source_block_ids=[str(b) for b in item.source_block_ids],
                bounding_box=item.bounding_box,
                content_hash=item.content_hash,
                ticker=item.ticker,
                fiscal_year=item.fiscal_year,
                fiscal_period=item.fiscal_period,
                retrieval_sources=[s.value for s in item.retrieval_sources],
                dense_score=item.dense_score,
                sparse_score=item.sparse_score,
                fusion_score=item.fusion_score,
                reranker_score=item.reranker_score,
                final_score=item.final_score,
                provenance=prov_resp,
                metadata=item.metadata,
            )
        )

    signals_resp = FinancialSignalsResponse(
        tickers=evidence_set.query.signals.tickers,
        company_names=evidence_set.query.signals.company_names,
        metrics=evidence_set.query.signals.metrics,
        fiscal_years=evidence_set.query.signals.fiscal_years,
        fiscal_periods=evidence_set.query.signals.fiscal_periods,
        sections=evidence_set.query.signals.sections,
        statement_types=evidence_set.query.signals.statement_types,
        currencies=evidence_set.query.signals.currencies,
        is_comparison=evidence_set.query.signals.is_comparison,
        is_table_lookup=evidence_set.query.signals.is_table_lookup,
        is_multi_period=evidence_set.query.signals.is_multi_period,
    )

    return RetrievalSearchResponse(
        query_id=str(evidence_set.query_id),
        raw_query=evidence_set.query.raw_query,
        normalized_query=evidence_set.query.normalized_query,
        query_type=evidence_set.query.query_type.value,
        signals=signals_resp,
        retrieval_strategy=evidence_set.retrieval_strategy,
        execution_stages=evidence_set.execution_stages,
        evidence_count=evidence_set.evidence_count,
        total_candidates=evidence_set.total_candidates,
        fallback_occurred=evidence_set.fallback_occurred,
        fallback_reason=evidence_set.fallback_reason,
        evidence=evidence_items_response,
        timing_ms=evidence_set.timing_ms,
        created_at=evidence_set.created_at,
    )


# Mount canonical alias /api/v1/search
search_router.add_api_route(
    "/search",
    search_evidence,
    methods=["POST"],
    response_model=RetrievalSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid search and evidence selection (Canonical Alias)",
    description="Canonical search route alias for /api/v1/retrieval/search.",
)
