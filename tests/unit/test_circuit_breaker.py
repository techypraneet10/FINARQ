"""Unit tests for Circuit Breaker and retry mechanisms."""

import asyncio

import pytest

from financial_rag.domain.exceptions import (
    InfrastructureError,
    ValidationError,
)
from financial_rag.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)
from financial_rag.infrastructure.resilience.retry import retry_with_backoff


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_recovers() -> None:
    breaker = CircuitBreaker(
        service_name="test_llm",
        failure_threshold=3,
        recovery_timeout_seconds=0.1,
        half_open_success_threshold=2,
    )

    assert breaker.state == CircuitBreakerState.CLOSED

    # 1. Successful execution
    async def mock_success() -> str:
        return "success"

    res = await breaker.execute(mock_success)
    assert res == "success"
    assert breaker.state == CircuitBreakerState.CLOSED

    # 2. Trigger failures up to threshold
    async def mock_fail() -> None:
        raise InfrastructureError("LLM downstream timeout")

    for _ in range(2):
        with pytest.raises(InfrastructureError):
            await breaker.execute(mock_fail)
        assert breaker.state == CircuitBreakerState.CLOSED

    # 3rd failure trips the breaker
    with pytest.raises(InfrastructureError):
        await breaker.execute(mock_fail)

    assert breaker.state == CircuitBreakerState.OPEN

    # 3. Subsequent calls fail-fast with CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await breaker.execute(mock_success)
    assert "is OPEN" in str(exc_info.value)

    # 4. Wait for recovery timeout -> transitions to HALF_OPEN
    await asyncio.sleep(0.15)
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    # 5. Execute 2 successful calls to recover to CLOSED
    await breaker.execute(mock_success)
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    await breaker.execute(mock_success)
    assert breaker.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_retry_with_backoff_success() -> None:
    attempts = 0

    async def flaky_call() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("Transient connection drop")
        return "recovered"

    result = await retry_with_backoff(
        flaky_call,
        max_retries=3,
        initial_backoff_seconds=0.01,
        jitter=False,
    )

    assert result == "recovered"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_aborts_on_non_retryable_exception() -> None:
    attempts = 0

    async def non_retryable_call() -> None:
        nonlocal attempts
        attempts += 1
        raise ValidationError("Invalid fiscal period format")

    with pytest.raises(ValidationError):
        await retry_with_backoff(
            non_retryable_call,
            max_retries=3,
            initial_backoff_seconds=0.01,
        )

    # Non-retryable error must not be retried
    assert attempts == 1
