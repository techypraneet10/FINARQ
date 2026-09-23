"""API layer exception handlers translating application errors to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from financial_rag.domain.exceptions import (
    AccountSuspendedError,
    AnswerGenerationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DomainError,
    DuplicateDocumentError,
    ExternalServiceError,
    FileValidationError,
    FinancialRAGError,
    InfrastructureError,
    InvalidTokenError,
    LLMTimeoutError,
    NotFoundError,
    RateLimitExceededError,
    ReasoningError,
    SecurityError,
    TenantIsolationError,
    TenantSuspendedError,
    TokenExpiredError,
    TokenRevokedError,
)
from financial_rag.domain.exceptions import (
    ValidationError as DomainValidationError,
)
from financial_rag.infrastructure.logging import get_logger, request_id_ctx_var

logger = get_logger("api.exceptions")


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers on the FastAPI application."""

    @app.exception_handler(AuthenticationError)
    @app.exception_handler(InvalidTokenError)
    @app.exception_handler(TokenExpiredError)
    @app.exception_handler(TokenRevokedError)
    @app.exception_handler(AccountSuspendedError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        logger.warning(f"Authentication failure: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationError)
    @app.exception_handler(TenantIsolationError)
    @app.exception_handler(TenantSuspendedError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        logger.warning(f"Authorization failure: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_error_handler(
        request: Request, exc: RateLimitExceededError
    ) -> JSONResponse:
        logger.warning(f"Rate limit error: {exc.message}")
        retry_after = exc.details.get("retry_after_seconds", 60)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    @app.exception_handler(SecurityError)
    async def generic_security_error_handler(request: Request, exc: SecurityError) -> JSONResponse:
        logger.warning(f"Security error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.warning(f"Resource not found: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(DuplicateDocumentError)
    async def duplicate_document_error_handler(
        request: Request, exc: DuplicateDocumentError
    ) -> JSONResponse:
        logger.warning(f"Duplicate document detected: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(DomainValidationError)
    @app.exception_handler(FileValidationError)
    async def domain_validation_error_handler(
        request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        logger.warning(f"Domain validation failed: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(f"Request schema validation failed: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "Invalid request parameters or payload.",
                    "details": {"errors": exc.errors()},
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(AnswerGenerationError)
    async def answer_generation_error_handler(
        request: Request, exc: AnswerGenerationError
    ) -> JSONResponse:
        logger.warning(f"Answer synthesis error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(ReasoningError)
    async def reasoning_error_handler(request: Request, exc: ReasoningError) -> JSONResponse:
        logger.warning(f"Reasoning rule error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning(f"Domain rule violation: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(
        request: Request, exc: ConfigurationError
    ) -> JSONResponse:
        logger.error(f"Configuration failure: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(LLMTimeoutError)
    async def llm_timeout_error_handler(request: Request, exc: LLMTimeoutError) -> JSONResponse:
        logger.error(f"LLM request timed out: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(
        request: Request, exc: ExternalServiceError
    ) -> JSONResponse:
        logger.error(f"External service dependency failure: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(InfrastructureError)
    async def infrastructure_error_handler(
        request: Request, exc: InfrastructureError
    ) -> JSONResponse:
        logger.error(f"Infrastructure failure: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(FinancialRAGError)
    async def generic_platform_error_handler(
        request: Request, exc: FinancialRAGError
    ) -> JSONResponse:
        logger.error(f"Application error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(f"HTTP exception {exc.status_code}: {exc.detail}")
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
                    "details": exc.detail if isinstance(exc.detail, dict) else {},
                    "request_id": request_id_ctx_var.get(),
                }
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled internal server error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": {},
                    "request_id": request_id_ctx_var.get(),
                }
            },
        )
