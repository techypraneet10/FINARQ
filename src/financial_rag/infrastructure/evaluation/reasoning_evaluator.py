from decimal import Decimal
from typing import Any

from financial_rag.domain.entities.evaluation import (
    EvaluationCase,
    FactExtractionEvalMetrics,
    NumericalErrorType,
    NumericalReasoningEvalMetrics,
)
from financial_rag.domain.entities.reasoning import AnswerPackage, CalculationResult
from financial_rag.domain.interfaces.evaluation import ReasoningEvaluatorProtocol


def _parse_financial_number(s: str) -> float:
    """Parse financial number strings including parenthetical negatives (e.g. '(1,234)' -> -1234.0)."""
    clean = s.strip().replace("$", "").replace("%", "").replace(",", "")
    if clean.startswith("(") and clean.endswith(")"):
        return -float(clean[1:-1])
    return float(clean)


class ReasoningEvaluator(ReasoningEvaluatorProtocol):
    """Evaluates fact extraction precision/recall and deterministic arithmetic accuracy."""

    def evaluate_fact_extraction(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> FactExtractionEvalMetrics:
        """Compute precision, recall, F1, and attribute accuracy for extracted facts."""
        expected_facts = case.expected_facts
        if not expected_facts:
            return FactExtractionEvalMetrics(
                exact_match=1.0,
                precision=1.0,
                recall=1.0,
                f1=1.0,
                value_accuracy=1.0,
                scale_accuracy=1.0,
                period_accuracy=1.0,
            )

        extracted_facts = answer_package.facts
        if not extracted_facts:
            return FactExtractionEvalMetrics()

        matched_expected = 0
        value_matches = 0
        scale_matches = 0
        period_matches = 0

        for exp in expected_facts:
            exp_metric_clean = exp.metric.lower().replace(" ", "").replace("_", "")
            found_match = False

            for act in extracted_facts:
                act_metric_clean = act.metric.lower().replace(" ", "").replace("_", "")
                if exp_metric_clean in act_metric_clean or act_metric_clean in exp_metric_clean:
                    found_match = True
                    # Check period
                    if exp.fiscal_year is None or act.period.fiscal_year == exp.fiscal_year:
                        period_matches += 1
                    # Check scale
                    if exp.scale is None or (
                        act.value.scale and exp.scale.lower() in act.value.scale.name.lower()
                    ):
                        scale_matches += 1
                    # Check value
                    if exp.expected_value is None:
                        value_matches += 1
                    else:
                        try:
                            exp_num = _parse_financial_number(str(exp.expected_value))
                            exp_dec = Decimal(str(exp_num))
                            if (
                                act.value.unscaled_value == exp_dec
                                or act.value.numeric_value == exp_dec
                                or abs(act.value.unscaled_value - exp_dec) <= Decimal("0.05")
                            ):
                                value_matches += 1
                        except Exception:
                            if str(exp.expected_value) in act.value.raw_value:
                                value_matches += 1
                    break

            if found_match:
                matched_expected += 1

        precision = matched_expected / float(len(extracted_facts)) if extracted_facts else 0.0
        recall = matched_expected / float(len(expected_facts))
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        exact_match = (
            1.0
            if matched_expected == len(expected_facts)
            and len(extracted_facts) == len(expected_facts)
            else 0.0
        )

        total_exp = float(len(expected_facts))
        return FactExtractionEvalMetrics(
            exact_match=exact_match,
            precision=min(1.0, precision),
            recall=min(1.0, recall),
            f1=min(1.0, f1),
            value_accuracy=min(1.0, value_matches / total_exp),
            scale_accuracy=min(1.0, scale_matches / total_exp),
            period_accuracy=min(1.0, period_matches / total_exp),
        )

    def evaluate_numerical_reasoning(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> NumericalReasoningEvalMetrics:
        """Compute calculation accuracy, formula correctness, and zero-division handling."""
        expected_calcs = case.expected_calculations
        if not expected_calcs:
            return NumericalReasoningEvalMetrics(
                calculation_accuracy=1.0,
                formula_accuracy=1.0,
                rounding_accuracy=1.0,
                zero_division_safety=1.0,
                unit_consistency=1.0,
            )

        actual_calcs = answer_package.calculations
        if not actual_calcs:
            return NumericalReasoningEvalMetrics(
                calculation_accuracy=0.0,
                formula_accuracy=0.0,
                rounding_accuracy=0.0,
                zero_division_safety=1.0,
                unit_consistency=1.0,
            )

        calc_matches = 0
        formula_matches = 0
        rounding_matches = 0

        for exp in expected_calcs:
            for act in actual_calcs:
                if act.operation == exp.operation:
                    try:
                        exp_num = _parse_financial_number(exp.expected_result_str)
                        act_num = float(act.rounded_result)
                        if (
                            abs(act_num - exp_num) <= (abs(exp_num) * exp.tolerance_pct)
                            or abs(act_num - exp_num) <= 0.05
                        ):
                            calc_matches += 1
                            rounding_matches += 1
                    except Exception:
                        clean_exp = (
                            exp.expected_result_str.replace("%", "")
                            .replace("$", "")
                            .replace(",", "")
                            .strip()
                        )
                        if clean_exp in act.display_result or clean_exp in str(act.rounded_result):
                            calc_matches += 1
                            rounding_matches += 1

                    # Check formula
                    if exp.expected_formula:
                        if exp.expected_formula in act.formula:
                            formula_matches += 1
                    else:
                        formula_matches += 1
                    break

        total_exp = float(len(expected_calcs))
        return NumericalReasoningEvalMetrics(
            calculation_accuracy=min(1.0, calc_matches / total_exp),
            formula_accuracy=min(1.0, formula_matches / total_exp),
            rounding_accuracy=min(1.0, rounding_matches / total_exp),
            zero_division_safety=1.0,
            unit_consistency=1.0,
        )

    def classify_numerical_error(
        self, expected_calc: Any, actual_calc: CalculationResult | None
    ) -> NumericalErrorType:
        """Classify numerical reasoning failure into standard error taxonomy."""
        if actual_calc is None or not actual_calc.success:
            return NumericalErrorType.MISSING_VALUE

        try:
            exp_num = _parse_financial_number(expected_calc.expected_result_str)
            act_num = float(actual_calc.rounded_result)

            # Check wrong sign
            if (exp_num > 0 > act_num) or (exp_num < 0 < act_num):
                return NumericalErrorType.WRONG_SIGN

            # Check scale error (10x, 100x, 1000x difference)
            if exp_num != 0.0 and act_num != 0.0:
                ratio = act_num / exp_num
                if (
                    abs(ratio - 1000.0) < 0.1
                    or abs(ratio - 0.001) < 1e-5
                    or abs(ratio - 100.0) < 0.1
                ):
                    return NumericalErrorType.WRONG_SCALE

            # Check formula mismatch
            if (
                expected_calc.expected_formula
                and expected_calc.expected_formula not in actual_calc.formula
            ):
                return NumericalErrorType.WRONG_FORMULA

            if (
                abs(act_num - exp_num) > (abs(exp_num) * expected_calc.tolerance_pct)
                and abs(act_num - exp_num) > 0.05
            ):
                return NumericalErrorType.WRONG_RESULT

        except Exception:
            return NumericalErrorType.UNSUPPORTED_CALCULATION

        return NumericalErrorType.NONE
