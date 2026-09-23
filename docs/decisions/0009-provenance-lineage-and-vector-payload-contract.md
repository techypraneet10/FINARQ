# 9. Provenance Lineage and Vector Payload Contract

Date: 2026-08-21

## Status

Accepted

## Context

In financial and regulatory contexts, citations must be verifiable down to the exact source document, version, page, and visual bounding box coordinates. A vector match that cannot trace back to its origin is inadmissible for audit and compliance.

## Decision

We enforce a strict structural lineage invariant:
`Document -> Version -> Page -> Block -> Table/Section -> Chunk -> Vector Embedding`

1. **Payload Schema Contract**:
   Every vector point indexed into Qdrant includes an exhaustive payload:
   ```json
   {
     "document_id": "doc_uuid",
     "document_version_id": "ver_uuid",
     "page_id": "page_uuid",
     "page_number": 12,
     "chunk_id": "chunk_uuid",
     "chunk_type": "text | table | header | footnote",
     "chunk_index": 4,
     "section_path": "Part II > Item 8 > Consolidated Balance Sheets",
     "block_ids": ["b1", "b2"],
     "table_id": "tbl_uuid",
     "bounding_boxes": [
       {"x0": 50.0, "y0": 180.0, "x1": 560.0, "y1": 300.0, "page_number": 12}
     ],
     "content_hash": "sha256_hex",
     "token_count": 245,
     "document_type": "10-K",
     "ticker_symbol": "AAPL",
     "fiscal_year": 2023,
     "fiscal_period": "FY",
     "text": "Full chunk text..."
   }
   ```
2. **Payload Indexing**:
   - `document_id` (keyword index)
   - `document_version_id` (keyword index)
   - `page_number` (integer index)
   - `chunk_type` (keyword index)
   - `ticker_symbol` (keyword index)
   - `fiscal_year` (integer index)
   - `document_type` (keyword index)
3. **Point ID Determinism & Consistency**:
   - Vector point IDs use standard UUIDv4 strings identical to `DocumentChunk.id` to allow 1-to-1 correlation between relational persistence and vector storage.

## Consequences

### Positive
- Every search result immediately yields the complete lineage path back to the relational database and raw PDF page.
- Enables filtered vector search by ticker, fiscal year, filing type, or document version.
- Allows atomic vector deletion by `document_id`.

### Negative / Trade-offs
- Larger Qdrant payload footprint per point.
