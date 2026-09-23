"""Thread-safe sliding-window rate limiter and brute force defense."""

import threading
import time
from collections import defaultdict

from financial_rag.config.settings import SecuritySettings, get_settings
from financial_rag.domain.interfaces.security import RateLimiterProtocol


class InMemoryRateLimiter(RateLimiterProtocol):
    """Thread-safe sliding-window rate limiter with brute-force lockout protection."""

    def __init__(self, security_settings: SecuritySettings | None = None) -> None:
        self._settings = security_settings or get_settings().security
        self._max_failed_logins = self._settings.max_failed_logins
        self._lockout_duration = float(self._settings.lockout_duration_seconds)
        self._enabled = self._settings.rate_limit_enabled

        self._lock = threading.Lock()
        # key -> list of request timestamps (float)
        self._request_history: dict[str, list[float]] = defaultdict(list)
        # identifier -> list of failed login timestamps (float)
        self._failed_logins: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, float]:
        """Check rate limit for a key. Returns (is_allowed, remaining_requests, retry_after_seconds)."""
        if not self._enabled:
            return True, max_requests, 0.0

        now = time.time()
        window_start = now - float(window_seconds)

        with self._lock:
            # Prune timestamps outside sliding window
            timestamps = [t for t in self._request_history[key] if t > window_start]

            if len(timestamps) >= max_requests:
                oldest_in_window = timestamps[0]
                retry_after = max(0.1, (oldest_in_window + window_seconds) - now)
                self._request_history[key] = timestamps
                return False, 0, round(retry_after, 2)

            timestamps.append(now)
            self._request_history[key] = timestamps
            remaining = max(0, max_requests - len(timestamps))
            return True, remaining, 0.0

    def record_failed_login(self, identifier: str) -> int:
        """Record a failed login attempt. Returns current total active failed attempts."""
        now = time.time()
        window_start = now - self._lockout_duration

        with self._lock:
            history = [t for t in self._failed_logins[identifier] if t > window_start]
            history.append(now)
            self._failed_logins[identifier] = history
            return len(history)

    def reset_failed_logins(self, identifier: str) -> None:
        """Clear failed login attempts upon successful login."""
        with self._lock:
            self._failed_logins.pop(identifier, None)

    def is_locked_out(self, identifier: str) -> tuple[bool, float]:
        """Check if an identifier is temporarily locked out. Returns (is_locked, retry_after_seconds)."""
        if not self._enabled:
            return False, 0.0

        now = time.time()
        window_start = now - self._lockout_duration

        with self._lock:
            history = [t for t in self._failed_logins[identifier] if t > window_start]
            self._failed_logins[identifier] = history

            if len(history) >= self._max_failed_logins:
                oldest_in_window = history[0]
                retry_after = max(0.1, (oldest_in_window + self._lockout_duration) - now)
                return True, round(retry_after, 2)

            return False, 0.0

    def clear(self) -> None:
        """Reset all rate limiter state (useful for tests)."""
        with self._lock:
            self._request_history.clear()
            self._failed_logins.clear()
