# 2. Layered Clean Architecture

Date: 2026-08-20  
Status: Accepted

## Context
The platform requires long-term maintainability, high testability, and the ability to replace third-party dependencies (such as vector databases, embedding models, and LLM providers) without modifying core business rules and calculation logic.

## Decision
We adopt Clean / Hexagonal Architecture with four distinct conceptual layers:
1. **Domain Layer**: Contains pure business entities, invariants, and abstract Protocol interfaces. Zero external framework dependencies.
2. **Application Layer**: Contains use case workflows and orchestration contracts.
3. **Infrastructure Layer**: Contains concrete adapters for external systems (Qdrant, PostgreSQL, S3, Redis, OpenAI/Anthropic/Gemini).
4. **API Layer**: Handles FastAPI routing, request validation, serialization, and middleware.

## Consequences
### Positive
- Strict dependency inversion: Business rules do not leak into database or API handlers.
- Infrastructure and AI providers can be swapped or upgraded with zero impact on domain models.
- 100% of domain and application logic is testable offline without live external services.

### Negative / Trade-offs
- Requires mapping between domain models and API schemas / database entities.
