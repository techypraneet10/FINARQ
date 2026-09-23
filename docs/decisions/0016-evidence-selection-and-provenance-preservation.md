# ADR 0016: Evidence Selection and Provenance Preservation Contract

## Status
Accepted

## Context
Standard RAG architectures simply take the top $K$ scoring vectors. In financial disclosures, this approach leads to several failure modes:
- **Redundancy**: Multiple chunks from the same repetitive disclosures in a single 10-K crowd out relevant disclosures from other documents or fiscal years.
- **Table Discarding**: Relevant tabular financial statements (Income Statement, Balance Sheet) scored slightly lower than narrative text are dropped.
- **Multi-Period Blindness**: For questions comparing 2023 and 2024, top vectors might all originate from 2024, leaving the reasoning engine without 2023 evidence.
- **Provenance Loss**: Score fusion or reranking often loses source page numbers, bounding boxes, or chunk hashes.

## Decision
1. **EvidenceSelector Implementation**: Built an evidence selection stage balancing:
   - **Table Preservation**: Guaranteed inclusion of high-quality table chunks when the query signals a table or balance sheet lookup.
   - **Multi-Period Representation**: In comparison queries spanning multiple fiscal periods (e.g., 2023 vs 2024), ensures candidate chunks from each identified fiscal period are included in the final set.
   - **Document Diversity**: Restricts maximum chunks per document (`max_chunks_per_document = 3`) to prevent single-filing crowding.
2. **Strict Provenance Contract**: Every `RankedEvidence` entity preserves 100% of chunk lineage: `chunk_id`, `document_id`, `document_version_id`, `page_number`, `page_numbers`, `source_block_ids`, `section_path`, `table_id`, `content_hash`, `dense_score`, `sparse_score`, `fusion_score`, `reranker_score`, `final_score`, and `retrieval_sources`.
3. **Quality Validation Guardrails**: `EvidenceValidator` inspects all selected evidence items to verify non-empty content, valid document identifiers, and intact provenance before dispatching to API callers.

## Consequences
- **Positive**: Complete auditability for downstream generation and regulatory inspection; balanced evidence representation across multi-period comparison queries.
- **Negative**: Adds selection heuristics that must be configured via application settings.
