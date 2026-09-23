# ADR 0013: Sparse Retrieval Engine and Domain Tokenization

## Status
Accepted

## Context
In financial document question answering, dense semantic embeddings excel at capturing conceptual similarity (e.g., "profitability trajectory" vs. "operating margin expansion") but frequently underperform on exact alphanumeric tokens such as:
- SEC Item identifiers (`Item 1A`, `Item 7`, `Item 8`)
- Specific fiscal years and quarters (`FY24`, `Q3 2024`)
- Exact numeric disclosures and decimal amounts (`$391,035 million`)
- Ticker symbols (`AAPL`, `NVDA`, `MSFT`)

We needed a high-performance, deterministic sparse lexical retrieval component that integrates cleanly into our Hexagonal architecture without introducing external infrastructure complexity (e.g. running separate Elasticsearch clusters for local developer environments).

## Decision
1. **Okapi BM25 In-Memory Retrieval**: Implemented a pure-Python, zero-dependency Okapi BM25 inverted index engine using standard parameters ($k_1=1.5, b=0.75$).
2. **Domain-Specific Tokenization**: Created `tokenize_financial_text` which preserves critical financial tokens:
   - Normalizes SEC sections (e.g., `item 1a` $\rightarrow$ `item_1a`).
   - Normalizes fiscal quarters (e.g., `4Q` $\rightarrow$ `q4`).
   - Preserves alphanumeric tokens, decimal amounts, and monetary units while stripping non-informative English stopwords.
3. **Exact Match Boosting**: Boosts candidate documents by a factor of 2.0x when exact extracted financial entities (tickers, fiscal years, SEC section paths) appear in query signals.
4. **Metadata Filtering**: Supports document ID, version ID, ticker, fiscal year, and table-only predicate filtering directly within the sparse candidate pipeline.

## Consequences
- **Positive**: Zero operational overhead; high precision on numerical and structural lookups; deterministic execution in test environments; instant indexing during document ingestion pipeline.
- **Negative**: Inverted index is stored in memory; future enterprise scale will require persistent sparse storage or distributed inverted indexes if index sizes exceed single-node memory constraints.
