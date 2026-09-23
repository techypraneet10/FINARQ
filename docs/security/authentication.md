# Financial RAG Platform — Authentication Architecture

## 1. Password Security & Hashing
- **Algorithm**: Memory-hard `scrypt` key derivation function (`salt_length=16`, `n=16384`, `r=8`, `p=1`).
- **Policy**: Minimum 8 characters (default); production recommendation >= 12 characters with mixed complexity.
- **Storage**: Stored strictly as format `scrypt$N$r$p$salt_hex$hash_hex` in `users.hashed_password`.
- **Invariants**: Plaintext passwords are never logged, never emitted in API responses, and never stored in memory longer than the request duration.

---

## 2. JWT Access Token Management
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Signature Secret**: Configured via `SECURITY_JWT_SECRET_KEY` (Pydantic `SecretStr`). Fails fast on startup if key is < 32 chars or contains default test strings in production.
- **Standard Claims**:
  - `sub`: Authenticated User ID (UUID string).
  - `tid`: Authenticated Tenant ID (UUID string).
  - `role`: Role string (`owner`, `admin`, `member`, `viewer`).
  - `iss`: `"financial-rag-platform"`.
  - `aud`: `"financial-rag-api"`.
  - `exp`: UTC expiration timestamp (15-minute default TTL).
  - `iat`: UTC issuance timestamp.
- **Validation**: Strict cryptographic signature verification; unsigned tokens or `"alg": "none"` tokens are unconditionally rejected with HTTP 401.

---

## 3. Refresh Token Rotation & Replay Attack Defense
- **Storage**: Persistent records in `refresh_tokens` table with SHA-256 hash of token value.
- **Lifecycle**: Default 7-day TTL.
- **Rotation**: On every `/api/v1/auth/refresh` invocation, the current refresh token is marked `revoked=True` and pointers are linked to the newly issued token ID (`rotated_to_token_id`).
- **Replay Attack Detection**: If an already revoked refresh token is presented to `/refresh`, the backend detects a potential token theft and executes an immediate cascade revocation of **all** refresh tokens belonging to that user ID.

---

## 4. Brute Force Protection & Account Lockout
- **Rate Limiting**: Sliding-window limiter restricts `/api/v1/auth/login` to 10 requests/minute per client IP.
- **Lockout Mechanism**: After 5 consecutive failed login attempts on a specific `IP:email` identifier, the account is temporarily locked for 300 seconds (5 minutes).
- **HTTP Response**: Returns `HTTP 429 Too Many Requests` with standard `Retry-After: <seconds>` header.
