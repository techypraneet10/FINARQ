"""Reasoning API endpoints for verified AnswerPackage generation and deterministic financial reasoning with tenant scoping."""

from fastapi import APIRouter, Depends, status

from financial_rag.api.dependencies import (
    ReasoningServiceDep,
    require_permission,
)
from financial_rag.api.v1.schemas import (
    AnswerPackageResponse,
    CalculationInputResponse,
    CalculationResultResponse,
    CitationResponse,
    ClaimResponse,
    EvidenceConflictResponse,
    FinancialFactResponse,
    FinancialValueResponse,
    FiscalPeriodResponse,
    GroundingValidationResultResponse,
    ProvenanceLineageResponse,
    RankedEvidenceResponse,
    ReasoningPlanResponse,
    ReasoningQueryRequest,
    ReasoningStepTraceResponse,
)
from financial_rag.domain.entities.reasoning import FinancialFact
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.domain.entities.security import Permission, PrincipalContext
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.api.v1.endpoints.reasoning")

router = APIRouter(prefix="/reasoning", tags=["Reasoning & Grounding Engine"])


def _map_fact_response(f: FinancialFact) -> FinancialFactResponse:
    f_val = f.value
    f_per = f.period
    return FinancialFactResponse(
        fact_id=f.fact_id,
        metric=f.metric,
        value=FinancialValueResponse(
            raw_value=f_val.raw_value,
            display_value=f_val.display_value,
            numeric_value=str(f_val.numeric_value),
            unscaled_value=str(f_val.unscaled_value),
            currency=f_val.currency,
            scale=f_val.scale.value,
            unit=f_val.unit,
            is_negative=f_val.is_negative,
            is_percentage=f_val.is_percentage,
        ),
        period=FiscalPeriodResponse(
            fiscal_year=f_per.fiscal_year,
            period_type=f_per.period_type,
            source_text=f_per.source_text,
            start_date=f_per.start_date,
            end_date=f_per.end_date,
            is_uncertain=f_per.is_uncertain,
            label=f_per.label,
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


@router.post(
    "/answer-package",
    response_model=AnswerPackageResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic financial reasoning and produce verified AnswerPackage",
    description=(
        "Transforms retrieved financial evidence into structured facts, executes deterministic "
        "arithmetic using high-precision Decimal operations, discovers potential evidence conflicts, "
        "constructs verifiable claims and citations, performs grounding verification, and assigns "
        "an explicit answerability status, strictly isolated within the caller's tenant boundary."
    ),
)
async def generate_answer_package(
    request: ReasoningQueryRequest,
    reasoning_service: ReasoningServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.RETRIEVAL_EXECUTE)),
) -> AnswerPackageResponse:
    """Execute end-to-end reasoning pipeline and return serializable AnswerPackage scoped to tenant."""
    logger.info(
        f"Received reasoning inquiry: '{request.query}' (top_k={request.top_k}) from user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )

    # Map request filters to domain RetrievalFilter bound to principal's tenant
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

    # Execute reasoning service
    package = await reasoning_service.reason(
        raw_query=request.query,
        top_k=request.top_k,
        filters=domain_filter,
        use_reranker=request.use_reranker,
    )

    # Map domain AnswerPackage to API Response Schema
    facts_resp: list[FinancialFactResponse] = [_map_fact_response(f) for f in package.facts]

    calcs_resp: list[CalculationResultResponse] = []
    for c in package.calculations:
        inputs_resp = [
            CalculationInputResponse(
                name=inp.name,
                value=str(inp.value),
                fact_id=inp.fact_id,
                source_description=inp.source_description,
                unit=inp.unit,
                currency=inp.currency,
            )
            for inp in c.inputs
        ]
        calcs_resp.append(
            CalculationResultResponse(
                calculation_id=c.calculation_id,
                operation=c.operation.value,
                formula=c.formula,
                inputs=inputs_resp,
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
        )

    trace_resp = [
        ReasoningStepTraceResponse(
            step_number=t.step_number,
            operation=t.operation.value,
            description=t.description,
            input_fact_ids=t.input_fact_ids,
            calculation_id=t.calculation_id,
            output_summary=t.output_summary,
            status=t.status,
        )
        for t in package.reasoning_trace
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
        for cl in package.claims
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
        for cit in package.citations
    ]

    evidence_resp = []
    for item in package.evidence:
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
        evidence_resp.append(
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

    conflicts_resp = []
    for conf in package.conflicts:
        conflicts_resp.append(
            EvidenceConflictResponse(
                conflict_id=conf.conflict_id,
                metric=conf.metric,
                period=conf.period,
                conflicting_facts=[_map_fact_response(f) for f in conf.conflicting_facts],
                difference_description=conf.difference_description,
                resolved=conf.resolved,
                resolved_fact_id=conf.resolved_fact_id,
                resolution_rationale=conf.resolution_rationale,
            )
        )

    grd_resp = None
    if package.grounding_validation:
        grd = package.grounding_validation
        grd_resp = GroundingValidationResultResponse(
            status=grd.status.value,
            total_claims=grd.total_claims,
            grounded_claims=grd.grounded_claims,
            ungrounded_claims=grd.ungrounded_claims,
            conflicting_claims=grd.conflicting_claims,
            unverified_citations=grd.unverified_citations,
            details=grd.details,
            validation_passed=grd.validation_passed,
        )

    plan_resp = ReasoningPlanResponse(
        plan_id=package.reasoning_plan.plan_id,
        query=package.reasoning_plan.query,
        operations=[op.value for op in package.reasoning_plan.operations],
        target_metrics=package.reasoning_plan.target_metrics,
        target_periods=package.reasoning_plan.target_periods,
        target_companies=package.reasoning_plan.target_companies,
        required_fact_keys=package.reasoning_plan.required_fact_keys,
        steps_description=package.reasoning_plan.steps_description,
        is_multi_period=package.reasoning_plan.is_multi_period,
        is_comparison=package.reasoning_plan.is_comparison,
    )

    return AnswerPackageResponse(
        package_id=package.package_id,
        query_id=str(package.query_id),
        raw_query=package.raw_query,
        normalized_query=package.normalized_query,
        answerability=package.answerability.value,
        answerability_rationale=package.answerability_rationale,
        reasoning_plan=plan_resp,
        facts=facts_resp,
        calculations=calcs_resp,
        reasoning_trace=trace_resp,
        claims=claims_resp,
        citations=cits_resp,
        evidence=evidence_resp,
        conflicts=conflicts_resp,
        missing_facts=package.missing_facts,
        grounding_validation=grd_resp,
        confidence_score=package.confidence_score,
        warnings=package.warnings,
        execution_time_ms=package.execution_time_ms,
        created_at=package.created_at.isoformat(),
    )
