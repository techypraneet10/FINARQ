"""Standard-compliant, cryptographically signed JWT token manager with strict validation."""

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, ClassVar

from financial_rag.config.settings import SecuritySettings, get_settings
from financial_rag.domain.entities.security import UserRole
from financial_rag.domain.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)
from financial_rag.domain.interfaces.security import TokenManagerProtocol


def _b64url_encode(data: bytes) -> str:
    """Base64URL encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data_str: str) -> bytes:
    """Base64URL decode with restored padding."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


class JwtTokenManager(TokenManagerProtocol):
    """Zero-dependency JWT manager implementing HMAC-SHA256 with strict claim verification."""

    ALLOWED_ALGORITHMS: ClassVar[set[str]] = {"HS256"}

    def __init__(self, security_settings: SecuritySettings | None = None) -> None:
        self._settings = security_settings or get_settings().security
        self._secret = self._settings.jwt_secret_key.get_secret_value().encode("utf-8")
        self._issuer = self._settings.jwt_issuer
        self._audience = self._settings.jwt_audience
        self._access_ttl_seconds = self._settings.access_token_ttl_minutes * 60
        self._refresh_ttl_seconds = self._settings.refresh_token_ttl_days * 86400

    def _sign(self, header_b64: str, payload_b64: str) -> str:
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        return _b64url_encode(signature)

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: UserRole,
        expires_in_minutes: int | None = None,
        custom_claims: dict[str, Any] | None = None,
    ) -> str:
        """Issue a short-lived, signed JWT access token."""
        now = int(time.time())
        ttl = (expires_in_minutes * 60) if expires_in_minutes else self._access_ttl_seconds

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }
        payload = {
            "sub": str(user_id),
            "tid": str(tenant_id),
            "role": role.value if isinstance(role, UserRole) else str(role),
            "iss": self._issuer,
            "aud": self._audience,
            "iat": now,
            "exp": now + ttl,
            "jti": str(uuid.uuid4()),
            "type": "access",
            **(custom_claims or {}),
        }

        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        sig_b64 = self._sign(header_b64, payload_b64)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        expires_in_days: int | None = None,
    ) -> tuple[str, str, str]:
        """Issue a long-lived refresh token. Returns (raw_jwt, token_jti, token_sha256_hash)."""
        now = int(time.time())
        ttl = (expires_in_days * 86400) if expires_in_days else self._refresh_ttl_seconds
        jti = str(uuid.uuid4())

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }
        payload = {
            "sub": str(user_id),
            "tid": str(tenant_id),
            "iss": self._issuer,
            "aud": self._audience,
            "iat": now,
            "exp": now + ttl,
            "jti": jti,
            "type": "refresh",
        }

        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        sig_b64 = self._sign(header_b64, payload_b64)

        raw_token = f"{header_b64}.{payload_b64}.{sig_b64}"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        return raw_token, jti, token_hash

    def _verify_token_common(self, token: str, expected_type: str) -> dict[str, Any]:
        if not token or not isinstance(token, str):
            raise InvalidTokenError(message="Authentication token is missing or empty.")

        parts = token.strip().split(".")
        if len(parts) != 3:
            raise InvalidTokenError(
                message="Malformed JWT token format: expected 3 dot-separated segments."
            )

        header_b64, payload_b64, signature_b64 = parts

        # 1. Parse and validate header
        try:
            header_json = _b64url_decode(header_b64).decode("utf-8")
            header = json.loads(header_json)
        except Exception as ex:
            raise InvalidTokenError(message=f"Failed to decode JWT header: {ex}") from ex

        alg = header.get("alg")
        if not alg or alg not in self.ALLOWED_ALGORITHMS:
            raise InvalidTokenError(
                message=f"Rejected JWT algorithm '{alg}'. Only {list(self.ALLOWED_ALGORITHMS)} allowed."
            )

        # 2. Verify cryptographic signature in constant time
        expected_sig = self._sign(header_b64, payload_b64)
        if not hmac.compare_digest(signature_b64, expected_sig):
            raise InvalidTokenError(message="Invalid token signature.")

        # 3. Parse and validate payload claims
        try:
            payload_json = _b64url_decode(payload_b64).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception as ex:
            raise InvalidTokenError(message=f"Failed to decode JWT payload: {ex}") from ex

        now = int(time.time())

        # Check expiration (exp)
        exp = payload.get("exp")
        if exp is None or not isinstance(exp, (int, float)):
            raise InvalidTokenError(message="Token missing required 'exp' claim.")
        if now > exp:
            raise TokenExpiredError(
                message="Authentication token has expired.",
                details={"expired_at": exp, "current_time": now},
            )

        # Check issued-at (iat)
        iat = payload.get("iat")
        if iat is not None and isinstance(iat, (int, float)) and iat > now + 60:
            raise InvalidTokenError(message="Token 'iat' is in the future.")

        # Check issuer (iss)
        iss = payload.get("iss")
        if iss != self._issuer:
            raise InvalidTokenError(
                message=f"Invalid token issuer '{iss}', expected '{self._issuer}'."
            )

        # Check audience (aud)
        aud = payload.get("aud")
        if aud != self._audience:
            raise InvalidTokenError(
                message=f"Invalid token audience '{aud}', expected '{self._audience}'."
            )

        # Check subject (sub) & tenant ID (tid)
        if not payload.get("sub"):
            raise InvalidTokenError(message="Token missing required 'sub' (user_id) claim.")
        if not payload.get("tid"):
            raise InvalidTokenError(message="Token missing required 'tid' (tenant_id) claim.")

        # Check token type
        tok_type = payload.get("type")
        if tok_type != expected_type:
            raise InvalidTokenError(
                message=f"Invalid token type: expected '{expected_type}', got '{tok_type}'."
            )

        return dict(payload)

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Validate an access token and return verified claims."""
        return self._verify_token_common(token, expected_type="access")

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        """Validate a refresh token and return verified claims."""
        return self._verify_token_common(token, expected_type="refresh")
