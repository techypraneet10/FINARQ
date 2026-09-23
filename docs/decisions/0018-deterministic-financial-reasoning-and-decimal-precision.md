# 18. Deterministic Financial Reasoning and Decimal Precision Arithmetic

Date: 2026-08-22

## Status

Accepted

## Context

Financial document intelligence systems cannot rely on Large Language Models (LLMs) as numerical calculators. LLMs frequently hallucinate arithmetic calculations, suffer from floating-point roundoff errors, fail on multi-period growth rates, and miscalculate financial ratios. Furthermore, floating-point representations (`float` / IEEE 754) introduce precision artifacts (e.g., `0.1 + 0.2 != 0.3`) that are unacceptable in quantitative SEC analysis and audited financial environments.

Dynamic script execution (`eval()`, `exec()`, or runtime code generation) introduces severe Remote Code Execution (RCE) security risks and unpredictable execution failures.

## Decision

We establish an explicit, deterministic reasoning engine strictly isolated from LLM generation:
1. **Python Decimal Arithmetic**: All financial calculations are executed using `decimal.Decimal` with fixed-precision rounding (`ROUND_HALF_UP`) and explicit scale multipliers.
2. **Zero-Division and Edge Case Protection**: Mathematical edge cases (division by zero, negative baselines, nil / em-dash values) are captured safely without exceptions, NaN, or infinity, returning explicit failure statuses with descriptive reasoning notes.
3. **No Unsafe Execution**: Calculation formulas are constructed via explicit domain operations (`DIRECT_LOOKUP`, `DIFFERENCE`, `PERCENTAGE_CHANGE`, `GROWTH_RATE`, `RATIO`, `SUM`, `AVERAGE`, `MIN`, `MAX`, `TREND`, `MULTI_PERIOD_COMPARISON`) without any `eval()` or `exec()`.
4. **Unit and Currency Incompatibility Guards**: Calculations enforce compatibility across units (preventing currency and percentage additions) and currencies (rejecting unadjusted USD / EUR arithmetic).

## Consequences

- **Pros**: Exact mathematical reproducibility, elimination of LLM hallucination in calculations, elimination of floating-point drift, complete auditability.
- **Cons**: Requires explicit parser and normalizer rules to map diverse reporting strings into standardized `FinancialValue` and `FiscalPeriod` domain entities.
