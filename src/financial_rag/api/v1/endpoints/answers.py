from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from financial_rag.api.dependencies import (
    AnswerOrchestratorServiceDep,
    require_permission,
)
from financial_rag.api.v1.schemas import (
    AnswerMetadataResponse,
    AnswerQueryRequest,
    AnswerQueryResponse,
    CalculationInputResponse,
    CalculationResultResponse,
    CitationResponse,
    ClaimResponse,
    FinancialFactResponse,
    FinancialValueResponse,
    FiscalPeriodResponse,
    ReasoningPlanResponse,
)
from financial_rag.domain.entities.answer import AnswerRequest, ResponseStyle
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.domain.entities.security import Permission, PrincipalContext
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.api.v1.endpoints.answers")

router = APIRouter(prefix="/answers", tags=["Verified Answer Synthesis"])


@router.post(
    "",
    response_model=AnswerQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate verified natural language answer backed by deterministic reasoning and citations",
    description=(
        "Executes the full verified answer pipeline: Phase 2 hybrid retrieval -> Phase 3 deterministic "
        "arithmetic & grounding -> Answerability Gate -> Budgeted Context & Versioned Prompt -> LLM Structured "
        "Synthesis -> 8-Stage Post-Generation Validation (Schema, Citations, Numbers, Grounding) -> "
        "Bounded Retry / Safe Fallback -> Response Renderer, strictly isolated to caller's tenant."
    ),
)
async def generate_verified_answer(
    request: AnswerQueryRequest,
    answer_service: AnswerOrchestratorServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.ANSWERS_EXECUTE)),
) -> AnswerQueryResponse:
    """Orchestrate verified natural language answer generation scoped to caller's tenant."""
    logger.info(
        f"Received answer synthesis request: '{request.query}' (style={request.response_style}) from user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )

    # Map request style
    style = ResponseStyle.STANDARD
    try:
        style = ResponseStyle(request.response_style.lower())
    except ValueError:
        style = ResponseStyle.STANDARD

    # Map filters with enforced tenant isolation
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

    # Build domain request bound to authenticated caller
    domain_request = AnswerRequest(
        query=request.query,
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
        response_style=style,
        include_citations=request.include_citations,
        citation_style=request.citation_style,
        filters=domain_filter,
        top_k=request.top_k,
        use_reranker=request.use_reranker,
        custom_instructions=request.custom_instructions,
    )

    # Execute service
    answer_resp = await answer_service.generate_answer(domain_request)

    # Map domain response to API schema
    facts_resp = [
        FinancialFactResponse(
            fact_id=f.fact_id,
            metric=f.metric,
            value=FinancialValueResponse(
                raw_value=f.value.raw_value,
                display_value=f.value.display_value,
                numeric_value=str(f.value.numeric_value),
                unscaled_value=str(f.value.unscaled_value),
                currency=f.value.currency,
                scale=f.value.scale.value,
                unit=f.value.unit,
                is_negative=f.value.is_negative,
                is_percentage=f.value.is_percentage,
            ),
            period=FiscalPeriodResponse(
                fiscal_year=f.period.fiscal_year,
                period_type=f.period.period_type,
                source_text=f.period.source_text,
                start_date=f.period.start_date,
                end_date=f.period.end_date,
                is_uncertain=f.period.is_uncertain,
                label=f.period.label,
            ),
            company=f.company,
            ticker=f.ticker,
            document_id=str(f.document_id),
            document_version_id=str(f.document_version_id),
            page_number=f.page_number,
            chunk_id=f.chunk_id,
            table_id=str(f.table_id) if f.table_id else None,
            source_evidence_id=f.source_evidence_id,
            extraction_method=f.extraction_method,
            confidence=f.confidence,
            source_text=f.source_text,
            bounding_box=f.bounding_box,
            section_path=f.section_path,
            metadata=f.metadata,
        )
        for f in answer_resp.facts
    ]

    calcs_resp = [
        CalculationResultResponse(
            calculation_id=c.calculation_id,
            operation=c.operation.value,
            formula=c.formula,
            inputs=[
                CalculationInputResponse(
                    name=inp.name,
                    value=str(inp.value),
                    fact_id=inp.fact_id,
                    source_description=inp.source_description,
                    unit=inp.unit,
                    currency=inp.currency,
                )
                for inp in c.inputs
            ],
            input_fact_ids=c.input_fact_ids,
            raw_result=str(c.raw_result),
            rounded_result=str(c.rounded_result),
            display_result=c.display_result,
            unit=c.unit,
            currency=c.currency,
            rounding_precision=c.rounding_precision,
            success=c.success,
            error_message=c.error_message,
        )
        for c in answer_resp.calculations
    ]

    claims_resp = [
        ClaimResponse(
            claim_id=cl.claim_id,
            text=cl.text,
            claim_type=cl.claim_type,
            source_fact_ids=cl.source_fact_ids,
            calculation_ids=cl.calculation_ids,
            reasoning_step_ids=cl.reasoning_step_ids,
            confidence=cl.confidence,
            is_grounded=cl.is_grounded,
        )
        for cl in answer_resp.claims
    ]

    cits_resp = [
        CitationResponse(
            citation_id=str(cit.citation_id),
            claim_id=cit.claim_id,
            document_id=str(cit.document_id),
            document_version_id=str(cit.document_version_id),
            page_number=cit.page_number,
            page_numbers=cit.page_numbers,
            chunk_id=cit.chunk_id,
            table_id=str(cit.table_id) if cit.table_id else None,
            section_path=cit.section_path,
            ticker=cit.ticker,
            source_excerpt=cit.source_excerpt,
            bounding_box=cit.bounding_box,
            citation_type=cit.citation_type.value,
            verified=cit.verified,
            validation_notes=cit.validation_notes,
        )
        for cit in answer_resp.citations
    ]

    plan_resp = None
    if answer_resp.reasoning_plan:
        plan_resp = ReasoningPlanResponse(
            plan_id=answer_resp.reasoning_plan.plan_id,
            query=answer_resp.reasoning_plan.query,
            operations=[op.value for op in answer_resp.reasoning_plan.operations],
            target_metrics=answer_resp.reasoning_plan.target_metrics,
            target_periods=answer_resp.reasoning_plan.target_periods,
            target_companies=answer_resp.reasoning_plan.target_companies,
            required_fact_keys=answer_resp.reasoning_plan.required_fact_keys,
            steps_description=answer_resp.reasoning_plan.steps_description,
            is_multi_period=answer_resp.reasoning_plan.is_multi_period,
            is_comparison=answer_resp.reasoning_plan.is_comparison,
        )

    metadata_resp = AnswerMetadataResponse(
        model_name=answer_resp.metadata.get("model_name", "financial-llm-v1"),
        prompt_version=answer_resp.metadata.get("prompt_version", "FINANCIAL_ANSWER_PROMPT_V1"),
        attempts=answer_resp.metadata.get("attempts", 1),
        used_fallback=answer_resp.metadata.get("used_fallback", False),
        cache_hit=answer_resp.metadata.get("cache_hit", False),
    )

    return AnswerQueryResponse(
        answer_id=str(answer_resp.answer_id),
        query_id=str(answer_resp.query_id),
        status=answer_resp.status.value,
        answer=answer_resp.answer_text,
        claims=claims_resp,
        citations=cits_resp,
        calculations=calcs_resp,
        facts=facts_resp,
        reasoning_plan=plan_resp,
        grounding_status=answer_resp.grounding_status.value,
        confidence_score=answer_resp.confidence_score,
        warnings=answer_resp.warnings,
        metadata=metadata_resp,
        execution_time_ms=answer_resp.execution_time_ms,
        created_at=answer_resp.created_at.isoformat(),
    )


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream progressive verified answer synthesis events (Server-Sent Events)",
    description="Emits SSE events ('stage_start', 'reasoning_complete', 'token_delta', 'calculations', 'citations', 'answer_complete').",
)
async def generate_verified_answer_stream(
    request: AnswerQueryRequest,
    answer_service: AnswerOrchestratorServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.ANSWERS_EXECUTE)),
) -> StreamingResponse:
    """Stream verified answer synthesis progressive events via Server-Sent Events (SSE)."""
    import asyncio
    import json
    from collections.abc import AsyncGenerator
    from datetime import UTC, datetime

    logger.info(
        f"Received streaming answer request: '{request.query}' from user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )

    style = ResponseStyle.STANDARD
    try:
        style = ResponseStyle(request.response_style.lower())
    except ValueError:
        style = ResponseStyle.STANDARD

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

    domain_request = AnswerRequest(
        query=request.query,
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
        response_style=style,
        include_citations=request.include_citations,
        citation_style=request.citation_style,
        filters=domain_filter,
        top_k=request.top_k,
        use_reranker=request.use_reranker,
        custom_instructions=request.custom_instructions,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        seq = 0
        try:
            async for event in answer_service.generate_answer_stream(domain_request):
                if await raw_req.is_disconnected():
                    logger.info(
                        "Client disconnected from answer stream; aborting stream generation."
                    )
                    break
                seq = event.sequence
                event_dict = {
                    "sequence": event.sequence,
                    "event_type": event.event_type.value,
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat(),
                }
                yield f"data: {json.dumps(event_dict)}\n\n"
        except asyncio.CancelledError:
            logger.info("Answer streaming task cancelled (client disconnected).")
        except Exception as exc:
            logger.error(f"Error during answer event stream: {exc}")
            err_dict = {
                "sequence": seq + 1,
                "event_type": "error",
                "payload": {
                    "code": "STREAM_ERROR",
                    "message": "An error occurred during answer generation.",
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(err_dict)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
