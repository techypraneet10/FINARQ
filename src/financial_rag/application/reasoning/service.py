"""Reasoning application service orchestrating retrieval, fact extraction, calculations, and grounding."""

import time
from uuid import uuid4

from financial_rag.domain.entities.reasoning import (
    AnswerPackage,
    CalculationResult,
    FinancialFact,
    ReasoningOperation,
    ReasoningStepTrace,
)
from financial_rag.domain.entities.retrieval import RetrievalFilter
from financial_rag.domain.interfaces.reasoning import (
    AnswerabilityEvaluatorProtocol,
    CitationGeneratorProtocol,
    CitationValidatorProtocol,
    ClaimBuilderProtocol,
    ConflictDetectorProtocol,
    FactExtractorProtocol,
    FinancialCalculatorProtocol,
    GroundingValidatorProtocol,
    ReasoningPlannerProtocol,
    ReasoningServiceProtocol,
)
from financial_rag.domain.interfaces.retrieval import RetrievalServiceProtocol
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.tracer import tracer
from financial_rag.infrastructure.reasoning.answerability import (
    DeterministicAnswerabilityEvaluator,
)
from financial_rag.infrastructure.reasoning.calculator import (
    DeterministicFinancialCalculator,
)
from financial_rag.infrastructure.reasoning.citation_generator import (
    DeterministicCitationGenerator,
)
from financial_rag.infrastructure.reasoning.citation_validator import (
    DeterministicCitationValidator,
)
from financial_rag.infrastructure.reasoning.claim_builder import (
    DeterministicClaimBuilder,
)
from financial_rag.infrastructure.reasoning.conflict_detector import (
    DeterministicConflictDetector,
)
from financial_rag.infrastructure.reasoning.fact_extractor import (
    DeterministicFactExtractor,
)
from financial_rag.infrastructure.reasoning.grounding_validator import (
    DeterministicGroundingValidator,
)
from financial_rag.infrastructure.reasoning.planner import (
    DeterministicReasoningPlanner,
)

logger = get_logger("financial_rag.application.reasoning.service")


