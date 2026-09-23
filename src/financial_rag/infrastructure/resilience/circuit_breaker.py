"""Circuit breaker implementation for protecting against cascading external service failures."""

import asyncio
import time
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Any, TypeVar

from financial_rag.domain.exceptions import InfrastructureError
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.observability.metrics import metrics_registry

logger = get_logger("financial_rag.infrastructure.resilience.circuit_breaker")

T = TypeVar("T")


class CircuitBreakerState(StrEnum):
    """Lifecycle states of the Circuit Breaker pattern."""

    CLOSED = "CLOSED"  # Normal operation: requests pass through
    OPEN = "OPEN"  # Tripped: requests fail fast without calling external dependency
    HALF_OPEN = "HALF_OPEN"  # Trial probe: allowing limited requests to test recovery


class CircuitBreakerOpenError(InfrastructureError):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""

    def __init__(self, service_name: str, recovery_time_remaining: float) -> None:
        super().__init__(
            message=f"Circuit breaker for service '{service_name}' is OPEN. Fast-failing request (retry in {recovery_time_remaining:.1f}s).",
            details={
                "service_name": service_name,
                "recovery_time_remaining": recovery_time_remaining,
            },
        )
        self.service_name = service_name
        self.recovery_time_remaining = recovery_time_remaining


class CircuitBreaker:
    """Production-grade asynchronous circuit breaker with failure threshold and cooldown recovery."""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
        is_failure_fn: Callable[[BaseException], bool] | None = None,
    ) -> None:
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold
        self._is_failure_fn = is_failure_fn or (lambda _: True)

        self._state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_state_change: float = time.monotonic()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        """Current operational state of the circuit breaker."""
        now = time.monotonic()
        if (
            self._state == CircuitBreakerState.OPEN
            and (now - self._last_state_change) >= self.recovery_timeout
        ):
            return CircuitBreakerState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def success_count(self) -> int:
        return self._success_count

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute the asynchronous operation wrapped in circuit breaker protection."""
        async with self._lock:
            current_state = self.state
            now = time.monotonic()

            if current_state == CircuitBreakerState.OPEN:
                remaining = max(0.0, self.recovery_timeout - (now - self._last_state_change))
                logger.warning(
                    f"Circuit breaker '{self.service_name}' is OPEN. Fast-failing execution. ({remaining:.1f}s cooldown remaining)"
                )
                metrics_registry.record_circuit_breaker_rejection(self.service_name)
                raise CircuitBreakerOpenError(
                    service_name=self.service_name,
                    recovery_time_remaining=remaining,
                )

            if (
                current_state == CircuitBreakerState.HALF_OPEN
                and self._state != CircuitBreakerState.HALF_OPEN
            ):
                self._state = CircuitBreakerState.HALF_OPEN
                self._success_count = 0
                self._last_state_change = now
                metrics_registry.record_circuit_breaker_transition(
                    self.service_name, "OPEN", "HALF_OPEN"
                )
                metrics_registry.record_circuit_breaker_state(self.service_name, 1.0)
                logger.info(
                    f"Circuit breaker '{self.service_name}' transitioned to HALF_OPEN trial state."
                )

        # Execute target coroutine outside the lock to prevent blocking concurrent throughput
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            if self._is_failure_fn(exc):
                await self._record_failure(exc)
            raise

        await self._record_success()
        return result

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_success_threshold:
                    self._state = CircuitBreakerState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._last_state_change = time.monotonic()
                    metrics_registry.record_circuit_breaker_transition(
                        self.service_name, "HALF_OPEN", "CLOSED"
                    )
                    metrics_registry.record_circuit_breaker_state(self.service_name, 0.0)
                    logger.info(
                        f"Circuit breaker '{self.service_name}' successfully recovered and transitioned to CLOSED."
                    )
            elif self._state == CircuitBreakerState.CLOSED:
                self._failure_count = 0

    async def _record_failure(self, exc: BaseException) -> None:
        async with self._lock:
            now = time.monotonic()
            self._failure_count += 1
            logger.warning(
                f"Recorded failure {self._failure_count}/{self.failure_threshold} on '{self.service_name}': {exc}"
            )

            if self._state == CircuitBreakerState.HALF_OPEN:
                # Any failure during half-open immediately trips back to OPEN
                self._state = CircuitBreakerState.OPEN
                self._last_state_change = now
                metrics_registry.record_circuit_breaker_transition(
                    self.service_name, "HALF_OPEN", "OPEN"
                )
                metrics_registry.record_circuit_breaker_state(self.service_name, 2.0)
                logger.error(
                    f"Trial failed in HALF_OPEN state. Circuit breaker '{self.service_name}' returned to OPEN."
                )
            elif (
                self._state == CircuitBreakerState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitBreakerState.OPEN
                self._last_state_change = now
                metrics_registry.record_circuit_breaker_transition(
                    self.service_name, "CLOSED", "OPEN"
                )
                metrics_registry.record_circuit_breaker_state(self.service_name, 2.0)
                logger.error(
                    f"Failure threshold reached ({self._failure_count}). Circuit breaker '{self.service_name}' TRIPPED to OPEN."
                )

    def reset(self) -> None:
        """Manually reset the circuit breaker back to CLOSED state."""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_state_change = time.monotonic()
        metrics_registry.record_circuit_breaker_state(self.service_name, 0.0)
        logger.info(f"Circuit breaker '{self.service_name}' was manually reset to CLOSED.")
