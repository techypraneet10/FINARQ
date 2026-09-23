"""Retry mechanisms with exponential backoff, jitter, and error classification."""

import asyncio
import random
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from financial_rag.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.observability.metrics import metrics_registry

logger = get_logger("financial_rag.infrastructure.resilience.retry")

T = TypeVar("T")

# Non-retryable error types representing client/semantic errors where retries are pointless
NON_RETRYABLE_EXCEPTIONS = (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValueError,
    TypeError,
    KeyError,
)


def is_retryable_exception(exc: BaseException) -> bool:
    """Classify whether an exception is transient (retryable) or terminal (non-retryable)."""
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False

    # Check for HTTP status codes if present on exception
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(status_code, int):
        return not (400 <= status_code < 500 and status_code not in (408, 429))

    return True


async def retry_with_backoff(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_retries: int = 3,
    initial_backoff_seconds: float = 0.5,
    backoff_factor: float = 2.0,
    max_backoff_seconds: float = 10.0,
    jitter: bool = True,
    retryable_predicate: Callable[[BaseException], bool] | None = None,
    service_name: str = "external_service",
    **kwargs: Any,
) -> T:
    """Execute asynchronous callable with bounded exponential backoff and jitter on retryable failures."""
    predicate = retryable_predicate or is_retryable_exception
    last_exception: BaseException | None = None
    current_backoff = initial_backoff_seconds

    for attempt in range(1, max_retries + 2):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc

            if attempt > max_retries or not predicate(exc):
                if not predicate(exc):
                    logger.debug(f"Non-retryable exception encountered on '{service_name}': {exc}")
                else:
                    metrics_registry.record_retry_attempt(
                        component=service_name,
                        attempt=attempt,
                        reason=type(exc).__name__,
                        status="exhausted",
                    )
                    logger.warning(
                        f"Exhausted all {max_retries} retries for '{service_name}'. Final error: {exc}"
                    )
                raise

            metrics_registry.record_retry_attempt(
                component=service_name,
                attempt=attempt,
                reason=type(exc).__name__,
                status="retrying",
            )
            sleep_duration = current_backoff
            if jitter:
                # Full jitter: random sleep between 0 and current_backoff
                sleep_duration = random.uniform(0.1, current_backoff)

            logger.warning(
                f"Attempt {attempt}/{max_retries} failed for '{service_name}' ({exc}). Retrying in {sleep_duration:.2f}s..."
            )
            await asyncio.sleep(sleep_duration)
            current_backoff = min(current_backoff * backoff_factor, max_backoff_seconds)

    assert last_exception is not None
    raise last_exception
