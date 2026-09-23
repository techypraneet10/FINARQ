# 19. Structured Fact Representation and Fiscal Period Normalization

Date: 2026-08-22

## Status

Accepted

## Context

Financial filings (10-K, 10-Q, 8-K) express numbers across diverse reporting scales ("in millions", "in thousands", "billions"), accounting conventions (parenthetical negative representations `(1,234)`), and temporal descriptors ("Three Months Ended September 30, 2024", "FY2024", "Q3 2023", "TTM"). A deterministic reasoning engine requires uniform structured facts with explicit provenance before executing comparisons and aggregations.

## Decision

We define domain entities for structured financial values, fiscal periods, and financial facts:
1. **FinancialValue**: Encapsulates raw text, human-readable display value, unscaled Decimal, fully scaled Decimal (applying thousand/million/billion/trillion multipliers), currency code, and negative/percentage flags.
2. **FiscalPeriod**: Standardizes temporal intervals into normalized fiscal years, period types (`FY`, `Q1`, `Q2`, `Q3`, `Q4`, `TTM`), date bounds, and human-readable standardized labels (e.g., `FY2024`, `Q3 2024`).
3. **FinancialFact**: Binds a metric name, `FinancialValue`, and `FiscalPeriod` with exact provenance metadata (`document_id`, `version_id`, `page_number`, `chunk_id`, `table_id`, `source_text`, `bounding_box`).
4. **Table Priority Hierarchy**: Facts extracted from structured financial tables receive authoritative precedence over narrative mentions, with conflict resolution logging when discrepancies exceed 0.1%.

## Consequences

- **Pros**: Clean semantic separation between presentation strings and mathematical values; robust multi-period and cross-document comparison capabilities.
- **Cons**: Table headers and section contexts must be parsed to propagate scale and currency factors to individual cells.
