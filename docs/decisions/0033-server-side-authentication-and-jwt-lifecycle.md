# ADR 0033: Server-Side Authentication & Cryptographic JWT Lifecycle

## Status
Accepted

## Context
A production financial intelligence platform must verify caller identity before authorizing any data access. Authentication must prevent credential theft, token forgery, replay attacks, and algorithm confusion vulnerabilities (`alg: none`).

## Decision
We implement a zero-external-dependency, cryptographically robust authentication and session management subsystem:

1. **Password Hashing**:
   - Primary: `hashlib.scrypt` with 32-byte cryptographically secure random salt, CPU/memory cost parameter $N=16384$, block size $r=8$, parallelization $p=1$.
   - Verification uses constant-time `hmac.compare_digest` to prevent timing side-channel attacks.

2. **JSON Web Tokens (JWT)**:
   - Tokens signed with HMAC-SHA256 (`HS256`).
   - Strict algorithm allowlist (`["HS256"]`); rejection of `alg: none` and unlisted signature schemes.
   - Access tokens are short-lived (default: 15 minutes) and encode subject (`sub`), tenant (`tid`), role (`role`), audience (`aud`), issuer (`iss`), issued-at (`iat`), and expiration (`exp`).
   - Refresh tokens are long-lived (default: 7 days), cryptographically hashed with SHA-256 before storage in PostgreSQL, and support single-use token rotation.
   - Refresh token reuse triggers immediate revocation of all active sessions for the compromised user account.

3. **Server-Side Verification**:
   - Client-provided bearer tokens are verified on every request.
   - User account and tenant organization status are confirmed active in PostgreSQL before serving requests.

## Consequences
### Positive
- Fully self-contained authentication with zero external paid service dependencies.
- Defense against token forgery, replay, and timing attacks.
- Graceful session termination and token revocation.
