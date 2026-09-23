"""Unit tests for sliding-window rate limiter and login lockout."""

from financial_rag.infrastructure.security.rate_limiter import InMemoryRateLimiter


def test_sliding_window_rate_limiting() -> None:
    limiter = InMemoryRateLimiter()
    key = "test_client_key"

    # Allow 3 requests in a 10s window
    allowed1, rem1, _ = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert allowed1 is True
    assert rem1 == 2

    allowed2, rem2, _ = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, _ = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert allowed3 is True
    assert rem3 == 0

    # 4th request must be throttled
    allowed4, rem4, retry_after = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert allowed4 is False
    assert rem4 == 0
    assert retry_after > 0


def test_login_brute_force_lockout() -> None:
    from financial_rag.config.settings import SecuritySettings

    settings = SecuritySettings(
        max_failed_logins=3,
        lockout_duration_seconds=60,
    )
    limiter = InMemoryRateLimiter(security_settings=settings)
    login_id = "192.168.1.1:user@example.com"

    # 3 failed attempts
    for _ in range(3):
        limiter.record_failed_login(login_id)

    is_locked, retry_after = limiter.is_locked_out(login_id)
    assert is_locked is True
    assert retry_after > 0

    # Reset failed attempts
    limiter.reset_failed_logins(login_id)
    is_locked, _ = limiter.is_locked_out(login_id)
    assert is_locked is False
