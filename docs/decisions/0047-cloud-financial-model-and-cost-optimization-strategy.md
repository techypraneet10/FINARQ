# ADR 0047: Cloud Financial Model and Cost Optimization Strategy

## Status
Accepted

## Context
Deploying financial RAG infrastructure without granular cost modeling risks uncontrolled AWS hosting and LLM token expenditures as user and document volume scales.

## Decision
We implement a comprehensive cloud financial and cost-control framework:
1. **Tiered Compute Sizing**:
   - Development: Single-AZ `t4g` instances (~$85/month).
   - Staging: Multi-AZ `r6g.large` (~$450/month).
   - Production: High-Availability Multi-AZ `r6g.xlarge` with autoscaling (~$1,250/month).
2. **Storage Tiering Automation**:
   - S3 Intelligent-Tiering after 30 days for active filings.
   - S3 Glacier Instant Retrieval for non-current document versions after 90 days.
3. **LLM Cost Optimization**:
   - Semantic answer caching in Redis reduces redundant LLM calls by 25-40%.
   - Strict token budgeting and context pruning in `ContextBuilder`.
   - Small embedding models (`text-embedding-3-small` / 1536d) providing optimal price-to-performance for dense retrieval.
4. **Tagging & Allocation**: All cloud resources are tagged with `Environment`, `Project`, and `CostCenter` for automated AWS Cost Explorer reporting.

## Consequences
### Positive
- Predictable per-tenant and per-query operational costs.
- Reduced cold storage and token costs over time.
