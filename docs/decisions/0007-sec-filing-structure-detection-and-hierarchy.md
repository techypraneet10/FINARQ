# 7. SEC Filing Structure Detection and Hierarchy

Date: 2026-08-21

## Status

Accepted

## Context

SEC filings (Form 10-K, Form 10-Q, 8-K) and corporate annual reports are organized in standardized legal and financial hierarchies:
- `Part I`: Item 1 (Business), Item 1A (Risk Factors), Item 1B (Unresolved Staff Comments).
- `Part II`: Item 7 (MD&A), Item 7A (Quantitative Disclosures About Market Risk), Item 8 (Financial Statements and Supplementary Data), Item 9A (Controls and Procedures).
- Core Financial Statements: Consolidated Balance Sheets, Consolidated Statements of Operations, Consolidated Statements of Cash Flows.

Without contextual section tagging, text chunks lose their legal and operational context (e.g. risk factor disclosures versus management commentary versus audited footnotes).

## Decision

We implement `FinancialStructureDetector`:
1. **Hierarchical State Tracking**:
   - Maintains continuous state machine across pages tracking `current_part`, `current_item`, and `current_statement`.
2. **Regex Pattern Matching**:
   - Identifies SEC Part patterns (`PART I`, `PART II`, `PART III`, `PART IV`).
   - Identifies SEC Item patterns (`ITEM 1. BUSINESS`, `ITEM 1A. RISK FACTORS`, `ITEM 7. MANAGEMENT'S DISCUSSION...`, `ITEM 8. FINANCIAL STATEMENTS...`).
   - Identifies financial statement titles (`CONSOLIDATED BALANCE SHEETS`, `STATEMENTS OF OPERATIONS`, `STATEMENTS OF CASH FLOWS`, `STATEMENTS OF COMPREHENSIVE INCOME`).
3. **Lineage Tagging**:
   - Tags every `LayoutBlock` and `FinancialTable` with a canonical breadcrumb `section_path` (e.g. `Part I > Item 1A. Risk Factors` or `Part II > Item 8. Financial Statements > Consolidated Balance Sheets`).
   - Upgrades font-matching heading candidates to `BlockType.HEADING`.

## Consequences

### Positive
- Chunks inherit rich structural breadcrumbs in metadata and vector payloads.
- Enables filtered search in Phase 2 (e.g., restricting retrieval to `Item 1A` for risk audits or `Item 8` for financial metrics).
- Resolves cross-page section continuity.

### Negative / Trade-offs
- Heuristics depend on standard SEC heading naming conventions. Unconventional corporate formatting may require broader fallback matchers.
