"""Diagnostic failure attribution engine and pipeline error budget calculator."""

from financial_rag.domain.entities.answer import AnswerResponse, AnswerStatus
from financial_rag.domain.entities.evaluation import (
    EvaluationCase,
    FailureAttribution,
    PipelineStage,
    RegressionSeverity,
)
from financial_rag.domain.entities.models import RetrievalResult
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
)
from financial_rag.domain.interfaces.evaluation import FailureAttributionProtocol


class FailureAttributionEngine(FailureAttributionProtocol):
    """Diagnoses intermediate failures and attributes them to the earliest failing pipeline boundary."""

    def attribute_failure(
        self,
        case: EvaluationCase,
        answer_package: AnswerPackage | None,
        answer_response: AnswerResponse | None,
        retrieved_items: list[RetrievalResult] | None = None,
        error_exception: Exception | None = None,
    ) -> FailureAttribution | None:
        """Diagnose failure across pipeline boundaries in sequential order."""
        if error_exception:
            return FailureAttribution(
                case_id=case.case_id,
                first_failed_stage=PipelineStage.API,
                error_type="UNHANDLED_EXCEPTION",
                severity=RegressionSeverity.CRITICAL,
                details=f"Pipeline execution raised exception: {error_exception}",
                recommendation="Investigate service stack trace and error handling boundaries.",
            )

        # 1. RETRIEVAL Stage Diagnosis
        if retrieved_items is not None:
            if not retrieved_items and case.expected_chunk_ids:
                return FailureAttribution(
                    case_id=case.case_id,
                    first_failed_stage=PipelineStage.RETRIEVAL,
                    error_type="EMPTY_RETRIEVAL",
                    severity=RegressionSeverity.CRITICAL,
                    details="Retrieval returned 0 candidates.",
                    recommendation="Verify index health and hybrid search query expansion.",
                )

            retrieved_chunk_ids = {str(r.chunk.id) for r in retrieved_items}
            retrieved_pages = {r.chunk.page_number for r in retrieved_items}
            exp_chunks = set(case.expected_chunk_ids)
            exp_pages = set(case.expected_page_numbers)

            if (
                exp_chunks
                and not exp_chunks.intersection(retrieved_chunk_ids)
                and exp_pages
                and not exp_pages.intersection(retrieved_pages)
            ):
                return FailureAttribution(
                    case_id=case.case_id,
                    first_failed_stage=PipelineStage.RETRIEVAL,
                    error_type="TARGET_EVIDENCE_NOT_RETRIEVED",
                    severity=RegressionSeverity.CRITICAL,
                    details=f"Expected chunks {case.expected_chunk_ids} or pages {case.expected_page_numbers} not in top-K.",
                    recommendation="Tune BM25 k1/b parameters or embedding similarity thresholds.",
                )

        # 2. EVIDENCE Stage Diagnosis
        if (
            answer_package
            and case.expected_document_ids
            and not answer_package.facts
            and not answer_package.evidence
            and case.expected_answerability == AnswerabilityStatus.ANSWERABLE
        ):
            return FailureAttribution(
                case_id=case.case_id,
                first_failed_stage=PipelineStage.EVIDENCE,
                error_type="EVIDENCE_SELECTION_DROPPED_CONTEXT",
                severity=RegressionSeverity.WARNING,
                details="Evidence selector failed to retain necessary chunks for fact extraction.",
                recommendation="Adjust evidence selector token budget or relevance score threshold.",
            )

        # 3. REASONING Stage Diagnosis (Fact Extraction & Arithmetic)
        if answer_package:
            # Check fact extraction
            for exp_fact in case.expected_facts:
                matched = any(
                    exp_fact.metric.lower().replace(" ", "") in f.metric.lower().replace(" ", "")
                    for f in answer_package.facts
                )
                if not matched:
                    return FailureAttribution(
                        case_id=case.case_id,
                        first_failed_stage=PipelineStage.REASONING,
                        error_type="MISSING_EXTRACTED_FACT",
                        severity=RegressionSeverity.CRITICAL,
                        details=f"Failed to extract required financial fact: '{exp_fact.metric}'.",
                        recommendation="Improve table structure extraction and financial entity recognition.",
                    )

            # Check calculations
            for exp_calc in case.expected_calculations:
                matched_calc = False
                for act_calc in answer_package.calculations:
                    if act_calc.operation == exp_calc.operation:
                        try:
                            exp_num = float(
                                exp_calc.expected_result_str.replace("%", "").replace(",", "")
                            )
                            act_num = float(act_calc.rounded_result)
                            if (
                                abs(act_num - exp_num) <= (abs(exp_num) * exp_calc.tolerance_pct)
                                or abs(act_num - exp_num) <= 0.05
                            ):
                                matched_calc = True
                                break
                        except Exception:
                            pass
                if not matched_calc:
                    return FailureAttribution(
                        case_id=case.case_id,
                        first_failed_stage=PipelineStage.REASONING,
                        error_type="CALCULATION_MISMATCH",
                        severity=RegressionSeverity.CRITICAL,
                        details=f"Calculation mismatch for {exp_calc.operation}: expected {exp_calc.expected_result_str}.",
                        recommendation="Audit deterministic reasoning arithmetic executor and operand alignment.",
                    )

        # 4. CITATION Stage Diagnosis
        if answer_package:
            if case.expected_citations_count > 0 and len(answer_package.citations) == 0:
                return FailureAttribution(
                    case_id=case.case_id,
                    first_failed_stage=PipelineStage.CITATION,
                    error_type="MISSING_CITATIONS",
                    severity=RegressionSeverity.CRITICAL,
                    details=f"Expected {case.expected_citations_count} citations, found 0.",
                    recommendation="Verify citation builder and claim-to-chunk provenance linking.",
                )

            unverified = [c for c in answer_package.citations if not c.verified]
            if unverified:
                return FailureAttribution(
                    case_id=case.case_id,
                    first_failed_stage=PipelineStage.CITATION,
                    error_type="UNVERIFIED_CITATION",
                    severity=RegressionSeverity.WARNING,
                    details=f"Citation {unverified[0].citation_id} failed verification.",
                    recommendation="Audit citation verification engine against underlying document chunk IDs.",
                )

        # 5. LLM GENERATION & VALIDATION Stage Diagnosis
        if answer_response:
            # Check refusal correctness
            if (
                case.expected_answerability == AnswerabilityStatus.INSUFFICIENT_EVIDENCE
                and answer_response.status
                not in (AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.COMPLETED)
            ):
                return FailureAttribution(
                    case_id=case.case_id,
                    first_failed_stage=PipelineStage.LLM_GENERATION,
                    error_type="INCORRECT_REFUSAL_BEHAVIOR",
                    severity=RegressionSeverity.CRITICAL,
                    details="Expected safe refusal for out-of-corpus query, but received standard answer.",
                    recommendation="Strengthen answerability gating and negative query prompts.",
                )

            # Check forbidden answer substrings (hallucinations/injection)
            for f in case.forbidden_answer_contains:
                if f.lower() in answer_response.answer_text.lower():
                    return FailureAttribution(
                        case_id=case.case_id,
                        first_failed_stage=PipelineStage.VALIDATION,
                        error_type="FORBIDDEN_CONTENT_LEAKAGE",
                        severity=RegressionSeverity.CRITICAL,
                        details=f"Answer text contained forbidden substring: '{f}'.",
                        recommendation="Update LLM prompt guardrails and post-generation validator filters.",
                    )

        return None

    def compute_error_budget(
        self, failures: list[FailureAttribution], total_cases: int
    ) -> dict[str, dict[str, float]]:
        """Compute error budget breakdown by pipeline stage."""
        stage_counts: dict[str, int] = {stage.value: 0 for stage in PipelineStage}
        for f in failures:
            stage_counts[f.first_failed_stage.value] = (
                stage_counts.get(f.first_failed_stage.value, 0) + 1
            )

        total = max(1, total_cases)
        return {
            stage: {
                "count": count,
                "pct": round((count / float(total)) * 100.0, 2),
            }
            for stage, count in stage_counts.items()
            if count > 0
        }
