# 3. Configuration Management Strategy

Date: 2026-08-20  
Status: Accepted

## Context
Production services require environment-based configuration that validates settings at startup, avoids hardcoding values, supports 12-factor application methodology, and prevents credential leakage in logs.

## Decision
We use `pydantic-settings` to define grouped settings classes (`AppSettings`, `DatabaseSettings`, `LoggingSettings`, `StorageSettings`, `QdrantSettings`, `LLMSettings`, `EmbeddingSettings`). Sensitive credentials use `pydantic.SecretStr` to prevent accidental emission in stringified representations or log outputs. Safe defaults are provided for local development.

## Consequences
### Positive
- Strict type validation and fail-fast startup on missing/malformed configuration.
- Transparent override capability via environment variables and `.env` files.
- Secrets are masked by default (`**********`).

### Negative / Trade-offs
- Slight initialization overhead during startup (mitigated via `@lru_cache`).
