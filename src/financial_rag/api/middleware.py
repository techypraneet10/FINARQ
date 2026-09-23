"""FastAPI custom middlewares for security headers, rate limiting, correlation tracing, and telemetry."""

import hashlib
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from financial_rag.config.settings import get_settings
from financial_rag.domain.entities.observability import TraceContext
from financial_rag.infrastructure.logging import get_logger, request_id_ctx_var
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.tracer import (
    current_span_id_ctx_var,
    trace_id_ctx_var,
    tracer,
)
from financial_rag.infrastructure.security.rate_limiter import InMemoryRateLimiter

logger = get_logger("api.middleware")

# Global singleton rate limiter instance
_global_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the active singleton in-memory rate limiter."""
    return _global_rate_limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce defense-in-depth HTTP security headers on all responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window API rate limiting middleware with granular per-endpoint thresholds."""

    def __init__(self, app: ASGIApp, rate_limiter: InMemoryRateLimiter | None = None) -> None:
        super().__init__(app)
        self._limiter = rate_limiter or InMemoryRateLimiter()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        app_settings = getattr(request.app.state, "settings", None) or get_settings()
        sec_settings = app_settings.security
        if not sec_settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        method = request.method

        # Exempt health, metrics, documentation, and OpenAPI metadata
        if path.endswith(("/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        # Determine threshold by route
        max_requests = sec_settings.rate_limit_default_per_minute
        window_seconds = 60

        if path.startswith("/api/v1/auth"):
            max_requests = sec_settings.rate_limit_auth_per_minute
        elif path.startswith("/api/v1/documents") and method == "POST":
            max_requests = sec_settings.rate_limit_upload_per_minute
        elif path.startswith("/api/v1/answers"):
            max_requests = sec_settings.rate_limit_answers_per_minute
        elif path.startswith("/api/v1/retrieval") or path.startswith("/api/v1/search"):
            max_requests = sec_settings.rate_limit_retrieval_per_minute

        # Determine client identity key
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            client_key = f"tok:{token_hash}:{path}"
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"
            client_key = f"ip:{client_ip}:{path}"

        limiter = getattr(request.app.state, "rate_limiter", None) or self._limiter
        allowed, remaining, retry_after = limiter.check_rate_limit(
            key=client_key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for key '{client_key}' on '{path}'. Retry after {retry_after}s."
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {max_requests} req/min exceeded. Retry after {retry_after:.1f}s.",
                        "details": {
                            "retry_after_seconds": retry_after,
                            "limit_per_minute": max_requests,
                        },
                    }
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates correlation IDs (X-Request-ID, X-Trace-ID, W3C traceparent) per request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        header_request_id = request.headers.get("X-Request-ID")
        request_id = header_request_id if header_request_id else str(uuid.uuid4())

        header_traceparent = request.headers.get("traceparent")
        header_trace_id = request.headers.get("X-Trace-ID")

        if header_traceparent:
            trace_ctx = TraceContext.from_traceparent(header_traceparent, request_id=request_id)
            trace_id = trace_ctx.trace_id
        elif header_trace_id:
            trace_id = header_trace_id
            trace_ctx = TraceContext(trace_id=trace_id, request_id=request_id)
        else:
            trace_id = str(uuid.uuid4())
            trace_ctx = TraceContext(trace_id=trace_id, request_id=request_id)

        # Set context variables for structured logging and distributed tracing
        req_token = request_id_ctx_var.set(request_id)
        trace_token = trace_id_ctx_var.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["traceparent"] = trace_ctx.to_traceparent()
            return response
        finally:
            request_id_ctx_var.reset(req_token)
            trace_id_ctx_var.reset(trace_token)


class TimingAndLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks request duration, manages root API spans, and records HTTP metrics."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method

        # Normalize low-cardinality endpoint tag for metrics
        endpoint_tag = "/api/v1/..." if path.startswith("/api/v1") else path
        if path.endswith("/health"):
            endpoint_tag = "/health"
        elif path.endswith("/ready"):
            endpoint_tag = "/ready"
        elif path.endswith("/metrics"):
            endpoint_tag = "/metrics"
        elif "/answers" in path:
            endpoint_tag = "/api/v1/answers"
        elif "/reasoning" in path:
            endpoint_tag = "/api/v1/reasoning"
        elif "/retrieval" in path:
            endpoint_tag = "/api/v1/retrieval"
        elif "/documents" in path:
            endpoint_tag = "/api/v1/documents"
        elif "/auth" in path:
            endpoint_tag = "/api/v1/auth"
        elif "/users" in path:
            endpoint_tag = "/api/v1/users"
        elif "/audit" in path:
            endpoint_tag = "/api/v1/audit"

        span = tracer.start_span(
            name=f"HTTP {method} {endpoint_tag}",
            attributes={"http_method": method, "endpoint": endpoint_tag},
        )
        span_token = current_span_id_ctx_var.set(span.span_id)

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000.0
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

            # Record telemetry metrics
            status_str = str(response.status_code)
            metrics_registry.increment_counter(
                name="http_requests_total",
                labels={
                    "endpoint": endpoint_tag,
                    "status": status_str,
                    "http_method": method,
                },
            )
            metrics_registry.record_histogram(
                name="http_request_duration_ms",
                value=process_time_ms,
                labels={
                    "endpoint": endpoint_tag,
                    "status": status_str,
                },
            )

            # Avoid polluting logs with health check probes
            if not path.endswith(("/health", "/ready", "/metrics")):
                logger.info(f"{method} {path} - {response.status_code} ({process_time_ms:.2f}ms)")

            return response
        except Exception as exc:
            span.record_error(exc)
            metrics_registry.increment_counter(
                name="http_requests_total",
                labels={
                    "endpoint": endpoint_tag,
                    "status": "500",
                    "http_method": method,
                },
            )
            raise
        finally:
            span.end()
            current_span_id_ctx_var.reset(span_token)


def register_middlewares(app: FastAPI) -> None:
    """Register standard middleware stack in correct execution order."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TimingAndLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
