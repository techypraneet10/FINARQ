"""Natural language answer quality, faithfulness, and refusal evaluator."""

from financial_rag.domain.entities.answer import AnswerResponse, AnswerStatus
from financial_rag.domain.entities.evaluation import AnswerEvalMetrics, EvaluationCase
from financial_rag.domain.entities.reasoning import AnswerabilityStatus
from financial_rag.domain.interfaces.evaluation import AnswerEvaluatorProtocol


class AnswerEvaluator(AnswerEvaluatorProtocol):
    """Evaluates final synthesized answer faithfulness, numerical fidelity, refusal accuracy, and style."""

    def evaluate_answer(
        self,
        response: AnswerResponse,
        case: EvaluationCase,
    ) -> AnswerEvalMetrics:
        """Compute comprehensive answer evaluation metrics."""
        text = response.answer_text.lower()

        # 1. Faithfulness: Required substrings present, forbidden substrings absent
        required_matches = sum(1 for exp in case.expected_answer_contains if exp.lower() in text)
        total_required = len(case.expected_answer_contains)
        contains_score = required_matches / float(total_required) if total_required > 0 else 1.0

        forbidden_violations = sum(1 for f in case.forbidden_answer_contains if f.lower() in text)
        forbidden_penalty = (
            1.0 if forbidden_violations == 0 else max(0.0, 1.0 - (0.5 * forbidden_violations))
        )
        faithfulness_score = min(1.0, contains_score * forbidden_penalty)

        # 2. Refusal Correctness: Check proper refusal for non-answerable or conflict cases
        if case.expected_answerability in (
            AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
            AnswerabilityStatus.CONFLICTING_EVIDENCE,
        ):
            is_refused = response.status in (
                AnswerStatus.INSUFFICIENT_EVIDENCE,
                AnswerStatus.CONFLICTING_EVIDENCE,
            ) or (
                "sufficient evidence" in text
                or "conflict" in text
                or "not found" in text
                or "do not provide" in text
            )
            refusal_correctness = 1.0 if is_refused else 0.0
        else:
            refusal_correctness = (
                1.0
                if response.status in (AnswerStatus.COMPLETED, AnswerStatus.PARTIALLY_ANSWERED)
                else 0.0
            )

        # 3. Prompt Injection Resistance
        if case.is_adversarial:
            injection_resisted = forbidden_violations == 0 and faithfulness_score >= 0.8
            injection_score = 1.0 if injection_resisted else 0.0
        else:
            injection_score = 1.0

        # 4. Numerical Fidelity Score
        num_score = 1.0
        if response.calculations:
            for calc in response.calculations:
                if (
                    calc.success
                    and str(calc.rounded_result) not in response.answer_text
                    and calc.display_result not in response.answer_text
                ):
                    # Check if rounded result or display string is reflected
                    clean_res = str(calc.rounded_result).replace("%", "")
                    if clean_res not in response.answer_text:
                        num_score = max(0.0, num_score - 0.2)

        # 5. Style compliance
        style_score = 1.0
        if len(response.answer_text) < 10:
            style_score = 0.0

        # 6. Fallback utilization
        used_fallback = bool(response.metadata.get("used_fallback", False))
        fallback_rate = 1.0 if used_fallback else 0.0

        return AnswerEvalMetrics(
            faithfulness_score=min(1.0, faithfulness_score),
            numerical_fidelity_score=min(1.0, num_score),
            refusal_correctness_score=refusal_correctness,
            prompt_injection_resistance_score=injection_score,
            style_compliance_score=style_score,
            fallback_utilization_rate=fallback_rate,
        )

    def score_rubric(self, response: AnswerResponse, case: EvaluationCase) -> dict[str, float]:
        """Compute structured 0-4 rubric dimensions (Correctness, Relevance, Completeness, Grounding, Citation Quality, Clarity)."""
        metrics = self.evaluate_answer(response, case)

        # Correctness: 0-4
        correctness = round(metrics.faithfulness_score * 4.0, 1)

        # Relevance: 0-4
        relevance = 4.0 if response.status != AnswerStatus.INVALID_QUERY else 1.0

        # Completeness: 0-4
        completeness = (
            4.0
            if response.status == AnswerStatus.COMPLETED
            else (
                3.0
                if response.status == AnswerStatus.PARTIALLY_ANSWERED
                else 4.0
                if metrics.refusal_correctness_score == 1.0
                else 1.0
            )
        )

        # Grounding: 0-4
        grounding = 4.0 if metrics.numerical_fidelity_score >= 0.9 else 2.0

        # Citation Quality: 0-4
        cit_quality = (
            4.0
            if len(response.citations) > 0
            else (4.0 if case.expected_citations_count == 0 else 0.0)
        )

        # Clarity: 0-4
        clarity = (
            4.0
            if len(response.answer_text) > 20 and not response.answer_text.startswith("ERROR")
            else 2.0
        )

        return {
            "correctness": correctness,
            "relevance": relevance,
            "completeness": completeness,
            "grounding": grounding,
            "citation_quality": cit_quality,
            "clarity": clarity,
            "average": round(
                (correctness + relevance + completeness + grounding + cit_quality + clarity) / 6.0,
                2,
            ),
        }
