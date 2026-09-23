"""Unit tests for JWT token management and cryptographic validation."""

import pytest
from pydantic import SecretStr

from financial_rag.config.settings import SecuritySettings
from financial_rag.domain.entities.security import UserRole
from financial_rag.domain.exceptions import (
    InvalidTokenError,
    SecurityError,
    TokenExpiredError,
)
from financial_rag.infrastructure.security.jwt import JwtTokenManager


@pytest.fixture
def jwt_manager() -> JwtTokenManager:
    settings = SecuritySettings(
        jwt_secret_key=SecretStr("unit-test-super-secret-key-32chars-min!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        jwt_issuer="financial-rag-test",
        jwt_audience="financial-rag-client",
    )
    return JwtTokenManager(security_settings=settings)


def test_access_token_creation_and_verification(jwt_manager: JwtTokenManager) -> None:
    token = jwt_manager.create_access_token(
        user_id="user-123",
        tenant_id="tenant-abc",
        role=UserRole.ADMIN,
    )

    claims = jwt_manager.verify_access_token(token)
    assert claims["sub"] == "user-123"
    assert claims["tid"] == "tenant-abc"
    assert claims["role"] == "admin"
    assert claims["iss"] == "financial-rag-test"
    assert claims["aud"] == "financial-rag-client"


def test_refresh_token_creation_and_hashing(jwt_manager: JwtTokenManager) -> None:
    raw_token, jti, token_hash = jwt_manager.create_refresh_token(
        user_id="user-123",
        tenant_id="tenant-abc",
    )

    assert isinstance(raw_token, str)
    assert isinstance(jti, str)
    assert isinstance(token_hash, str)

    claims = jwt_manager.verify_refresh_token(raw_token)
    assert claims["jti"] == jti
    assert claims["sub"] == "user-123"
    assert claims["tid"] == "tenant-abc"
    assert claims["type"] == "refresh"


def test_tampered_token_rejection(jwt_manager: JwtTokenManager) -> None:
    token = jwt_manager.create_access_token(
        user_id="user-123",
        tenant_id="tenant-abc",
        role=UserRole.MEMBER,
    )

    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}tampered.{parts[2]}"

    with pytest.raises(InvalidTokenError):
        jwt_manager.verify_access_token(tampered)


def test_expired_token_rejection(jwt_manager: JwtTokenManager) -> None:
    import base64
    import json
    import time

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "user-123",
        "tid": "tenant-abc",
        "role": "viewer",
        "iss": "financial-rag-test",
        "aud": "financial-rag-client",
        "iat": int(time.time()) - 1000,
        "exp": int(time.time()) - 500,  # Expired 500s ago
        "jti": "jti-expired",
        "type": "access",
    }
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig_b64 = jwt_manager._sign(h_b64, p_b64)
    expired_token = f"{h_b64}.{p_b64}.{sig_b64}"

    with pytest.raises(TokenExpiredError):
        jwt_manager.verify_access_token(expired_token)


def test_invalid_algorithm_rejection(jwt_manager: JwtTokenManager) -> None:
    # Attempting to verify token with invalid alg header
    import base64
    import json

    header = {"alg": "none", "typ": "JWT"}
    payload = {"sub": "user-1", "tid": "t1", "role": "admin"}

    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    forged = f"{h_b64}.{p_b64}."

    with pytest.raises(SecurityError):
        jwt_manager.verify_access_token(forged)
