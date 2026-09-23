"""Unit tests for password hashing infrastructure."""

from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher


def test_scrypt_hashing_and_verification() -> None:
    hasher = ScryptPasswordHasher()
    pwd = "CorrectFinancialSecret#2026"

    hashed = hasher.hash_password(pwd)
    assert hashed.startswith("scrypt$")

    assert hasher.verify_password(pwd, hashed) is True
    assert hasher.verify_password("WrongPassword123", hashed) is False


def test_salt_randomness() -> None:
    hasher = ScryptPasswordHasher()
    pwd = "IdenticalPassword"

    h1 = hasher.hash_password(pwd)
    h2 = hasher.hash_password(pwd)
    assert h1 != h2
    assert hasher.verify_password(pwd, h1) is True
    assert hasher.verify_password(pwd, h2) is True


def test_invalid_hash_format_handling() -> None:
    hasher = ScryptPasswordHasher()
    assert hasher.verify_password("secret", "invalid_format") is False
    assert hasher.verify_password("secret", "unknown$16384$8$1$salt$hash") is False
