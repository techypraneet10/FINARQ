# 6. Financial Table Normalization and Parenthetical Negatives

Date: 2026-08-21

## Status

Accepted

## Context

Financial statements (Balance Sheets, Statements of Operations, Cash Flow Statements) employ distinct accounting formatting conventions that break standard NLP parsers and generic tabular tokenizers:
1. **Parenthetical Negative Numbers**: Financial losses and cash outflows are conventionally denoted with parentheses, e.g. `(1,234.50)`, `$(850)`, or `(2.1%)` rather than leading minus signs `-1234.50`. Generic tokenizers treat parentheses as sentence punctuation or token separators, destroying semantic polarity.
2. **Implicit Multipliers and Scales**: Statements frequently state scale factors in titles or headers, e.g., `(In thousands)`, `(In millions, except per share data)`.
3. **Currency Symbols and Zero Dash Notations**: Currencies (`$`, `€`, `£`, `¥`) and zero dashes (`—`, `-`, `None`) must be parsed into clean numeric floating-point values while preserving the formatted presentation for LLM readability.

## Decision

We implement a dedicated `FinancialTableNormalizer` and `FinancialTableExtractor`:
1. **Parenthetical Negative Conversion**:
   - Compiles regex patterns `PARENTHETICAL_NEGATIVE_PATTERN` matching `$(1,234.56)`, `(1,234.50)`, and `(2.1%)`.
   - Normalizes parsed numeric values into strict negative floats (e.g. `-1234.50`, `-2.1`) while recording cell coordinates `(row_index, col_index)`.
2. **Currency and Scale Multiplier Detection**:
   - Detects currency symbols and scale descriptors (`thousands` -> `1,000`, `millions` -> `1,000,000`, `billions` -> `1,000,000,000`).
   - Stores `scale` multiplier on `FinancialTable` metadata.
3. **Dual Representation (Structured Cell Grid & Markdown)**:
   - Maintains an addressable `TableCell` grid with `row_index`, `col_index`, `is_header`, `numeric_value`, and raw text.
   - Generates standardized GitHub-flavored markdown representations for prompt injection and vector indexing.

## Consequences

### Positive
- Prevents catastrophic polarity inversion where accounting losses are misinterpreted as positive revenues.
- Enables precise numeric lookups in downstream reasoning modules (Phase 3).
- Clean markdown rendering preserves column alignment for dense financial tables.

### Negative / Trade-offs
- Heavily irregular, non-standard footnotes or merged multi-level spanning headers require specialized structural heuristics.
