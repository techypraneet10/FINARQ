"""Memory-hard, cryptographically secure password hashing using standard library scrypt."""

import hashlib
import hmac
import secrets

from financial_rag.domain.exceptions import ValidationError
from financial_rag.domain.interfaces.security import PasswordHasherProtocol


class ScryptPasswordHasher(PasswordHasherProtocol):
    """Secure password hasher using memory-hard scrypt algorithm with salt and constant-time verification."""

    def __init__(
        self,
        n: int = 16384,
        r: int = 8,
        p: int = 1,
        key_len: int = 64,
        salt_len: int = 32,
    ) -> None:
        self._n = n
        self._r = r
        self._p = p
        self._key_len = key_len
        self._salt_len = salt_len

    def hash_password(self, plain_password: str) -> str:
        """Generate a secure memory-hard password hash."""
        if not plain_password or len(plain_password.strip()) == 0:
            raise ValidationError(
                message="Password cannot be empty or whitespace only.",
                code="INVALID_PASSWORD",
            )

        salt = secrets.token_bytes(self._salt_len)
        password_bytes = plain_password.encode("utf-8")

        try:
            derived = hashlib.scrypt(
                password_bytes,
                salt=salt,
                n=self._n,
                r=self._r,
                p=self._p,
                dklen=self._key_len,
            )
            salt_hex = salt.hex()
            derived_hex = derived.hex()
            return f"scrypt$n={self._n},r={self._r},p={self._p}${salt_hex}${derived_hex}"
        except Exception:
            # Fallback to PBKDF2 with 600,000 iterations if scrypt fails on constrained platforms
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                password_bytes,
                salt,
                600000,
                dklen=self._key_len,
            )
            salt_hex = salt.hex()
            derived_hex = derived.hex()
            return f"pbkdf2_sha256$600000${salt_hex}${derived_hex}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against stored hash using constant-time comparison."""
        if not plain_password or not hashed_password:
            return False

        try:
            parts = hashed_password.split("$")
            if len(parts) < 4:
                return False

            algo = parts[0]
            password_bytes = plain_password.encode("utf-8")

            if algo == "scrypt":
                # scrypt$n=16384,r=8,p=1$<salt_hex>$<derived_hex>
                params_str = parts[1]
                salt = bytes.fromhex(parts[2])
                expected_derived = bytes.fromhex(parts[3])

                # Parse params
                param_dict = dict(item.split("=") for item in params_str.split(","))
                n = int(param_dict.get("n", self._n))
                r = int(param_dict.get("r", self._r))
                p = int(param_dict.get("p", self._p))

                actual_derived = hashlib.scrypt(
                    password_bytes,
                    salt=salt,
                    n=n,
                    r=r,
                    p=p,
                    dklen=len(expected_derived),
                )
                return hmac.compare_digest(actual_derived, expected_derived)

            elif algo == "pbkdf2_sha256":
                # pbkdf2_sha256$<iterations>$<salt_hex>$<derived_hex>
                iterations = int(parts[1])
                salt = bytes.fromhex(parts[2])
                expected_derived = bytes.fromhex(parts[3])

                actual_derived = hashlib.pbkdf2_hmac(
                    "sha256",
                    password_bytes,
                    salt,
                    iterations,
                    dklen=len(expected_derived),
                )
                return hmac.compare_digest(actual_derived, expected_derived)

            return False
        except Exception:
            return False
