# 20. Verifiable Citation Mapping and Grounding Validation

Date: 2026-08-22

## Status

Accepted

## Context

Financial compliance, regulatory auditability, and institutional trust mandate that every claim, statement, and arithmetic calculation produced by the platform must be directly verifiable against the underlying source documents. Ungrounded claims or fabricated citations violate platform integrity.

## Decision

We implement a two-step deterministic claim-to-citation construction and audit pipeline:
1. **Atomic Claims**: Claims are categorized into `direct_fact` (verbatim extraction) and `calculated` (derived through arithmetic), each holding explicit references to supporting `fact_ids` and `calculation_ids`.
2. **Deterministic Citation Generation**: Citations inherit exact provenance parameters (`document_id`, `version_id`, `page_number`, `chunk_id`, `table_id`, `source_excerpt`, `bounding_box`) from the underlying `FinancialFact` entities.
3. **Citation Verification**: The `CitationValidator` confirms that every citation maps to a genuine chunk in the retrieved evidence set with matching document IDs and page numbers.
4. **Grounding Validation Graph**: The `GroundingValidator` audits that 100% of claims are connected via unbroken chains to verified citations and successful calculations. If any claim lacks a valid citation or relies on a failed calculation, the status is marked `UNGROUNDED` and flagged in the validation result.

## Consequences

- **Pros**: Complete chain-of-custody from source chunk to final output; zero phantom citations; strict compliance with financial audit standards.
- **Cons**: Requires granular chunk provenance metadata to be maintained throughout ingestion, retrieval, and reasoning pipelines.
