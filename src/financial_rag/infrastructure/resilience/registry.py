"""Centralized Circuit Breaker Registry for infrastructure adapters and external services."""

import threading
from typing import Any

from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)


class CircuitBreakerRegistry:
    """Thread-safe registry managing and inspecting named Circuit Breakers across the platform."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
    ) -> CircuitBreaker:
        """Retrieve existing circuit breaker or create a new configured instance."""
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(
                    service_name=service_name,
                    failure_threshold=failure_threshold,
                    recovery_timeout_seconds=recovery_timeout_seconds,
                    half_open_success_threshold=half_open_success_threshold,
                )
            return self._breakers[service_name]

    def register(self, breaker: CircuitBreaker) -> None:
        """Register an existing circuit breaker instance."""
        with self._lock:
            self._breakers[breaker.service_name] = breaker

    def get(self, service_name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name if registered."""
        with self._lock:
            return self._breakers.get(service_name)

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """Export operational state and statistics of all managed circuit breakers."""
        statuses: dict[str, dict[str, Any]] = {}
        with self._lock:
            for name, cb in self._breakers.items():
                state = cb.state
                state_val = (
                    0.0
                    if state == CircuitBreakerState.CLOSED
                    else (1.0 if state == CircuitBreakerState.HALF_OPEN else 2.0)
                )
                metrics_registry.record_circuit_breaker_state(name, state_val)

                statuses[name] = {
                    "state": state.value,
                    "failure_count": cb.failure_count,
                    "success_count": cb.success_count,
                    "failure_threshold": cb.failure_threshold,
                    "recovery_timeout_seconds": cb.recovery_timeout,
                }
        return statuses

    def reset_all(self) -> None:
        """Reset all circuit breakers back to CLOSED state."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()


# Default singleton registry
circuit_breaker_registry = CircuitBreakerRegistry()
