# 8. Structure-Aware Semantic Chunking

Date: 2026-08-21

## Status

Accepted

## Context

Standard fixed-character or fixed-token chunking strategies split text arbitrarily across paragraphs, sentences, or tabular rows. In financial documents:
- Splitting a financial table across multiple chunks destroys column headers and numerical context.
- Splitting across section boundaries merges unrelated disclosures (e.g. Risk Factors into Legal Proceedings).
- Splitting sentences mid-clause damages quantitative statements (e.g. `$25.4 million` separated from `in revenue`).

## Decision

We implement `StructureAwareChunker`:
1. **Section Boundary Respect**:
   - Chunks never cross major structural section boundaries (`section_path`). When a new section begins, any accumulated chunk is finalized immediately.
2. **Dedicated Table Chunks**:
   - Financial tables are chunked as atomic units (`ChunkType.TABLE`).
   - The table chunk content includes the title, currency, scale multipliers, full markdown table, and footnotes.
   - Associated layout blocks and parent page IDs are preserved in `block_ids` and `page_id`.
3. **Paragraph & Sentence-Level Aggregation**:
   - Narrative text blocks (`ChunkType.TEXT`, `ChunkType.HEADING`) are aggregated respecting token budgets (default 512 tokens with 50-token overlap).
   - Chunks maintain paragraph integrity, falling back to sentence tokenization before splitting across token boundaries.
4. **Header Context Injection**:
   - Section breadcrumbs and table titles are prepended as contextual headers in the chunk text representation.

## Consequences

### Positive
- High retrieval precision by maintaining self-contained semantic units.
- Complete tabular context preserved for downstream synthesis and tabular reasoning.
- Exact block and page references retained on every chunk.

### Negative / Trade-offs
- Very large tables exceeding single chunk budgets must be serialized with repeating headers on subsequent chunks.