class ReasoningService(ReasoningServiceProtocol):
    """Orchestrates end-to-end deterministic financial reasoning and evidence grounding."""

    def __init__(
        self,
        retrieval_service: RetrievalServiceProtocol,
        planner: ReasoningPlannerProtocol | None = None,
        fact_extractor: FactExtractorProtocol | None = None,
        calculator: FinancialCalculatorProtocol | None = None,
        conflict_detector: ConflictDetectorProtocol | None = None,
        claim_builder: ClaimBuilderProtocol | None = None,
        citation_generator: CitationGeneratorProtocol | None = None,
        citation_validator: CitationValidatorProtocol | None = None,
        grounding_validator: GroundingValidatorProtocol | None = None,
        answerability_evaluator: AnswerabilityEvaluatorProtocol | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.planner = planner or DeterministicReasoningPlanner()
        self.fact_extractor = fact_extractor or DeterministicFactExtractor()
        self.calculator = calculator or DeterministicFinancialCalculator()
        self.conflict_detector = conflict_detector or DeterministicConflictDetector()
        self.claim_builder = claim_builder or DeterministicClaimBuilder()
        self.citation_generator = citation_generator or DeterministicCitationGenerator()
        self.citation_validator = citation_validator or DeterministicCitationValidator()
        self.grounding_validator = grounding_validator or DeterministicGroundingValidator()
        self.answerability_evaluator = (
            answerability_evaluator or DeterministicAnswerabilityEvaluator()
        )

    def _matches_metric(self, target: str, candidate: str) -> bool:
        t = target.lower()
        c = candidate.lower()
        if t in c or c in t:
            return True
        for group in DeterministicAnswerabilityEvaluator.SYNONYM_GROUPS:
            if any(term in t for term in group) and any(term in c for term in group):
                return True
        return False

    def _select_target_facts(
        self,
        all_facts: list[FinancialFact],
        target_metrics: list[str],
        target_periods: list[str],
    ) -> list[FinancialFact]:
        """Select facts matching target metrics and periods, prioritizing table facts."""
        if not target_metrics and not target_periods:
            return all_facts

        matched_facts: list[FinancialFact] = []
        for fact in all_facts:
            metric_match = True
            if target_metrics:
                metric_match = any(self._matches_metric(tm, fact.metric) for tm in target_metrics)

            period_match = True
            if target_periods:
                period_match = any(
                    tp.lower() in fact.period.label.lower()
                    or fact.period.label.lower() in tp.lower()
                    or (fact.period.fiscal_year and tp in str(fact.period.fiscal_year))
                    for tp in target_periods
                )

            if metric_match and period_match:
                matched_facts.append(fact)

        # If strict matching produced facts, prefer them; otherwise fall back to all extracted facts
        selected = matched_facts if matched_facts else all_facts

        # Deduplicate facts by (metric, period), prioritizing table_structured over narrative
        dedup_map: dict[tuple[str, str], FinancialFact] = {}
        for f in selected:
            key = (f.metric.lower(), f.period.label.lower())
            if key not in dedup_map:
                dedup_map[key] = f
            else:
                existing = dedup_map[key]
                if (
                    "table" in f.extraction_method and "table" not in existing.extraction_method
                ) or f.confidence > existing.confidence:
                    dedup_map[key] = f

        return list(dedup_map.values())

    async def reason(
        self,
        raw_query: str,
        top_k: int = 10,
        filters: RetrievalFilter | None = None,
        use_reranker: bool = True,
    ) -> AnswerPackage:
        """Execute end-to-end reasoning workflow and return verified AnswerPackage."""
        package_id = str(uuid4())
        timing: dict[str, float] = {}
        t0 = time.perf_counter()

        logger.info(
            f"Initiating reasoning execution for query: '{raw_query}' (package_id={package_id})"
        )

        async with tracer.async_span("reasoning.pipeline", attributes={"package_id": package_id}):
            # 1. Retrieval stage
            t_ret_0 = time.perf_counter()
            evidence_set = await self.retrieval_service.search(
                raw_query=raw_query,
                filters=filters,
                top_k=top_k,
                use_reranker=use_reranker,
            )
            timing["retrieval_ms"] = round((time.perf_counter() - t_ret_0) * 1000, 2)

            # 2. Planning stage
            t_plan_0 = time.perf_counter()
            with tracer.span("reasoning.planning"):
                plan = self.planner.plan(evidence_set.query)
            timing["planning_ms"] = round((time.perf_counter() - t_plan_0) * 1000, 2)

            # 3. Fact extraction stage
            t_fact_0 = time.perf_counter()
            with tracer.span("reasoning.fact_extraction"):
                all_extracted_facts = self.fact_extractor.extract_facts(evidence_set.items)
                target_facts = self._select_target_facts(
                    all_facts=all_extracted_facts,
                    target_metrics=plan.target_metrics,
                    target_periods=plan.target_periods,
                )
            timing["fact_extraction_ms"] = round((time.perf_counter() - t_fact_0) * 1000, 2)

            # 4. Conflict detection
            t_conf_0 = time.perf_counter()
            with tracer.span("reasoning.conflict_detection"):
                conflicts = self.conflict_detector.detect_conflicts(all_extracted_facts)
            timing["conflict_detection_ms"] = round((time.perf_counter() - t_conf_0) * 1000, 2)

            # 5. Deterministic arithmetic calculation
            t_calc_0 = time.perf_counter()
            calculations: list[CalculationResult] = []
            reasoning_trace: list[ReasoningStepTrace] = []
            step_num = 1

            # Trace fact lookup steps
            for f in target_facts:
                reasoning_trace.append(
                    ReasoningStepTrace(
                        step_number=step_num,
                        operation=ReasoningOperation.DIRECT_LOOKUP,
                        description=f"Extracted verified fact: {f.metric} for {f.period.label} = {f.value.display_value}",
                        input_fact_ids=[f.fact_id],
                        calculation_id=None,
                        output_summary=f.value.display_value,
                        status="success",
                    )
                )
                step_num += 1

            # Execute planned calculations if not just DIRECT_LOOKUP
            with tracer.span("reasoning.calculation"):
                for op in plan.operations:
                    if op != ReasoningOperation.DIRECT_LOOKUP:
                        calc_result = self.calculator.execute(operation=op, facts=target_facts)
                        calculations.append(calc_result)
                        reasoning_trace.append(
                            ReasoningStepTrace(
                                step_number=step_num,
                                operation=op,
                                description=f"Executed calculation '{op.value}' with formula: {calc_result.formula}",
                                input_fact_ids=calc_result.input_fact_ids,
                                calculation_id=calc_result.calculation_id,
                                output_summary=calc_result.display_result,
                                status="success" if calc_result.success else "failed",
                            )
                        )
                        step_num += 1
                        metrics_registry.record_reasoning_metrics(
                            operation=op.value,
                            duration_ms=0.0,
                            status="success" if calc_result.success else "failed",
                        )
            timing["calculation_ms"] = round((time.perf_counter() - t_calc_0) * 1000, 2)

            # 6. Claim construction
            t_claim_0 = time.perf_counter()
            with tracer.span("reasoning.claim_building"):
                claims = self.claim_builder.build_claims(
                    plan=plan,
                    facts=target_facts,
                    calculations=calculations,
                )
            timing["claim_building_ms"] = round((time.perf_counter() - t_claim_0) * 1000, 2)

            # 7. Citation generation & validation
            t_cit_0 = time.perf_counter()
            with tracer.span("reasoning.citations"):
                raw_citations = self.citation_generator.generate_citations(
                    claims=claims,
                    facts=target_facts,
                    evidence_items=evidence_set.items,
                )
                validated_citations = self.citation_validator.validate_citations(
                    citations=raw_citations,
                    evidence_items=evidence_set.items,
                )
            timing["citation_ms"] = round((time.perf_counter() - t_cit_0) * 1000, 2)

            # 8. Grounding validation
            t_grd_0 = time.perf_counter()
            with tracer.span("reasoning.grounding"):
                grounding_result = self.grounding_validator.validate(
                    claims=claims,
                    facts=target_facts,
                    calculations=calculations,
                    citations=validated_citations,
                    conflicts=conflicts,
                )
            timing["grounding_ms"] = round((time.perf_counter() - t_grd_0) * 1000, 2)

            # 9. Answerability evaluation
            t_ans_0 = time.perf_counter()
            with tracer.span("reasoning.answerability"):
                answerability, rationale, missing_facts = self.answerability_evaluator.evaluate(
                    plan=plan,
                    facts=target_facts,
                    calculations=calculations,
                    conflicts=conflicts,
                    grounding=grounding_result,
                )
            timing["answerability_ms"] = round((time.perf_counter() - t_ans_0) * 1000, 2)

            timing["total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            metrics_registry.record_reasoning_metrics(
                operation="pipeline",
                duration_ms=timing["total_ms"],
                status="success",
            )

            confidence = 1.0
            if answerability != "answerable":
                confidence = 0.5 if "partial" in answerability.value else 0.0

            package = AnswerPackage(
                package_id=package_id,
                query_id=evidence_set.query_id,
                raw_query=raw_query,
                normalized_query=evidence_set.query.normalized_query,
                answerability=answerability,
                answerability_rationale=rationale,
                reasoning_plan=plan,
                facts=target_facts,
                calculations=calculations,
                reasoning_trace=reasoning_trace,
                claims=claims,
                citations=validated_citations,
                evidence=evidence_set.items,
                conflicts=conflicts,
                missing_facts=missing_facts,
                grounding_validation=grounding_result,
                confidence_score=confidence,
                warnings=[c.difference_description for c in conflicts if c.resolved],
                execution_time_ms=timing,
            )

            logger.info(
                f"Completed reasoning execution (package_id={package_id}, "
                f"answerability={answerability.value}, facts={len(target_facts)}, "
                f"claims={len(claims)}, citations={len(validated_citations)}, time={timing['total_ms']}ms)"
            )
            return package
