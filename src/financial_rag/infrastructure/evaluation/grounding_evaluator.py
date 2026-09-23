"""Evidence grounding and unsupported claim evaluator."""

from financial_rag.domain.entities.evaluation import EvaluationCase, GroundingEvalMetrics
from financial_rag.domain.entities.reasoning import AnswerPackage, GroundingStatus
from financial_rag.domain.interfaces.evaluation import GroundingEvaluatorProtocol


class GroundingEvaluator(GroundingEvaluatorProtocol):
    """Evaluates factual grounding consistency and unsupported claim rate."""

    def evaluate_grounding(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> GroundingEvalMetrics:
        """Compute grounding compliance metrics."""
        validation = answer_package.grounding_validation

        if validation is None:
            # If no validation was performed, evaluate based on package claims
            claims = answer_package.claims
            if not claims:
                return GroundingEvalMetrics(
                    grounded_answer_rate=1.0,
                    unsupported_claim_rate=0.0,
                    grounding_failure_rate=0.0,
                )
            ungrounded = sum(1 for c in claims if not c.is_grounded)
            unsupported_rate = float(ungrounded) / float(len(claims))
            return GroundingEvalMetrics(
                grounded_answer_rate=1.0 if unsupported_rate == 0.0 else 0.0,
                unsupported_claim_rate=unsupported_rate,
                grounding_failure_rate=1.0 if unsupported_rate > 0.5 else 0.0,
            )

        # Evaluate against expected grounding status
        is_expected_status = validation.status == case.expected_grounding_status
        grounded_rate = (
            1.0 if is_expected_status or validation.status == GroundingStatus.GROUNDED else 0.0
        )

        total_claims = max(1, validation.total_claims)
        unsupported_rate = validation.ungrounded_claims / float(total_claims)
        failure_rate = 1.0 if validation.status == GroundingStatus.UNGROUNDED else 0.0

        return GroundingEvalMetrics(
            grounded_answer_rate=grounded_rate,
            unsupported_claim_rate=unsupported_rate,
            grounding_failure_rate=failure_rate,
        )
