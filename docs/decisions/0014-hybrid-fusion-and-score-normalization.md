# ADR 0014: Hybrid Candidate Fusion via Reciprocal Rank Fusion (RRF)

## Status
Accepted

## Context
Combining dense vector search scores (cosine similarity in $[0, 1]$) with sparse lexical BM25 scores (unbounded positive floats) presents calibration challenges. Linear combinations $\alpha \cdot S_{\text{dense}} + (1 - \alpha) \cdot S_{\text{sparse}}$ suffer from distribution skew, where BM25 scores vary wildly depending on corpus size, query term frequency, and document length.

## Decision
1. **Reciprocal Rank Fusion (RRF)**: Adopted Cormack et al.'s Reciprocal Rank Fusion algorithm:
   $$RRF(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{w_m}{k + \text{rank}_m(d)}$$
   with default constant $k = 60$ and equal stream weights $w_m = 1.0$.
2. **Provenance & Source Tracking**: Candidate chunks retain their individual dense score, dense rank, sparse score, sparse rank, and an explicit source flag (`DENSE`, `SPARSE`, or `BOTH`).
3. **Score Normalization**: Normalized final fusion scores to $[0.0, 1.0]$ relative to the maximum reciprocal rank achieved in the pool, ensuring clean downstream comparability.

## Consequences
- **Positive**: Immune to score magnitude imbalances; guarantees candidates retrieved by both modalities receive a significant rank promotion; robust across diverse query types without fine-tuning per-query score multipliers.
- **Negative**: Relies solely on relative ordering rather than absolute confidence deltas between adjacent ranked positions.
