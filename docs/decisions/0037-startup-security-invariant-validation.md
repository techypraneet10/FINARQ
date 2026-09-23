# ADR 0037: Fail-Fast Startup Security Invariant Validation

## Status
Accepted

## Context
Deploying applications with insecure defaults (e.g. short JWT secret keys, missing encryption settings, insecure token algorithms, disabled tenant isolation in production) is a primary cause of security breaches.

## Decision
We enforce strict fail-fast startup validation through `validate_security_configuration()` called in application lifespan initialization:

1. **Production Invariants**:
   - `jwt_secret_key` must be at least 32 characters long.
   - `jwt_secret_key` must not match insecure defaults (e.g., `"dev-insecure-secret"`, `"secret"`, `"password"`).
   - `jwt_algorithm` must be in the approved cryptographic allowlist (`["HS256"]`).
   - `auth_disabled_dev` must be `False` in production environments.

2. **Lifespan Execution**:
   - Any violation raises `ConfigurationError` immediately during startup, preventing the server from listening or accepting traffic with an insecure configuration.

## Consequences
### Positive
- Prevents misconfigured instances from entering production.
- Guarantees cryptographic entropy for signing keys.
