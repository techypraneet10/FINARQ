"""Application layer orchestrator for Verified LLM Answer Synthesis & Response Generation."""

import logging
import time
from collections.abc import AsyncIterator
from uuid import uuid4

from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
    AnswerStreamEvent,
    AnswerStreamEventType,
    LLMAnswerOutput,
    ValidationResult,
)
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    GroundingStatus,
)
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.domain.interfaces.answer import (
    AnswerabilityGateProtocol,
    AnswerCacheProtocol,
    AnswerOrchestratorServiceProtocol,
    AnswerValidatorProtocol,
    ContextBuilderProtocol,
    PromptBuilderProtocol,
    ResponseRendererProtocol,
)
from financial_rag.domain.interfaces.llm import LLMProviderProtocol
from financial_rag.domain.interfaces.reasoning import ReasoningServiceProtocol
from financial_rag.infrastructure.observability.cost import cost_calculator
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.telemetry import telemetry_collector
from financial_rag.infrastructure.observability.tracer import tracer

logger = logging.getLogger(__name__)


class AnswerOrchestrationService(AnswerOrchestratorServiceProtocol):
    """Orchestrates Phase 3 reasoning consumption, answerability gating, LLM synthesis, and post-generation validation."""

    def __init__(
        self,
        reasoning_service: ReasoningServiceProtocol,
        llm_provider: LLMProviderProtocol,
        context_builder: ContextBuilderProtocol,
        prompt_builder: PromptBuilderProtocol,
        answerability_gate: AnswerabilityGateProtocol,
        validator: AnswerValidatorProtocol,
        renderer: ResponseRendererProtocol,
        cache: AnswerCacheProtocol | None = None,
        max_retries: int = 1,
        model_name: str = "financial-llm-v1",
    ) -> None:
        self.reasoning_service = reasoning_service
        self.llm_provider = llm_provider
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.answerability_gate = answerability_gate
        self.validator = validator
        self.renderer = renderer
        self.cache = cache
        self.max_retries = max_retries
        self.model_name = model_name

    async def generate_answer(self, request: AnswerRequest) -> AnswerResponse:
        """Execute the end-to-end verified answer generation pipeline."""
        timings: dict[str, float] = {}
        total_start = time.perf_counter()

        logger.info(
            "answer_orchestration_started",
            extra={"query": request.query, "style": request.response_style.value},
        )

        async with tracer.async_span(
            "answer.orchestration",
            attributes={"style": request.response_style.value, "model": self.model_name},
        ):
            # Stage 1: Phase 3 Reasoning & AnswerPackage Generation
            r_start = time.perf_counter()
            filters = request.filters
            if filters is None or not filters.tenant_id:
                orig_custom = dict(filters.custom_metadata) if filters else {}
                filters = RetrievalFilter(
                    document_ids=filters.document_ids if filters else None,
                    version_ids=filters.version_ids if filters else None,
                    tenant_id=request.tenant_id,
                    ticker_symbols=filters.ticker_symbols if filters else None,
                    fiscal_years=filters.fiscal_years if filters else None,
                    fiscal_periods=filters.fiscal_periods if filters else None,
                    document_types=filters.document_types if filters else None,
                    sections=filters.sections if filters else None,
                    chunk_types=filters.chunk_types if filters else None,
                    table_only=filters.table_only if filters else None,
                    custom_metadata=orig_custom,
                )

            answer_package: AnswerPackage = await self.reasoning_service.reason(
                raw_query=request.query,
                filters=filters,
                top_k=request.top_k,
                use_reranker=request.use_reranker,
            )
            timings["reasoning_ms"] = (time.perf_counter() - r_start) * 1000.0

            # Stage 2: Answerability Gate Check
            gate_start = time.perf_counter()
            with tracer.span("answer.answerability_gate"):
                intercepted_response = self.answerability_gate.evaluate_gate(
                    answer_package, request
                )
            timings["gate_ms"] = (time.perf_counter() - gate_start) * 1000.0

            if intercepted_response is not None:
                logger.info(
                    "answerability_gate_intercepted",
                    extra={"status": intercepted_response.status.value},
                )
                timings["total_ms"] = (time.perf_counter() - total_start) * 1000.0
                intercepted_response.execution_time_ms = timings
                intercepted_response.tenant_id = request.tenant_id
                intercepted_response.user_id = request.user_id
                return intercepted_response

            # Stage 3: Context & Prompt Construction
            ctx_start = time.perf_counter()
            with tracer.span("answer.context_and_prompt"):
                context = self.context_builder.build_context(answer_package)
                prompt, system_instruction, prompt_version = self.prompt_builder.build_prompt(
                    request, context, answer_package
                )
            timings["prompt_construction_ms"] = (time.perf_counter() - ctx_start) * 1000.0

            # Stage 4: Cache Check
            cache_key = ""
            if self.cache is not None:
                with tracer.span("answer.cache_lookup"):
                    facts_sig = sorted(
                        f"{f.company}:{f.metric}:{f.period.label}:{f.value.numeric_value}"
                        for f in answer_package.facts
                    )
                    calcs_sig = sorted(
                        f"{c.operation.value}:{c.formula}:{c.raw_result}"
                        for c in answer_package.calculations
                    )
                    pkg_fingerprint = f"{request.tenant_id}|{answer_package.normalized_query}|facts:{facts_sig}|calcs:{calcs_sig}"
                    cache_key = self.cache.build_cache_key(
                        request=request,
                        package_id=pkg_fingerprint,
                        prompt_version=prompt_version,
                        model_name=self.model_name,
                    )
                    cached_resp = await self.cache.get(cache_key)

                if cached_resp is not None:
                    logger.info("answer_cache_hit", extra={"cache_key": cache_key})
                    timings["total_ms"] = (time.perf_counter() - total_start) * 1000.0
                    cached_resp.execution_time_ms = timings
                    return cached_resp

            # Stage 5: Gated LLM Generation & Bounded Validation Loop
            llm_start = time.perf_counter()
            llm_output: LLMAnswerOutput | None = None
            validation_result: ValidationResult | None = None
            current_prompt = prompt
            attempts = 0
            used_fallback = False
            fallback_reason = ""

            while attempts <= self.max_retries:
                attempts += 1
                try:
                    async with tracer.async_span(
                        "answer.llm_call",
                        attributes={"attempt": attempts, "model": self.model_name},
                    ):
                        llm_output = await self.llm_provider.structured_generate(
                            prompt=current_prompt,
                            response_schema=LLMAnswerOutput,
                            system_instruction=system_instruction,
                            temperature=0.0,
                        )
                    with tracer.span("answer.validation", attributes={"attempt": attempts}):
                        validation_result = self.validator.validate_answer(
                            llm_output=llm_output,
                            answer_package=answer_package,
                            request=request,
                        )

                    if validation_result.valid:
                        metrics_registry.record_validation_metrics(rule="all_rules", status="valid")
                        break  # Passed validation!

                    metrics_registry.record_validation_metrics(rule="all_rules", status="invalid")
                    for f in validation_result.failures:
                        rule_name = (
                            f.failure_type.value if hasattr(f, "failure_type") else "rule_failure"
                        )
                        metrics_registry.record_validation_metrics(
                            rule=str(rule_name), status="invalid"
                        )

                    logger.warning(
                        "llm_output_validation_failed",
                        extra={
                            "attempt": attempts,
                            "failures": [f.message for f in validation_result.failures],
                        },
                    )

                    if attempts <= self.max_retries and validation_result.retry_recommended:
                        current_prompt = self.prompt_builder.build_correction_prompt(
                            base_prompt=prompt,
                            failures=validation_result.failures,
                        )
                    else:
                        used_fallback = True
                        fallback_reason = f"Validation failed after {attempts} attempts: {'; '.join(f.message for f in validation_result.failures)}"
                        break

                except Exception as e:
                    logger.error(
                        "llm_provider_execution_error",
                        extra={"error": str(e), "attempt": attempts},
                    )
                    used_fallback = True
                    fallback_reason = f"LLM provider error: {e}"
                    break

            llm_duration_ms = (time.perf_counter() - llm_start) * 1000.0
            timings["llm_generation_ms"] = llm_duration_ms

            # Record LLM Telemetry & Cost
            if llm_output is not None:
                in_tok = len(current_prompt.split()) * 2  # Approximate input tokens
                out_tok = (
                    len(llm_output.summary.split()) + len(llm_output.detailed_answer.split())
                ) * 2
                cost = cost_calculator.calculate_cost(
                    model_name=self.model_name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                )
                metrics_registry.record_llm_usage(
                    model=self.model_name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=llm_duration_ms,
                    cost_usd=cost,
                )

            # Stage 6: Rendering
            render_start = time.perf_counter()
            with tracer.span("answer.rendering"):
                if (
                    used_fallback
                    or llm_output is None
                    or validation_result is None
                    or not validation_result.valid
                ):
                    telemetry_collector.record_fallback(
                        component="answer_synthesis",
                        reason=fallback_reason or "Validation or provider failure",
                    )
                    final_text = self.renderer.render_deterministic_fallback(
                        answer_package=answer_package,
                        request=request,
                        reason=fallback_reason or "Safe deterministic fallback",
                    )
                    status = (
                        AnswerStatus.PARTIALLY_ANSWERED
                        if answer_package.answerability == AnswerabilityStatus.PARTIALLY_ANSWERABLE
                        else AnswerStatus.COMPLETED
                    )
                    warnings = list(answer_package.warnings)
                    if fallback_reason:
                        warnings.append(f"Fallback utilized: {fallback_reason}")
                else:
                    final_text = self.renderer.render_response(
                        llm_output=llm_output,
                        answer_package=answer_package,
                        request=request,
                        validation_result=validation_result,
                    )
                    status = (
                        AnswerStatus.PARTIALLY_ANSWERED
                        if answer_package.answerability == AnswerabilityStatus.PARTIALLY_ANSWERABLE
                        else AnswerStatus.COMPLETED
                    )
                    warnings = list(answer_package.warnings) + llm_output.warnings

            timings["rendering_ms"] = (time.perf_counter() - render_start) * 1000.0
            timings["total_ms"] = (time.perf_counter() - total_start) * 1000.0

            response = AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                status=status,
                answer_text=final_text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=(
                    answer_package.grounding_validation.status
                    if answer_package.grounding_validation
                    else GroundingStatus.GROUNDED
                ),
                confidence_score=0.95 if not used_fallback else 0.85,
                warnings=warnings,
                metadata={
                    "model_name": self.model_name,
                    "prompt_version": prompt_version,
                    "attempts": attempts,
                    "used_fallback": used_fallback,
                    "cache_hit": False,
                    "tenant_id": request.tenant_id,
                },
                execution_time_ms=timings,
            )

            # Cache response
            if self.cache is not None and cache_key and not used_fallback:
                await self.cache.set(cache_key, response)

            logger.info(
                "answer_orchestration_completed",
                extra={"status": response.status.value, "total_ms": timings["total_ms"]},
            )
            return response

    async def generate_answer_stream(
        self, request: AnswerRequest
    ) -> AsyncIterator[AnswerStreamEvent]:
        """Execute and stream progressive verified answer synthesis events."""
        seq = 0
        stream_start = time.perf_counter()
        metrics_registry.record_sse_metrics(event_type="stream_start")

        # Helper to yield event
        def make_event(event_type: AnswerStreamEventType, payload: dict) -> AnswerStreamEvent:
            nonlocal seq
            seq += 1
            metrics_registry.record_sse_metrics(event_type=event_type.value)
            return AnswerStreamEvent(sequence=seq, event_type=event_type, payload=payload)

        # 1. Stage: Reasoning
        yield make_event(
            AnswerStreamEventType.STAGE_START, {"stage": "reasoning", "query": request.query}
        )

        filters = request.filters
        if filters is None or not filters.tenant_id:
            orig_custom = dict(filters.custom_metadata) if filters else {}
            filters = RetrievalFilter(
                document_ids=filters.document_ids if filters else None,
                version_ids=filters.version_ids if filters else None,
                tenant_id=request.tenant_id,
                ticker_symbols=filters.ticker_symbols if filters else None,
                fiscal_years=filters.fiscal_years if filters else None,
                fiscal_periods=filters.fiscal_periods if filters else None,
                document_types=filters.document_types if filters else None,
                sections=filters.sections if filters else None,
                chunk_types=filters.chunk_types if filters else None,
                table_only=filters.table_only if filters else None,
                custom_metadata=orig_custom,
            )

        try:
            answer_package = await self.reasoning_service.reason(
                raw_query=request.query,
                filters=filters,
                top_k=request.top_k,
                use_reranker=request.use_reranker,
            )
        except Exception as e:
            logger.error(f"Reasoning service error during stream: {e}")
            metrics_registry.record_sse_metrics(event_type="error", disconnected=True)
            yield make_event(AnswerStreamEventType.ERROR, {"error": str(e), "stage": "reasoning"})
            return

        yield make_event(
            AnswerStreamEventType.REASONING_COMPLETE,
            {
                "answerability": answer_package.answerability.value,
                "facts_count": len(answer_package.facts),
                "calculations_count": len(answer_package.calculations),
                "citations_count": len(answer_package.citations),
                "grounding_status": (
                    answer_package.grounding_validation.status.value
                    if answer_package.grounding_validation
                    else "grounded"
                ),
            },
        )

        # 2. Gate check
        intercepted = self.answerability_gate.evaluate_gate(answer_package, request)
        if intercepted is not None:
            yield make_event(
                AnswerStreamEventType.TOKEN_DELTA,
                {"delta": intercepted.answer_text},
            )
            yield make_event(
                AnswerStreamEventType.ANSWER_COMPLETE,
                {
                    "answer_id": str(intercepted.answer_id),
                    "status": intercepted.status.value,
                    "final_text": intercepted.answer_text,
                    "confidence_score": intercepted.confidence_score,
                    "warnings": intercepted.warnings,
                },
            )
            duration_ms = (time.perf_counter() - stream_start) * 1000.0
            metrics_registry.record_sse_metrics(
                event_type="stream_complete", duration_ms=duration_ms
            )
            return

        # 3. Emit calculations & citations metadata early
        calcs_payload = [
            {
                "calculation_id": c.calculation_id,
                "operation": c.operation.value,
                "formula": c.formula,
                "display_result": c.display_result,
                "success": c.success,
            }
            for c in answer_package.calculations
        ]
        if calcs_payload:
            yield make_event(AnswerStreamEventType.CALCULATIONS, {"calculations": calcs_payload})

        cits_payload = [
            {
                "citation_id": str(c.citation_id),
                "document_id": str(c.document_id),
                "page_number": c.page_number,
                "section_path": c.section_path,
                "source_excerpt": c.source_excerpt,
            }
            for c in answer_package.citations
        ]
        if cits_payload:
            yield make_event(AnswerStreamEventType.CITATIONS, {"citations": cits_payload})

        # 4. Prompt construction & Generation
        yield make_event(
            AnswerStreamEventType.STAGE_START, {"stage": "generation", "model": self.model_name}
        )
        context = self.context_builder.build_context(answer_package)
        prompt, system_instruction, prompt_version = self.prompt_builder.build_prompt(
            request, context, answer_package
        )

        accumulated_text = ""
        try:
            async for token in self.llm_provider.generate_stream(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.0,
            ):
                accumulated_text += token
                yield make_event(AnswerStreamEventType.TOKEN_DELTA, {"delta": token})
        except Exception as ex:
            logger.warning(
                f"Streaming token generation failed: {ex}. Falling back to deterministic fallback."
            )
            fallback_text = self.renderer.render_deterministic_fallback(
                answer_package=answer_package,
                request=request,
                reason=f"LLM streaming error: {ex}",
            )
            yield make_event(AnswerStreamEventType.TOKEN_DELTA, {"delta": fallback_text})
            accumulated_text = fallback_text

        # 5. Complete event
        yield make_event(
            AnswerStreamEventType.ANSWER_COMPLETE,
            {
                "answer_id": str(uuid4()),
                "status": "completed",
                "final_text": accumulated_text,
                "model_name": self.model_name,
                "prompt_version": prompt_version,
            },
        )
        duration_ms = (time.perf_counter() - stream_start) * 1000.0
        metrics_registry.record_sse_metrics(event_type="stream_complete", duration_ms=duration_ms)
