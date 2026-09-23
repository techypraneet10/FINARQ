"""Deterministic financial arithmetic engine operating on Decimal quantities with zero-division protection."""

from decimal import ROUND_HALF_UP, Decimal, DivisionByZero, InvalidOperation
from uuid import uuid4

from financial_rag.domain.entities.reasoning import (
    CalculationInput,
    CalculationResult,
    FinancialFact,
    ReasoningOperation,
)
from financial_rag.domain.exceptions import (
    IncompatibleCompanyError,
    IncompatibleCurrencyError,
    IncompatibleUnitsError,
)
from financial_rag.domain.interfaces.reasoning import FinancialCalculatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.calculator")


class DeterministicFinancialCalculator(FinancialCalculatorProtocol):
    """Executes verified financial formulas using high-precision Decimal arithmetic."""

    def _validate_currency_and_units(
        self,
        facts: list[FinancialFact],
        operation: ReasoningOperation,
    ) -> tuple[str | None, str]:
        """Validate that all input facts share compatible currency and unit descriptors."""
        if not facts:
            return None, ""

        first_fact = facts[0]
        base_currency = first_fact.value.currency
        base_is_pct = first_fact.value.is_percentage
        base_unit = first_fact.value.unit

        for fact in facts[1:]:
            # Check percentage vs absolute currency compatibility for additive/comparative ops
            if operation in (
                ReasoningOperation.DIFFERENCE,
                ReasoningOperation.SUM,
                ReasoningOperation.AVERAGE,
                ReasoningOperation.MIN,
                ReasoningOperation.MAX,
            ):
                if fact.value.is_percentage != base_is_pct:
                    raise IncompatibleUnitsError(
                        unit_a="percentage" if base_is_pct else base_unit,
                        unit_b="percentage" if fact.value.is_percentage else fact.value.unit,
                        operation=operation.value,
                    )
                if not base_is_pct and fact.value.currency != base_currency:
                    raise IncompatibleCurrencyError(
                        currency_a=str(base_currency),
                        currency_b=str(fact.value.currency),
                        operation=operation.value,
                    )

        return base_currency, base_unit

    def _validate_company_compatibility(
        self,
        facts: list[FinancialFact],
        operation: ReasoningOperation,
        company_override: str | None = None,
    ) -> None:
        """Ensure facts belong to the same company entity unless explicit cross-company comparison is enabled."""
        if company_override or len(facts) <= 1:
            return

        first_ticker = (facts[0].ticker or facts[0].company or "").strip().upper()
        if not first_ticker:
            return

        for fact in facts[1:]:
            other_ticker = (fact.ticker or fact.company or "").strip().upper()
            if other_ticker and other_ticker != first_ticker:
                raise IncompatibleCompanyError(
                    company_a=first_ticker,
                    company_b=other_ticker,
                    operation=operation.value,
                )

    def _build_inputs(self, facts: list[FinancialFact]) -> list[CalculationInput]:
        """Convert domain FinancialFact items into CalculationInput operands."""
        inputs = []
        for _i, fact in enumerate(facts):
            name = f"{fact.metric} ({fact.period.label})"
            inputs.append(
                CalculationInput(
                    name=name,
                    value=fact.value.numeric_value,
                    fact_id=fact.fact_id,
                    source_description=f"{fact.metric} for {fact.period.label} ({fact.company or 'Entity'})",
                    unit=fact.value.unit,
                    currency=fact.value.currency,
                )
            )
        return inputs

    def execute(
        self,
        operation: ReasoningOperation,
        facts: list[FinancialFact],
        company_override: str | None = None,
    ) -> CalculationResult:
        """Execute deterministic arithmetic over input facts and return audited CalculationResult."""
        calc_id = str(uuid4())
        logger.info(
            f"Executing deterministic calculation '{operation.value}' across {len(facts)} facts"
        )

        if not facts:
            return CalculationResult(
                calculation_id=calc_id,
                operation=operation,
                formula="N/A",
                inputs=[],
                input_fact_ids=[],
                raw_result=Decimal("0"),
                rounded_result=Decimal("0"),
                display_result="N/A",
                unit="",
                currency=None,
                success=False,
                error_message="No input facts provided for calculation.",
            )

        # Validate company, currency, and unit invariants
        try:
            self._validate_company_compatibility(facts, operation, company_override)
            base_currency, base_unit = self._validate_currency_and_units(facts, operation)
        except (IncompatibleUnitsError, IncompatibleCurrencyError, IncompatibleCompanyError) as e:
            return CalculationResult(
                calculation_id=calc_id,
                operation=operation,
                formula=operation.value,
                inputs=self._build_inputs(facts),
                input_fact_ids=[f.fact_id for f in facts],
                raw_result=Decimal("0"),
                rounded_result=Decimal("0"),
                display_result="Calculation Incompatibility",
                unit="",
                currency=None,
                success=False,
                error_message=e.message,
            )

        inputs = self._build_inputs(facts)
        input_ids = [f.fact_id for f in facts]

        try:
            if operation == ReasoningOperation.DIRECT_LOOKUP:
                fact = facts[0]
                val = fact.value.numeric_value
                display = fact.value.display_value
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=f"{fact.metric} = {val}",
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=val,
                    rounded_result=val,
                    display_result=display,
                    unit=fact.value.unit,
                    currency=fact.value.currency,
                    success=True,
                )

            elif operation == ReasoningOperation.DIFFERENCE:
                if len(facts) < 2:
                    return self._insufficient_operands_result(
                        calc_id, operation, inputs, input_ids, 2
                    )
                val_a = facts[0].value.numeric_value
                val_b = facts[1].value.numeric_value
                diff = val_a - val_b
                formula = f"{inputs[0].name} - {inputs[1].name}"
                rounded = diff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                display = self._format_monetary(diff, base_currency)
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=diff,
                    rounded_result=rounded,
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            elif operation in (
                ReasoningOperation.PERCENTAGE_CHANGE,
                ReasoningOperation.GROWTH_RATE,
            ):
                if len(facts) < 2:
                    return self._insufficient_operands_result(
                        calc_id, operation, inputs, input_ids, 2
                    )
                # Sort chronologically if fiscal years are present
                sorted_facts = sorted(
                    facts, key=lambda f: (f.period.fiscal_year or 0, f.period.period_type)
                )
                old_fact = sorted_facts[0]
                new_fact = sorted_facts[1]
                old_val = old_fact.value.numeric_value
                new_val = new_fact.value.numeric_value
                old_name = f"{old_fact.metric} ({old_fact.period.label})"
                new_name = f"{new_fact.metric} ({new_fact.period.label})"

                if old_val == Decimal("0"):
                    return CalculationResult(
                        calculation_id=calc_id,
                        operation=operation,
                        formula=f"(({new_name} - {old_name}) / {old_name}) * 100",
                        inputs=inputs,
                        input_fact_ids=input_ids,
                        raw_result=Decimal("0"),
                        rounded_result=Decimal("0"),
                        display_result="Division by Zero (Base is 0)",
                        unit="%",
                        currency=None,
                        success=False,
                        error_message="Division by zero: denominator (base period value) is zero.",
                    )
                pct_change = ((new_val - old_val) / abs(old_val)) * Decimal("100")
                rounded = pct_change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                prefix = "+" if rounded > 0 else ""
                display = f"{prefix}{rounded:.2f}%"
                formula = f"(({new_name} - {old_name}) / |{old_name}|) * 100"
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=pct_change,
                    rounded_result=rounded,
                    display_result=display,
                    unit="%",
                    currency=None,
                    success=True,
                )

            elif operation == ReasoningOperation.RATIO:
                if len(facts) < 2:
                    return self._insufficient_operands_result(
                        calc_id, operation, inputs, input_ids, 2
                    )
                num = facts[0].value.numeric_value
                den = facts[1].value.numeric_value
                if den == Decimal("0"):
                    return CalculationResult(
                        calculation_id=calc_id,
                        operation=operation,
                        formula=f"{inputs[0].name} / {inputs[1].name}",
                        inputs=inputs,
                        input_fact_ids=input_ids,
                        raw_result=Decimal("0"),
                        rounded_result=Decimal("0"),
                        display_result="Division by Zero (Denominator is 0)",
                        unit="ratio",
                        currency=None,
                        success=False,
                        error_message="Division by zero: denominator is zero.",
                    )

                ratio = num / den
                rounded = ratio.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                display = f"{rounded:.4f}"
                formula = f"{inputs[0].name} / {inputs[1].name}"
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=ratio,
                    rounded_result=rounded,
                    display_result=display,
                    unit="ratio",
                    currency=None,
                    success=True,
                )

            elif operation == ReasoningOperation.SUM:
                total = sum((f.value.numeric_value for f in facts), Decimal("0"))
                formula = " + ".join(inp.name for inp in inputs)
                rounded = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                display = self._format_monetary(total, base_currency)
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=total,
                    rounded_result=rounded,
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            elif operation == ReasoningOperation.AVERAGE:
                count = Decimal(len(facts))
                total = sum((f.value.numeric_value for f in facts), Decimal("0"))
                avg = total / count

                formula = f"({' + '.join(inp.name for inp in inputs)}) / {len(facts)}"
                rounded = avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                display = self._format_monetary(avg, base_currency)
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=avg,
                    rounded_result=rounded,
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            elif operation == ReasoningOperation.MIN:
                min_fact = min(facts, key=lambda f: f.value.numeric_value)
                val = min_fact.value.numeric_value
                rounded = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                display = self._format_monetary(val, base_currency)
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=f"min({', '.join(inp.name for inp in inputs)})",
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=val,
                    rounded_result=rounded,
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            elif operation == ReasoningOperation.MAX:
                max_fact = max(facts, key=lambda f: f.value.numeric_value)
                val = max_fact.value.numeric_value
                rounded = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                display = self._format_monetary(val, base_currency)
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=f"max({', '.join(inp.name for inp in inputs)})",
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=val,
                    rounded_result=rounded,
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            elif operation in (
                ReasoningOperation.TREND,
                ReasoningOperation.MULTI_PERIOD_COMPARISON,
                ReasoningOperation.COMPARISON,
            ):
                # Sort facts chronologically if fiscal years available
                sorted_facts = sorted(
                    facts, key=lambda f: (f.period.fiscal_year or 0, f.period.period_type)
                )
                first_val = sorted_facts[0].value.numeric_value
                last_val = sorted_facts[-1].value.numeric_value
                total_delta = last_val - first_val
                if first_val != Decimal("0"):
                    total_growth = ((last_val - first_val) / abs(first_val)) * Decimal("100")
                    rounded_growth = total_growth.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    growth_str = f" ({'+' if rounded_growth > 0 else ''}{rounded_growth:.2f}%)"
                else:
                    growth_str = ""

                direction = (
                    "increased"
                    if total_delta > 0
                    else ("decreased" if total_delta < 0 else "remained flat")
                )
                display = f"{direction} by {self._format_monetary(abs(total_delta), base_currency)}{growth_str}"
                formula = (
                    f"trend from {sorted_facts[0].period.label} to {sorted_facts[-1].period.label}"
                )
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=formula,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=total_delta,
                    rounded_result=total_delta.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    display_result=display,
                    unit=base_unit,
                    currency=base_currency,
                    success=True,
                )

            else:
                return CalculationResult(
                    calculation_id=calc_id,
                    operation=operation,
                    formula=operation.value,
                    inputs=inputs,
                    input_fact_ids=input_ids,
                    raw_result=Decimal("0"),
                    rounded_result=Decimal("0"),
                    display_result="Unsupported Operation",
                    unit="",
                    currency=None,
                    success=False,
                    error_message=f"Unsupported reasoning operation '{operation.value}'",
                )

        except (DivisionByZero, InvalidOperation) as e:
            return CalculationResult(
                calculation_id=calc_id,
                operation=operation,
                formula=operation.value,
                inputs=inputs,
                input_fact_ids=input_ids,
                raw_result=Decimal("0"),
                rounded_result=Decimal("0"),
                display_result="Calculation Error",
                unit="",
                currency=None,
                success=False,
                error_message=f"Mathematical calculation error: {e}",
            )

    def _insufficient_operands_result(
        self,
        calc_id: str,
        operation: ReasoningOperation,
        inputs: list[CalculationInput],
        input_ids: list[str],
        required_count: int,
    ) -> CalculationResult:
        """Helper generating result for insufficient operands."""
        return CalculationResult(
            calculation_id=calc_id,
            operation=operation,
            formula=operation.value,
            inputs=inputs,
            input_fact_ids=input_ids,
            raw_result=Decimal("0"),
            rounded_result=Decimal("0"),
            display_result=f"Requires at least {required_count} facts",
            unit="",
            currency=None,
            success=False,
            error_message=f"Operation '{operation.value}' requires at least {required_count} facts, got {len(inputs)}.",
        )

    def _format_monetary(self, val: Decimal, currency: str | None) -> str:
        """Format Decimal into human-readable monetary or unit representation."""
        abs_val = abs(val)
        curr_prefix = "$" if currency == "USD" else (f"{currency} " if currency else "")
        sign = "-" if val < 0 else ""
        if abs_val >= Decimal("1000000000000"):
            scaled = abs_val / Decimal("1000000000000")
            return f"{sign}{curr_prefix}{scaled:,.2f} trillion"
        if abs_val >= Decimal("1000000000"):
            scaled = abs_val / Decimal("1000000000")
            return f"{sign}{curr_prefix}{scaled:,.2f} billion"
        if abs_val >= Decimal("1000000"):
            scaled = abs_val / Decimal("1000000")
            return f"{sign}{curr_prefix}{scaled:,.2f} million"
        return f"{sign}{curr_prefix}{abs_val:,.2f}"
