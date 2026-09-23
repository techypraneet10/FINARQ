# Architectural Boundaries & Dependency Rules

This document specifies the strict boundary rules across the codebase layers.

## Layer Dependency Flow

```
[ API Layer ] ---> [ Application Layer ] ---> [ Domain Layer ] <--- [ Infrastructure Layer ]
```

### 1. Domain Layer (`src/financial_rag/domain/`)
- **Allowed Imports**: Standard library (`typing`, `dataclasses`, `datetime`, `uuid`, `enum`), `financial_rag.common`.
- **Forbidden Imports**: `fastapi`, `starlette`, `pydantic_settings`, `sqlalchemy`, `qdrant_client`, `redis`, `openai`, `anthropic`, `google.genai`, `boto3`.
- **Responsibility**: Pure domain entities, business invariants, custom exception definitions, and abstract protocol contracts (`Protocol`).

### 2. Application Layer (`src/financial_rag/application/`)
- **Allowed Imports**: Standard library, `financial_rag.domain`, `financial_rag.common`.
- **Forbidden Imports**: Concrete infrastructure libraries, web frameworks (`fastapi`).
- **Responsibility**: High-level workflow contracts and use case orchestration.

### 3. Infrastructure Layer (`src/financial_rag/infrastructure/`)
- **Allowed Imports**: Standard library, `financial_rag.domain`, `financial_rag.config`, `financial_rag.common`, third-party database / AI SDKs.
- **Responsibility**: Concrete implementations of domain protocols (e.g. S3 Object Storage adapter, Qdrant vector adapter, logging formatters, database clients).

### 4. API Layer (`src/financial_rag/api/`)
- **Allowed Imports**: `fastapi`, `starlette`, `pydantic`, `financial_rag.domain`, `financial_rag.config`, `financial_rag.infrastructure`, `financial_rag.common`.
- **Responsibility**: HTTP routing, request parsing, response formatting, middleware execution, dependency injection, and exception translation to HTTP status codes.
